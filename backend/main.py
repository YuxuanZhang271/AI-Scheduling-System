from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 导入路由模块
from routers import users, login, tasks,chatbot

app = FastAPI(title="AI Scheduling System", version="1.0")

# 注册 CORS（允许前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册各路由
app.include_router(users.router)  
app.include_router(login.router)  
app.include_router(tasks.router)
app.include_router(chatbot.router)

@app.get("/")
async def root():
    return {"message": "AI Scheduling System is running!"}
