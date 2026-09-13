import json
import datetime
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from app.schemas import ChatRequest, ChatResponse, ChatMessage
from app.services.openrouter_client import call_openrouter

router = APIRouter(prefix="/chat", tags=["chat"])

DEFAULT_CHAT_SYSTEM_PROMPT = """You are NovaBuild Copilot — a witty, world-class fullstack software architect, senior engineer, and friendly product designer.

Your goal is to converse casually, guide the user through software development ideas, answer technical questions, explain architecture, suggest database schemas, or brainstorm product concepts.

Guidelines:
- Keep a helpful, clear, and modern developer tone.
- When the user asks about an app idea, outline key features, entities, or tech stack recommendations concisely.
- Format code cleanly using markdown syntax highlighting.
- Be concise when asked simple questions, but provide thorough architecture breakdowns when requested.
- If the user discusses a product or application they want to build, naturally summarize key specifications and mention they can click "Synthesize into Blueprint" to generate the full Next.js application codebase.
"""


def _get_fallback_reply(last_user_message: str) -> str:
    msg_lower = last_user_message.lower()
    if any(k in msg_lower for k in ["hi", "hello", "hey", "who are you"]):
        return (
            "Hey there! 👋 I'm NovaBuild Copilot. I'm here to chat casually about your app ideas, "
            "recommend system architectures, design database schemas, or troubleshoot your Next.js and SQL code. "
            "What kind of project or tech question is on your mind today?"
        )
    elif any(k in msg_lower for k in ["idea", "build", "app", "project", "saas"]):
        return (
            f"That sounds like a compelling concept! When architecting this kind of app, here are key considerations:\n\n"
            f"1. **Core Data Entities**: Start with your primary domain models and establish clean foreign key relationships.\n"
            f"2. **User Flows & RBAC**: Determine the main workflows (e.g. Admin, Member, Client) and permissions.\n"
            f"3. **Next.js 14 App Router**: Utilize Server Components for data fetching and Server Actions for mutations.\n\n"
            f"Whenever you're ready, click **'Synthesize into Blueprint'** below to turn this into an executable Next.js architecture!"
        )
    else:
        return (
            f"Got it! That's a great point regarding '{last_user_message}'. "
            f"From a software engineering perspective, keeping your components modular, state predictable, "
            f"and database schemas strictly typed will give you the best developer velocity. "
            f"Would you like to explore entity models, API routes, or UI components for this?"
        )


@router.post("", response_model=ChatResponse)
async def send_chat_message(req: ChatRequest):
    if not req.messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one message is required."
        )

    system_prompt = req.system_prompt or DEFAULT_CHAT_SYSTEM_PROMPT
    if req.project_context:
        system_prompt += f"\n\nCurrent Project Context:\n{req.project_context}"

    llm_messages = [{"role": "system", "content": system_prompt}]
    for m in req.messages:
        llm_messages.append({"role": m.role, "content": m.content})

    try:
        reply_content = await call_openrouter(llm_messages)
    except Exception:
        # Graceful fallback if OpenRouter key has rate limits or network issues
        last_msg = req.messages[-1].content if req.messages else "Hello"
        reply_content = _get_fallback_reply(last_msg)

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return ChatResponse(
        message=ChatMessage(
            role="assistant",
            content=reply_content,
            timestamp=timestamp
        ),
        suggested_actions=["Synthesize into Blueprint", "Refine Architecture", "Add DB Entities"]
    )


async def _stream_chat_response(messages: list[dict], fallback_text: str) -> AsyncGenerator[str, None]:
    try:
        reply = await call_openrouter(messages)
        words = reply.split(" ")
        for i in range(0, len(words), 3):
            chunk = " ".join(words[i:i+3]) + " "
            yield f"data: {json.dumps({'chunk': chunk, 'done': False})}\n\n"
        yield f"data: {json.dumps({'chunk': '', 'done': True, 'full_text': reply})}\n\n"
    except Exception:
        words = fallback_text.split(" ")
        for i in range(0, len(words), 3):
            chunk = " ".join(words[i:i+3]) + " "
            yield f"data: {json.dumps({'chunk': chunk, 'done': False})}\n\n"
        yield f"data: {json.dumps({'chunk': '', 'done': True, 'full_text': fallback_text})}\n\n"


@router.post("/stream")
async def send_chat_message_stream(req: ChatRequest):
    if not req.messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one message is required."
        )

    system_prompt = req.system_prompt or DEFAULT_CHAT_SYSTEM_PROMPT
    if req.project_context:
        system_prompt += f"\n\nCurrent Project Context:\n{req.project_context}"

    llm_messages = [{"role": "system", "content": system_prompt}]
    for m in req.messages:
        llm_messages.append({"role": m.role, "content": m.content})

    last_msg = req.messages[-1].content if req.messages else "Hello"
    fallback_text = _get_fallback_reply(last_msg)

    return StreamingResponse(
        _stream_chat_response(llm_messages, fallback_text),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
