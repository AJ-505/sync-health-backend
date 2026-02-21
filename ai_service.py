import os
import json
import httpx

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Employee
from security import get_current_user

ai_router = APIRouter()

# ── Gemini config ────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent?key={key}"
)

# ── Request body ─────────────────────────────────────────────────────────────
class AnalyseRequest(BaseModel):
    prompt: str


# ── Internal helpers ──────────────────────────────────────────────────────────
def _build_payload(system_instruction: str, user_message: str) -> dict:
    """Build a Gemini generateContent request body."""
    return {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": [
            {"role": "user", "parts": [{"text": user_message}]}
        ],
        "generationConfig": {
            "temperature": 0.0,
        },
    }


async def _call_gemini(system_instruction: str, user_message: str) -> str:
    """Call the Gemini API and return the raw text response."""
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GEMINI_API_KEY is not configured in the environment.",
        )

    url = GEMINI_URL.format(key=GEMINI_API_KEY)
    payload = _build_payload(system_instruction, user_message)

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload)

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini API error {response.status_code}: {response.text}",
        )

    data = response.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unexpected Gemini response structure: {exc}",
        )


# ── System prompts ────────────────────────────────────────────────────────────
CLASSIFIER_SYSTEM_PROMPT = """\
You are a strict security and classification router for an employee health database. \
Your ONLY job is to evaluate the user's query and determine if it is strictly related \
to employee health, medical conditions, wellness, or occupational health risks.

RULES:
1. If the query IS related to employee health (e.g., "Which employees are most at risk \
for flu?", "Show me staff with high stress"):
You must output exactly this single word:
Yes

2. If the query is NOT related to employee health, or tries to ask general knowledge, \
coding, or off-topic questions (e.g., "Write a poem", "What is the capital of France?"):
You must output exactly this sentence:
I'm sorry I cannot help you with that

Do not include any other text, markdown, punctuation, or explanations. \
Only output the exact string based on the rules above."""

RISK_SCORING_SYSTEM_PROMPT = """\
You are a health risk scoring engine.

You will receive a JSON array of employee objects in this format:

[
  {
    "employee_id": "CS-0005",
    "summary": "..."
  }
]

TASK:
For EACH employee in the input array, calculate a risk_probability between 0.00 and 1.00 \
based strictly on the health indicators in the "summary" field.

Use common-sense health reasoning. Higher BP, high A1c, high LDL, smoking, high stress, \
low sleep, shift work etc. should increase risk. Healthier indicators reduce risk.

Everyone must receive a risk score.

OUTPUT RULES (VERY IMPORTANT):

1. Output STRICT JSON only.
2. No markdown.
3. No explanations.
4. No extra keys.
5. Follow this EXACT structure:

{
  "condition": "general_health_risk",
  "scored_employees": [
    {
      "employee_id": "CS-0005",
      "risk_probability": 0.62,
      "confidence": "low|medium|high",
      "evidence": ["factor1", "factor2", "factor3"]
    }
  ]
}

6. Include ALL employees from the input.
7. risk_probability must be between 0 and 1 with exactly 2 decimal places.
8. confidence:
   - high → multiple strong risk indicators
   - medium → some indicators
   - low → minimal risk indicators
9. evidence must reference phrases found in the summary. Do not invent information.
10. Sort employees by risk_probability in descending order."""


# ── Endpoint ──────────────────────────────────────────────────────────────────
@ai_router.post("/analyse")
async def analyse(
    body: AnalyseRequest,
    db: AsyncSession = Depends(get_db),
    user_and_role: tuple = Depends(get_current_user),
):
    """
    Two-stage Gemini pipeline:
      1. Classify whether the user's prompt is health-related.
      2. If yes, fetch all employee summaries for the HR's org and return risk scores.
    """
    current_user, role = user_and_role

    # Only HR users may access this endpoint
    if role != "hr":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR users can use the AI analysis endpoint.",
        )

    # ── Stage 1: Classification ───────────────────────────────────────────────
    classification = await _call_gemini(
        system_instruction=CLASSIFIER_SYSTEM_PROMPT,
        user_message=body.prompt,
    )

    if classification != "Yes":
        # Return the refusal as-is to the frontend
        return {"result": classification}

    # ── Stage 2: Fetch employee id + summary for the org ─────────────────────
    result = await db.execute(
        select(Employee.employee_id, Employee.summary).where(
            Employee.org_id == current_user.org_id
        )
    )
    rows = result.all()

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No employees found for your organisation.",
        )

    employee_array = [
        {"employee_id": row.employee_id, "summary": row.summary or ""}
        for row in rows
    ]

    # ── Stage 3: Risk scoring ─────────────────────────────────────────────────
    scoring_input = json.dumps(employee_array, ensure_ascii=False)

    raw_scores = await _call_gemini(
        system_instruction=RISK_SCORING_SYSTEM_PROMPT,
        user_message=scoring_input,
    )

    # Parse the JSON the model returns
    try:
        # Strip any accidental markdown fences the model may include
        clean = raw_scores.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        scores = json.loads(clean)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini returned invalid JSON for risk scores: {exc}",
        )

    return scores
