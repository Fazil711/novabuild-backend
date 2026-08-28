import datetime
import json
import re
import uuid
from typing import Dict, Any, List, Optional
from pydantic import ValidationError

from app.schemas import (
    AppPlan, DiscoveryQuestion, DiscoveryAnswer, ConfidenceScore, DiscoverySession
)
from app.services.openrouter_client import call_openrouter
from app.services.plan_engine import _normalize_plan

# In-memory session store (keyed by session_id)
_sessions: Dict[str, DiscoverySession] = {}

QUESTION_GENERATION_PROMPT = """You are the NovaBuild Discovery Interviewer.
Given a user's initial software idea, generate 4 to 6 intelligent, highly specific discovery questions to uncover critical business requirements.

Categories to cover:
1. Business & Industry context
2. Target users & roles
3. Core user workflow (step-by-step)
4. Primary data entities & attributes to track
5. Must-have features & monetization/auth

Rules:
- Return ONLY a JSON object with a single key "questions" containing a list of questions.
- No markdown formatting fences, no explanations.

Schema:
{
  "questions": [
    {
      "id": "q1",
      "question": "string",
      "category": "business" | "users" | "workflow" | "data" | "features" | "design",
      "type": "text" | "single_choice" | "multi_choice",
      "options": ["string"]?,
      "context_hint": "string (brief hint why this matters)"
    }
  ]
}"""

CONFIDENCE_EVALUATION_PROMPT = """You are the NovaBuild Confidence Evaluator.
Evaluate the user's answers to the discovery questions and rate your comprehension confidence from 0 to 100%.

Produce:
1. A concise, clear understanding summary ("Here's what I understood: Business: ..., Target Users: ..., Main Data: ..., Workflow: ...")
2. Confidence score (0-100)
3. Breakdown scores across (business, users, workflow, data, features)
4. Status ("ready_to_build" if score >= 85, else "needs_clarification")

Return ONLY JSON:
{
  "score": number (0-100),
  "summary": "string",
  "breakdown": {
    "business": number,
    "users": number,
    "workflow": number,
    "data": number,
    "features": number
  },
  "status": "ready_to_build" | "needs_clarification"
}"""

DISCOVERY_SYNTHESIS_PROMPT = """You are the NovaBuild Blueprint Architect.
Synthesize the complete, production-ready full-stack application blueprint based on the original idea and the user's detailed discovery answers.

Output ONLY valid JSON matching the AppPlan schema.
{
  "app_name": "string",
  "type": "saas" | "dashboard" | "internal" | "ecommerce" | "portal",
  "description": "string",
  "project_dna": {
    "business_name": "string",
    "industry": "string",
    "target_users": ["string"],
    "main_workflow": "string",
    "goals": ["string"]
  },
  "entities": [
    {
      "name": "string (singular)",
      "plural": "string",
      "fields": [
        { "name": "string", "type": "text"|"number"|"boolean"|"date"|"textarea"|"select", "required": boolean, "options": ["string"]? }
      ]
    }
  ],
  "features": ["string"],
  "pages": [
    {
      "name": "string",
      "path": "string",
      "title": "string",
      "page_type": "dashboard"|"crud_table"|"detail_view"|"form"|"settings",
      "entity_ref": "string?",
      "description": "string"
    }
  ],
  "navigation": [
    { "label": "string", "path": "string", "icon": "string", "order": 1 }
  ],
  "auth_config": {
    "enabled": true,
    "roles": ["string"],
    "public_signups": true,
    "default_role": "string"
  }
}"""


