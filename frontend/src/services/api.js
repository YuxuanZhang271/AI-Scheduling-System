import axios from "axios";

// ✅ 后端 FastAPI 服务器地址
const API_BASE = "http://127.0.0.1:8000";

// --- 建立一個 Axios 實例 (instance) ---
// 它可以自動處理 Token
const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

// --- 設定請求攔截器 (Interceptor) ---
// 會在「每一次」apiClient 發送請求前自動執行
apiClient.interceptors.request.use(
  (config) => {
    // 統一使用 "access_token"
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// -------------------- ✅ 新增：獲取使用者資訊 --------------------
/**
 * (私有) 獲取當前登入使用者的資訊 (包括 user_id)
 * 這會自動使用 apiClient 攔截器中的 token
 */
const getMe = () => {
  return apiClient.get("/users/me");
};

// -------------------- 登录 --------------------
/**
 * ✅ 關鍵修正：
 * 登入流程現在分為兩步：
 * 1. 獲取 token
 * 2. 獲取 user_id 並儲存
 */
export const loginUser = async ({ username, password }) => {
  // 步驟 1: 呼叫 /login/ 獲取 token
  const res = await axios.post(`${API_BASE}/login/`, {
    username,
    password,
  });

  if (res.data.access_token) {
    // 儲存 token
    localStorage.setItem("access_token", res.data.access_token);
    
    // 步驟 2: 立刻呼叫 /users/me 獲取使用者資訊
    try {
      const userRes = await getMe(); // getMe() 會自動使用剛存好的 token
      if (userRes.data.id) {
        // 儲存 user_id
        localStorage.setItem("user_id", userRes.data.id);
      }
    } catch (err) {
      console.error("無法在登入後獲取使用者資訊", err);
      // 登入失敗，清除 token
      localStorage.removeItem("access_token");
    }
  }
  
  return res.data;
};

// -------------------- 任务接口 --------------------
// 全部改用 apiClient 自動發送 token
export const getTasks = (userId) =>
  apiClient.get(`/tasks/${userId}`);

export const createTask = (userId, data) =>
  apiClient.post(`/tasks/${userId}`, data);

export const deleteTask = (taskId, type) =>
  apiClient.delete(`/tasks/${taskId}?task_type=${type}`);

export const updateTask = (taskId, type, data) =>
  apiClient.put(`/tasks/${taskId}?task_type=${type}`, data);

export const updateTaskStatus = (taskId, status) =>
  apiClient.post(`/tasks/assign/${taskId}?status=${status}`);

// -------------------- 智能调度 --------------------
export const runScheduler = (userId) =>
  apiClient.post(`/scheduler/run/${userId}`);

// -------------------- 報表接口 --------------------
// 這些函式現在會由 apiClient 自動帶上 token
export const getDailyStats = (date) => {
  return apiClient.get("/stats/daily", {
    params: { date },
  });
};

export const getWeeklyStats = (startDate, endDate) => {
  return apiClient.get("/stats/weekly", {
    params: {
      start_date: startDate,
      end_date: endDate,
    },
  });
};
