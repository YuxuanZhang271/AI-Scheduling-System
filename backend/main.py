from fastapi import FastAPI
from routers import users

app = FastAPI(title="AI Scheduling System")

app.include_router(users.router)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to AI Scheduling System!"}

from routers.chat import router as chat_router
app.include_router(chat_router)
