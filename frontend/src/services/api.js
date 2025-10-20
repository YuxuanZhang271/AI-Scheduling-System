<<<<<<< HEAD
import axios from "axios";

// ✅ 后端 FastAPI 服务器地址
const API_BASE = "http://127.0.0.1:8000";

// -------------------- 登录 --------------------
export const loginUser = async ({ username, password }) => {
  const res = await axios.post(`${API_BASE}/login/`, {
    username,
    password,
  });
  return res.data;
};

// -------------------- 任务接口 --------------------
export const getTasks = (userId) =>
  axios.get(`${API_BASE}/tasks/${userId}`);

export const createTask = (userId, data) =>
  axios.post(`${API_BASE}/tasks/${userId}`, data);

export const deleteTask = (taskId, type) =>
  axios.delete(`${API_BASE}/tasks/${taskId}?task_type=${type}`);

export const updateTaskStatus = (taskId, status) =>
  axios.post(`${API_BASE}/tasks/assign/${taskId}?status=${status}`);

// -------------------- 智能调度 --------------------
// ✅ 修复：改为 /scheduler/run/ 来匹配后端路由
export const runScheduler = (userId) =>
  axios.post(`${API_BASE}/scheduler/run/${userId}`);
=======
// src/services/api.js
import axios from "axios";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// 登入：POST /login/
export async function loginUser({ username, password }) {
  const res = await axios.post(`${API_URL}/login/`, {
    username,
    password,
  });
  return res.data; // 後端會回 { access_token, token_type, user_id }
}

export const getTasks = (userId) =>
  axios.get(`${API_URL}/tasks/${userId}`);

export const createTask = (userId, taskData) =>
  axios.post(`${API_URL}/tasks/${userId}`, taskData);

export const deleteTask = (taskId, taskType) =>
  axios.delete(`${API_URL}/tasks/${taskId}?task_type=${taskType}`);
>>>>>>> 30116164397e8c1561c270e9510c582eea7af293
