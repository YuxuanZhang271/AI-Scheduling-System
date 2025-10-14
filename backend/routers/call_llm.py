# routers/call_llm.py

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate

# load .env (so OPENAI_API_KEY is loaded)
load_dotenv()

# 初始化 LLM
_llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.2,
    max_tokens=None,
)

# Build prompt template with system + human messages
# System prompt constrains to only talk about tasks
_chat_prompt_template = ChatPromptTemplate.from_messages([
    ("system",
     "You are an AI assistant specialized in managing tasks and schedules. "
     "You should ONLY answer questions related to tasks, deadlines, planning, scheduling. "
     "If asked something unrelated, reply: 'I’m sorry, I can only answer questions about tasks and scheduling.'"
    ),
    ("human", "{user_input}")
])

async def call_llm(user_message: str, history=None) -> str:
    """
    Call LLM with the constrained prompt.
    user_message: the user's input string
    history: not used currently
    """
    # format the prompt
    messages = _chat_prompt_template.format_messages(user_input=user_message)
    # messages is list[BaseMessage], first system, then human
    
    # invoke the LLM
    resp = await _llm.ainvoke(messages)
    return resp.content