async def start_discovery(prompt: str) -> DiscoverySession:
    session_id = str(uuid.uuid4())
    
    try:
        raw = await call_openrouter([
            {"role": "system", "content": QUESTION_GENERATION_PROMPT},
            {"role": "user", "content": f"Software Idea:\n{prompt}"},
        ])
        cleaned = re.sub(r"```json|```", "", raw).strip()
        parsed = json.loads(cleaned)
        raw_questions = parsed.get("questions", [])
        questions = [DiscoveryQuestion(**q) for q in raw_questions]
    except Exception:
        # Resilient fallback questions
        questions = [
            DiscoveryQuestion(
                id="q1",
                question="What is the official name and industry for this business or application?",
                category="business",
                type="text",
                context_hint="Used for branding and project DNA"
            ),
            DiscoveryQuestion(
                id="q2",
                question="Who are the primary target users and what roles will they have?",
                category="users",
                type="single_choice",
                options=["Admins and Customers", "Internal Team Only", "Buyers, Sellers & Brokers", "Members & Managers"],
                context_hint="Defines role-based permissions"
            ),
            DiscoveryQuestion(
                id="q3",
                question="Describe the step-by-step workflow (from creating an item to completion):",
                category="workflow",
                type="text",
                context_hint="e.g., Create Lead -> Follow Up -> Send Quote -> Close Deal"
            ),
            DiscoveryQuestion(
                id="q4",
                question="What key data entities must be tracked?",
                category="data",
                type="text",
                context_hint="e.g. Products, Orders, Invoices, Customers"
            ),
            DiscoveryQuestion(
                id="q5",
                question="What visual style and theme do you prefer?",
                category="design",
                type="single_choice",
                options=["Modern Dark", "Clean Corporate Light", "Luxury High-End", "Minimalist Slate"],
                context_hint="Defines UI styling"
            )
        ]

    session = DiscoverySession(
        session_id=session_id,
        prompt=prompt,
        questions=questions,
        answers={},
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    _sessions[session_id] = session
    return session


def _normalize_confidence(data: dict, answered_count: int, total_count: int) -> ConfidenceScore:
    raw_score = data.get("score") or data.get("confidence_score") or data.get("confidence")
    if raw_score is not None:
        try:
            score = int(str(raw_score).replace("%", "").strip())
        except Exception:
            score = 88
    else:
        ratio = answered_count / max(total_count, 1)
        score = min(int(ratio * 30) + 70, 96) if answered_count > 0 else 50

    summary = data.get("summary") or data.get("understanding") or f"Here's what I understood: The project has {answered_count} defined requirements covering core workflows, entities, and users."
    breakdown = data.get("breakdown")
    if not isinstance(breakdown, dict):
        breakdown = {"business": score, "users": score, "workflow": min(score, 92), "data": score, "features": score}

    status = "ready_to_build" if score >= 80 else "needs_clarification"
    return ConfidenceScore(score=score, summary=summary, breakdown=breakdown, status=status)


async def submit_answers(session_id: str, answers: List[DiscoveryAnswer]) -> DiscoverySession:
    session = _sessions.get(session_id)
    if not session:
        raise ValueError(f"Discovery session '{session_id}' not found")

    for ans in answers:
        session.answers[ans.question_id] = ans.answer

    # Evaluate confidence
    qa_context = "\n".join(
        f"Q: {q.question}\nA: {session.answers.get(q.id, 'Not provided')}"
        for q in session.questions
    )

    answered_count = len([q for q in session.questions if q.id in session.answers])
    total_count = max(len(session.questions), 1)

    try:
        raw = await call_openrouter([
            {"role": "system", "content": CONFIDENCE_EVALUATION_PROMPT},
            {"role": "user", "content": f"Initial Prompt: {session.prompt}\n\nQ&A Discovery:\n{qa_context}"},
        ])
        cleaned = re.sub(r"```json|```", "", raw).strip()
        parsed = json.loads(cleaned)
        session.confidence = _normalize_confidence(parsed, answered_count, total_count)
    except Exception:
        session.confidence = _normalize_confidence({}, answered_count, total_count)

    _sessions[session_id] = session
    return session


async def synthesize_discovered_blueprint(session_id: str) -> AppPlan:
    session = _sessions.get(session_id)
    if not session:
        raise ValueError(f"Discovery session '{session_id}' not found")

    qa_context = "\n".join(
        f"Q: {q.question}\nA: {session.answers.get(q.id, 'Not specified')}"
        for q in session.questions
    )

    full_context = (
        f"INITIAL IDEA:\n{session.prompt}\n\n"
        f"DISCOVERY INTERVIEW ANSWERS:\n{qa_context}\n\n"
        f"CONFIDENCE SUMMARY:\n{session.confidence.summary if session.confidence else 'Ready to build'}"
    )

    try:
        raw = await call_openrouter([
            {"role": "system", "content": DISCOVERY_SYNTHESIS_PROMPT},
            {"role": "user", "content": full_context},
        ])

        cleaned = re.sub(r"```json|```", "", raw).strip()
        parsed = json.loads(cleaned)
        normalized = _normalize_plan(parsed)
        plan = AppPlan(**normalized)
    except Exception:
        # Resilient synthesis fallback
        from app.schemas import EntitySchema, FieldSchema, PageBlueprint, NavItem, ProjectDNA, AuthConfig
        plan = AppPlan(
            app_name="DiscoveredApp",
            type="saas",
            description=session.prompt,
            project_dna=ProjectDNA(
                business_name="Discovered Enterprise",
                industry="Software & Services",
                target_users=["Administrators", "Members", "Clients"],
                main_workflow="Onboard -> Process -> Complete",
                goals=["Streamline core business workflow"]
            ),
            entities=[
                EntitySchema(
                    name="Item",
                    plural="Items",
                    fields=[
                        FieldSchema(name="title", type="text", required=True),
                        FieldSchema(name="status", type="select", options=["Pending", "Active", "Completed"]),
                        FieldSchema(name="notes", type="textarea")
                    ]
                )
            ],
            features=["Comprehensive data management", "Role-based authentication"],
            pages=[
                PageBlueprint(name="Dashboard", path="/", title="Overview", page_type="dashboard"),
                PageBlueprint(name="Items", path="/items", title="Item Management", page_type="crud_table", entity_ref="Item")
            ],
            navigation=[
                NavItem(label="Dashboard", path="/", icon="LayoutDashboard", order=1),
                NavItem(label="Items", path="/items", icon="Layers", order=2)
            ],
            auth_config=AuthConfig(enabled=True, roles=["admin", "member"], default_role="member")
        )

    session.blueprint = plan
    _sessions[session_id] = session
    return plan


def get_session(session_id: str) -> Optional[DiscoverySession]:
    return _sessions.get(session_id)
