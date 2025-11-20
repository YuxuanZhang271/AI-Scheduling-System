from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from bson import ObjectId
import os, re, json, openai
from datetime import datetime, timedelta
from dotenv import load_dotenv
from database import db
from models import FIXED_TASK_COLLECTION, FLEXIBLE_TASK_COLLECTION

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=dotenv_path)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ Missing OPENAI_API_KEY in .env")

client = openai.OpenAI(api_key=api_key)

class ChatMessage(BaseModel):
    message: str


def clean_mongo_doc(document: dict):
    """清理 ObjectId 与 datetime"""
    if not document:
        return document
    result = {}
    for k, v in document.items():
        if isinstance(v, ObjectId):
            result[k] = str(v)
        elif isinstance(v, datetime):
            result[k] = v.strftime("%Y%m%d%H%M")
        else:
            result[k] = v
    return result


@router.post("/reply")
async def get_reply(request: Request, msg: ChatMessage):
    try:
        user_id = request.query_params.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="Missing user_id in query params")

        # 1️⃣ 调用 GPT
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """
                    You are an API formatter. Return ONLY one JSON object with NO markdown, no explanations. If the question is not calendar-related, respond with: Please ask calendar-related question."
                    
                    Fixed Task Example:
                    {
                      "name": "task name",
                      "mode": "fixed",
                      "startTime": "YYYYMMDDHHMM",
                      "duration": 120,
                      "category": "work",
                      "priority": 2,
                      "difficulty": 3,
                      "location": ""
                    }
                    
                    Flexible Task Example:
                    {
                      "name": "task name",
                      "mode": "flexible",
                      "deadline": "YYYYMMDDHHMM",
                      "duration": 60,
                      "category": "work",
                      "priority": 2,
                      "difficulty": 3,
                      "location": ""
                    }
                    """
                },
                {"role": "user", "content": msg.message},
            ],
            temperature=0.2,
            max_tokens=400,
        )

        gpt_output = completion.choices[0].message.content.strip()
        print("🧠 GPT Raw Output:\n", gpt_output)

        # 2️⃣ 提取 JSON 内容，容错 “json”, “```json” 等情况
        json_match = re.search(r"\{[\s\S]*\}", gpt_output)
        if not json_match:
            raise ValueError(f"No valid JSON object found in GPT output:\n{gpt_output}")
        json_str = json_match.group(0).strip()

        try:
            task_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"❌ JSON decode error: {e}\nExtracted:\n{json_str}")

        # 3️⃣ 构建符合 tasks.py 的结构
        mode = task_data.get("mode", "").lower()

        if mode == "fixed":
            start_time = task_data.get("startTime")
            duration = int(task_data.get("duration", 60))
            start_dt = datetime.strptime(start_time, "%Y%m%d%H%M")
            end_dt = start_dt + timedelta(minutes=duration)
            end_time = end_dt.strftime("%Y%m%d%H%M")

            new_task = {
                "user_id": str(user_id),
                "task_name": task_data["name"],
                "task_start_time": start_time,
                "task_duration": duration,
                "task_end_time": end_time,
                "task_type": task_data.get("category", "work"),
                "task_priority": int(task_data.get("priority", 2)),
                "expected_difficulty": int(task_data.get("difficulty", 3)),
                "task_location": task_data.get("location", ""),
                "status": "assigned",
                "created_at": datetime.now(),
            }

            result = await db[FIXED_TASK_COLLECTION].insert_one(new_task)
            print(f"✅ Inserted fixed_task: {result.inserted_id}")
            return {
                "message": "✅ Fixed task created successfully",
                "task_data": clean_mongo_doc(new_task),
            }

        elif mode == "flexible":
            deadline = task_data.get("deadline")
            duration = float(task_data.get("duration", 60))
            new_task = {
                "user_id": str(user_id),
                "task_name": task_data["name"],
                "task_deadline": deadline,
                "expected_duration": duration,
                "expected_difficulty": int(task_data.get("difficulty", 3)),
                "task_priority": int(task_data.get("priority", 2)),
                "task_type": task_data.get("category", "work"),
                "task_location": task_data.get("location", ""),
                "status": "unassigned",
                "start_time": None,
                "end_time": None,
                "created_at": datetime.now(),
            }

            result = await db[FLEXIBLE_TASK_COLLECTION].insert_one(new_task)
            print(f"✅ Inserted flexible_task: {result.inserted_id}")
            return {
                "message": "✅ Flexible task created successfully",
                "task_data": clean_mongo_doc(new_task),
            }

        else:
            raise ValueError(f"Invalid mode: {mode}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
