# routers/chatbot.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from openai import OpenAI

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

# API
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
            model="gpt-4o",  
            messages=[
                {"role": "system", "content": 
                 """
                 You are an AI scheduling assistant that helps users manage tasks and calendars. You are designed to answer only calendar-related questions.When a user asks a scheduling-related question, you should identify the task, task type, and time from the sentence.If the question is not calendar-related, respond with: Please ask calendar-related question."
                 Examples:
                 Question: How is the weather today? Answer: Sorry, please ask calendar-related question.
                 Question: Can you help me add the group meeting starting from 10/21 15:00 to 17:00? Answer: Okay, I can help you with this.
                 You should always respond in a JSON format like this:
                 [
                     {
                         "task": "task name",
                         "task_type": "work",
                         "task_starttime": "2025-10-02 20:00",
                         "task_deadline": "2025-10-03 20:00",
                         "task_priority": 2,
                         "task_description": "Write report",
                         "task_location": "Library"
                    }
                 ]
                 """    },
                {"role": "user", "content": msg.message},
            ],
            temperature=0.3,
            max_tokens=500,
        )

        reply = completion.choices[0].message.content
        return {"reply": reply}

    except Exception as e:
        print("❌ Chatbot error:", e)
        raise HTTPException(status_code=500, detail="Chatbot service error")
