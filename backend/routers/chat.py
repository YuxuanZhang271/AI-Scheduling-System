# routers/chat.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Literal, Optional
from .call_llm import call_llm  # ← 如果你的 call_llm 放別的資料夾，請調整匯入路徑

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatTurn(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatTurn]] = None  # 可選：多輪上下文

class ChatResponse(BaseModel):
    reply: str

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    try:
        reply = await call_llm(user_message=req.message, history=req.history or [])
        return ChatResponse(reply=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {e}")
