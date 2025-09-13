# chat_router.py
from __future__ import annotations

import os
from typing import List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(tags=["chat"])

print('chat router loaded (direct HTTP mode)')

# ---- Models (Pydantic v2) ----
class ChatMessage(BaseModel):
    role: str = Field(pattern=r"^(user|assistant|system)$")
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: int = 256

class ChatResponse(BaseModel):
    reply: str
    usage_tokens: Optional[int] = None
    model: Optional[str] = None

# ---- Config ----
OPENAI_API_KEY = os.getenv("OPEN_AI_API_KEY")
AI_MODEL = "gpt-4o-mini"

SYSTEM_PRIMER = (
    "You are the helpful PlyCraft assistant. Provide concise, accurate answers "
    "about products, materials, sizing, care, and brand information. If unsure, "
    "say you don't have that data. Never invent product specs."
)

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest, request: Request) -> ChatResponse:
    print('chat endpoint invoked')
    if not payload.messages:
        
        raise HTTPException(status_code=400, detail="messages cannot be empty")

    # Ensure there is a system message
    messages_for_provider = [{"role": m.role, "content": m.content} for m in payload.messages]
    if not any(m.role == "system" for m in payload.messages):
        messages_for_provider.insert(0, {"role": "system", "content": SYSTEM_PRIMER})

    last_user = payload.messages[-1].content[:400]

    # No key? Return a mock so the UI still works.
    if not OPENAI_API_KEY:
        mock = f"(Mock) You said: {last_user}"
        return ChatResponse(reply=mock, usage_tokens=len(mock.split()), model="mock")

    # Prepare payload for OpenAI Chat Completions API
    body = {
        "model": AI_MODEL,
        "messages": messages_for_provider,
        "max_tokens": payload.max_tokens,
        "temperature": 0.7,
    }

    try:
        async with httpx.AsyncClient(timeout=40) as client:
            r = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
        if r.status_code >= 400:
            print('OpenAI error status', r.status_code, r.text[:200])
            fb = f"(Fallback) You said: {last_user}"
            return ChatResponse(reply=fb, usage_tokens=len(fb.split()), model="fallback-mock")
        data = r.json()
        choice0 = (data.get("choices") or [{}])[0]
        message = (choice0.get("message") or {}).get("content") or "I'm sorry, I couldn't generate a response just now."
        usage = data.get("usage", {})
        total_tokens = usage.get("total_tokens")
        return ChatResponse(reply=message.strip(), usage_tokens=total_tokens, model=AI_MODEL)
    except Exception as e:
        print('Exception calling OpenAI', repr(e))
        fb = f"(Fallback) You said: {last_user}"
        return ChatResponse(reply=fb, usage_tokens=len(fb.split()), model="fallback-mock")
