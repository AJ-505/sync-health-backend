

import json
import os
import bcrypt
import psycopg2
from psycopg2.extras import Json

from database import Base
from dotenv import load_dotenv

load_dotenv()# ── DB connection ─────────────────────────────────────────────────────────────
# Priority: DATABASE_URL env var → individual fields below
DATABASE_URL = os.getenv("DATABASE_URL")  # e.g. "postgresql://user:pass@host:5432/dbname"

DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "dbname":   os.getenv("DB_NAME",     "healthdb"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

# ── Hashing config ────────────────────────────────────────────────────────────
BCRYPT_ROUNDS = 12          # cost factor stored in hr_users.hash_rounds
HASH_ALGORITHM = "bcrypt"   # stored in hr_users.hash_algorithm

# ── Data file ─────────────────────────────────────────────────────────────────
DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")


# ─────────────────────────────────────────────────────────────────────────────
def get_connection(retries: int = 5, base_delay: float = 3.0):
    """
    Connect to Postgres with retry logic.

    Neon free-tier computes go to sleep when idle. The first connection
    attempt during a cold-start will time out or be dropped. Retrying a few
    times with a short delay lets the compute finish waking up.
    """
    import time

    db_url = DATABASE_URL
    if db_url:
        # psycopg2 needs a plain postgresql:// scheme (not asyncpg)
        if db_url.startswith("postgresql+asyncpg://"):
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

        # Neon's pooler endpoint only accepts HTTP connections (serverless drivers).
        # psycopg2 uses raw TCP, so we must use the direct (non-pooler) endpoint.
        # Strip '-pooler' from the hostname if present.
        db_url = db_url.replace("-pooler.", ".")

        # Neon and most cloud providers require SSL
        if "sslmode=" not in db_url:
            separator = "&" if "?" in db_url else "?"
            db_url = f"{db_url}{separator}sslmode=require"

        # Add a per-attempt timeout so we fail fast and retry promptly
        if "connect_timeout=" not in db_url:
            separator = "&" if "?" in db_url else "?"
            db_url = f"{db_url}{separator}connect_timeout=10"

    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            if db_url:
                conn = psycopg2.connect(db_url)
            else:
                conn = psycopg2.connect(**DB_CONFIG)
            if attempt > 1:
                print(f"  Connected on attempt {attempt}.")
            return conn
        except psycopg2.OperationalError as exc:
            last_exc = exc
            if attempt < retries:
                delay = base_delay * attempt
                print(f"  Connection attempt {attempt} failed — retrying in {delay:.0f}s …")
                time.sleep(delay)
            else:
                print(f"  All {retries} connection attempts failed.")

    raise last_exc



def hash_password(plain: str) -> str:
    """Return a bcrypt hash string for *plain*."""
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def create_tables(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id   SERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS hr_users (
            id              SERIAL PRIMARY KEY,
            org_id          INT  NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            name            TEXT NOT NULL,
            email           TEXT NOT NULL UNIQUE,
            password_hash   TEXT NOT NULL,
            hash_algorithm  TEXT NOT NULL,   -- e.g. "bcrypt"
            hash_rounds     INT  NOT NULL,   -- cost factor  (e.g. 12)
            role            TEXT NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            org_id        INT  NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            employee_id   TEXT PRIMARY KEY,
            name          TEXT,
            gender        TEXT,
            dob           DATE,
            department    TEXT,
            job_level     TEXT,
            location_city TEXT,
            marital_status TEXT,
            health        JSONB,
            summary       TEXT
        );
    """)

    # Add summary column if it doesn't exist (for pre-existing databases)
    cur.execute("""
        ALTER TABLE employees ADD COLUMN IF NOT EXISTS summary TEXT;
    """)


def upsert_organization(cur, name: str) -> int:
    """Insert org if not exists, return its id."""
    cur.execute("""
        INSERT INTO organizations (name)
        VALUES (%s)
        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
        RETURNING id;
    """, (name,))
    return cur.fetchone()[0]


def upsert_hr(cur, org_id: int, hr: dict):
    plain_pw = hr["password"]
    pw_hash  = hash_password(plain_pw)

    cur.execute("""
        INSERT INTO hr_users (org_id, name, email, password_hash, hash_algorithm, hash_rounds, role)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (email) DO UPDATE SET
            org_id         = EXCLUDED.org_id,
            name           = EXCLUDED.name,
            password_hash  = EXCLUDED.password_hash,
            hash_algorithm = EXCLUDED.hash_algorithm,
            hash_rounds    = EXCLUDED.hash_rounds,
            role           = EXCLUDED.role;
    """, (org_id, hr["name"], hr["email"], pw_hash, HASH_ALGORITHM, BCRYPT_ROUNDS, hr["role"]))


def upsert_employee(cur, org_id: int, emp: dict):
    cur.execute("""
        INSERT INTO employees
            (org_id, employee_id, name, gender, dob, department, job_level,
             location_city, marital_status, health, summary)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (employee_id) DO UPDATE SET
            org_id         = EXCLUDED.org_id,
            name           = EXCLUDED.name,
            gender         = EXCLUDED.gender,
            dob            = EXCLUDED.dob,
            department     = EXCLUDED.department,
            job_level      = EXCLUDED.job_level,
            location_city  = EXCLUDED.location_city,
            marital_status = EXCLUDED.marital_status,
            health         = EXCLUDED.health,
            summary        = EXCLUDED.summary;
    """, (
        org_id,
        emp["employee_id"],
        emp["name"],
        emp["gender"],
        emp["dob"],
        emp["department"],
        emp["job_level"],
        emp["location_city"],
        emp["marital_status"],
        Json(emp["health"]),
        emp.get("summary"),
    ))


def load_data(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    print(f"Loading {DATA_FILE} …")
    data = load_data(DATA_FILE)

    conn = get_connection()
    conn.autocommit = False

    try:
        with conn.cursor() as cur:
            print("Creating tables if they don't exist …")
            create_tables(cur)

            for org_data in data["organizations"]:
                org_name = org_data["name"]
                print(f"\n→ Organization: {org_name}")

                org_id = upsert_organization(cur, org_name)
                print(f"  org_id = {org_id}")

                # HR users
                for hr in org_data.get("hrs", []):
                    upsert_hr(cur, org_id, hr)
                    print(f"  HR upserted: {hr['email']}")

                # Employees
                employees = org_data.get("employees", [])
                for emp in employees:
                    upsert_employee(cur, org_id, emp)
                print(f"  {len(employees)} employees upserted.")

        conn.commit()
        print("\n✓ All data committed successfully.")

    except Exception as exc:
        conn.rollback()
        print(f"\n✗ Error — rolled back. Details:\n  {exc}")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()
