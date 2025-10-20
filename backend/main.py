from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import users
from routers import users, login, tasks, scheduler  # ✅ 确保 login 在这里


app = FastAPI(title="AI Scheduling System")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(login.router)       # ✅ 这行必须存在
app.include_router(tasks.router)
app.include_router(scheduler.router)

@app.get("/")
async def root():
    return {"message": "Welcome to AI Scheduling System!"}



