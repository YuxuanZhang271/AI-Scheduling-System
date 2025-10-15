# routers/chatbot.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from openai import OpenAI

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

# 从环境变量中读取 API 密钥
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatMessage(BaseModel):
    message: str

@router.post("/reply")
async def get_reply(msg: ChatMessage):
    """
    接收前端的用户消息，调用 OpenAI API 并返回回复
    """
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # ✅ 轻量版 GPT-4 适合聊天
            messages=[
                {"role": "system", "content": "You are an AI scheduling assistant that helps users manage tasks and calendars."},
                {"role": "user", "content": msg.message},
            ],
            temperature=0.7,
            max_tokens=500,
        )

        reply = completion.choices[0].message.content
        return {"reply": reply}

    except Exception as e:
        print("❌ Chatbot error:", e)
        raise HTTPException(status_code=500, detail="Chatbot service error")
