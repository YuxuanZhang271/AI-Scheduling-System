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

export const updateTask = (taskId, type, data) =>
  axios.put(`${API_BASE}/tasks/${taskId}?task_type=${type}`, data);

export const updateTaskStatus = (taskId, status) =>
  axios.post(`${API_BASE}/tasks/assign/${taskId}?status=${status}`);

// -------------------- 智能调度 --------------------
// ✅ 修复：改为 /scheduler/run/ 来匹配后端路由
export const runScheduler = (userId) =>
  axios.post(`${API_BASE}/scheduler/run/${userId}`);
