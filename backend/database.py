# database.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

MONGO_USERNAME = os.getenv("MONGO_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_CLUSTER = os.getenv("MONGO_CLUSTER")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

MONGO_URI = f"mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_CLUSTER}/?retryWrites=true&w=majority"

client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB_NAME]

FIXED_TASK_COLLECTION = "fixed_tasks"
FLEXIBLE_TASK_COLLECTION = "flexible_tasks"
