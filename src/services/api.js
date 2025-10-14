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
