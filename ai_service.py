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
    "gemini-3-flash-preview:generateContent?key={key}"
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


async def _call_ai(system_instruction: str, user_message: str) -> str:
    """Call the Gemini API and return the raw text response."""
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GEMINI_API_KEY is not configured in the environment.",
        )

    url = GEMINI_URL.format(key=GEMINI_API_KEY)
    payload = _build_payload(system_instruction, user_message)

    async with httpx.AsyncClient(timeout=None) as client:
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


# ── System prompts ─────────────────────────────────────────────────────────────
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

# FIX 1: Prompt now enforces a realistic score distribution and forbids inflation.
# FIX 2: The user's query is injected as CONDITION: so the model scores for the
#         exact condition asked, not one it invents on its own.
RISK_SCORING_SYSTEM_PROMPT = """\
You are a precise health risk scoring engine. You score employees for a SPECIFIC \
condition stated at the top of the user message.

The user message will always begin with:
CONDITION: <exact condition to score for>
DATA:
[JSON array of employees]

TASK:
Evaluate each employee's susceptibility to the specified CONDITION only. \
Focus exclusively on health factors in their summary that are relevant to that condition. \
Ignore unrelated indicators entirely.

SCORING DISCIPLINE — THIS IS MANDATORY:
- You must produce a realistic, spread-out distribution of scores.
- Most employees should score between 0.15 and 0.55 for any given condition.
- A score above 0.65 requires the employee to have MULTIPLE strong risk factors \
that are DIRECTLY and SPECIFICALLY linked to the condition being asked about.
- A score above 0.80 requires overwhelming, specific, undeniable evidence from \
their summary — not just generic poor health.
- DO NOT give everyone high risk. DO NOT inflate scores.
- If only 3 out of 50 employees genuinely have meaningful susceptibility, only 3 appear in the output.
- Scores across employees MUST differ meaningfully. \
Giving many employees the same or near-identical scores is a critical error.

OUTPUT RULES:
1. Output STRICT JSON only. No markdown. No explanations. No extra keys.
2. Use this exact structure:

{
  "condition": "<condition from the CONDITION line, verbatim>",
  "scored_employees": [
    {
      "employee_id": "CS-0005",
      "risk_probability": 0.74,
      "confidence": "high",
      "evidence": ["smokes 6 cigarettes per day", "stress level 9/10", "sleep 5.2h avg"]
    }
  ]
}

3. scored_employees MUST ONLY contain employees with risk_probability strictly above 0.65.
4. If no employees exceed 0.65, return scored_employees as an empty array [].
5. risk_probability must be a float between 0.00 and 1.00 with exactly 2 decimal places.
6. confidence levels:
   - "high"   → 3 or more strong, directly relevant risk factors
   - "medium" → 1–2 relevant indicators
   - "low"    → borderline, minimal direct evidence
7. Each evidence item must be a short phrase quoted or closely paraphrased from the summary. \
Do NOT invent or assume any information not stated in the summary.
8. Sort scored_employees by risk_probability descending."""


# ── Endpoint ───────────────────────────────────────────────────────────────────
@ai_router.post("/analyse")
async def analyse(
    body: AnalyseRequest,
    db: AsyncSession = Depends(get_db),
    user_and_role: tuple = Depends(get_current_user),
):
    """
    Two-stage Gemini pipeline:
      1. Classify whether the user's prompt is health-related.
      2. If yes, fetch employee summaries for the HR's org and return risk scores
         for the specific condition the user asked about.
    """
    current_user, role = user_and_role

    # Only HR users may access this endpoint
    if role != "hr":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR users can use the AI analysis endpoint.",
        )

    # ── Stage 1: Classification ───────────────────────────────────────────────
    classification = await _call_ai(
        system_instruction=CLASSIFIER_SYSTEM_PROMPT,
        user_message=body.prompt,
    )

    if classification != "Yes":
        return {"result": classification}

    # ── Stage 2: Fetch employee id + summary for the org ─────────────────────
    result = await db.execute(
        select(Employee.employee_id, Employee.summary).where(
            Employee.org_id == current_user.org_id
        ).limit(15)
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
    # Prefix the user's exact query as CONDITION so the model scores specifically for it
    scoring_input = (
        f"CONDITION: {body.prompt}\n"
        f"DATA:\n"
        f"{json.dumps(employee_array, ensure_ascii=False)}"
    )

    raw_scores = await _call_ai(
        system_instruction=RISK_SCORING_SYSTEM_PROMPT,
        user_message=scoring_input,
    )

    # Parse the JSON the model returns
    try:
        # Strip any accidental markdown fences the model may include
        clean = (
            raw_scores.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        scores = json.loads(clean)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini returned invalid JSON for risk scores: {exc}",
        )

    return scores
