import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginUser } from "../services/api";

export default function Login({ onLogin }) {
  const navigate = useNavigate();

  // form state
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  // banners & errors
  const [errorBanner, setErrorBanner] = useState("");
  const [successBanner, setSuccessBanner] = useState("");
  const [pwdErrVisible, setPwdErrVisible] = useState(false);

  // ui state
  const [loading, setLoading] = useState(false);

  // modals
  const [signupOpen, setSignupOpen] = useState(false);
  const [forgotOpen, setForgotOpen] = useState(false);

  // ✅ 用户名只需非空即可
  const isUsernameValid = useMemo(() => username.trim().length > 0, [username]);
  const isPasswordValid = useMemo(() => password.length > 0, [password]);
  const canSubmit = isUsernameValid && isPasswordValid && !loading;

  // ✅ 刷新时检查本地存储，若已登录则跳转
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      navigate("/schedule");
    }
  }, [navigate]);

  // keyboard: ESC to close modals
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") {
        setSignupOpen(false);
        setForgotOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const resetForm = () => {
    setUsername("");
    setPassword("");
    setRemember(false);
    setShowPassword(false);
    setLoading(false);
    setErrorBanner("");
    setSuccessBanner("");
    setPwdErrVisible(false);
  };

  // ✅ 串接后端登录接口
  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorBanner("");
    setSuccessBanner("");

    if (!isUsernameValid) {
      setErrorBanner("Please enter your username.");
      return;
    }
    if (!isPasswordValid) {
      setPwdErrVisible(true);
      return;
    }

    setLoading(true);
    try {
      const res = await loginUser({
        username: username,
        password: password,
      });

      // ✅ FastAPI 返回格式
      // {
      //   "access_token": "...",
      //   "token_type": "bearer",
      //   "user_id": "68e9212ba448a137ef81a37c"
      // }

      const { access_token, token_type, user_id } = res;

      if (!access_token || !user_id) {
        throw new Error("Missing access_token or user_id in response");
      }

      // ✅ 存储用户信息到 localStorage
      localStorage.setItem("access_token", access_token);
      localStorage.setItem("token_type", token_type || "bearer");
      localStorage.setItem("user_id", user_id);
      localStorage.setItem("username", username);

      console.log("✅ Login success:", { user_id, token_type });

      setSuccessBanner("Sign in successful! Redirecting to dashboard...");
      setTimeout(() => {
        if (typeof onLogin === "function") onLogin();
        navigate("/schedule");
      }, 1000);
    } catch (err) {
      console.error("❌ Login failed:", err);
      const msg =
        err?.response?.data?.detail || "Incorrect username or password.";
      setErrorBanner(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      {/* 左侧品牌面板 */}
      <div className="brand-panel">
        <div className="logo">
          <svg
            width="44"
            height="44"
            viewBox="0 0 56 56"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden
          >
            <rect x="8" y="16" width="40" height="32" rx="8" fill="#003D7C" />
            <circle cx="20" cy="28" r="4" fill="#EF7C00" />
            <circle cx="36" cy="28" r="4" fill="#EF7C00" />
            <circle cx="20" cy="28" r="2" fill="white" />
            <circle cx="36" cy="28" r="2" fill="white" />
            <rect x="22" y="36" width="12" height="4" rx="2" fill="#EF7C00" />
            <line
              x1="28"
              y1="16"
              x2="28"
              y2="8"
              stroke="#003D7C"
              strokeWidth="2"
            />
            <circle cx="28" cy="6" r="3" fill="#EF7C00" />
            <rect x="4" y="24" width="4" height="8" rx="2" fill="#003D7C" />
            <rect x="48" y="24" width="4" height="8" rx="2" fill="#003D7C" />
          </svg>
        </div>

        <h1 className="brand-title">AI-Powered Scheduling</h1>
        <p className="brand-subtitle">
          Smart daily planning that adapts to your energy and priorities.
        </p>

        <svg
          className="illustration"
          viewBox="0 0 200 160"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden
        ></svg>
      </div>

      {/* 右侧登录面板 */}
      <div className="login-panel">
        <div className={`login-card ${loading ? "form-loading" : ""}`}>
          {errorBanner && <div className="error-banner">{errorBanner}</div>}
          {successBanner && (
            <div className="success-banner">{successBanner}</div>
          )}

          <h2 className="login-title">Sign in</h2>

          <form id="loginForm" onSubmit={handleSubmit}>
            <div className="form-group">
              <input
                type="text"
                id="username"
                className="form-input"
                placeholder="Username"
                aria-label="Username"
                value={username}
                onChange={(e) => {
                  setUsername(e.target.value);
                  setErrorBanner("");
                }}
                required
              />
            </div>

            <div className="form-group">
              <div className="password-container">
                <input
                  type={showPassword ? "text" : "password"}
                  id="password"
                  className="form-input"
                  placeholder="Password"
                  aria-label="Password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    setPwdErrVisible(false);
                    setErrorBanner("");
                  }}
                  required
                />
                <button
                  type="button"
                  className="password-toggle"
                  aria-label={
                    showPassword ? "Hide password" : "Show password"
                  }
                  onClick={() => setShowPassword((s) => !s)}
                >
                  {showPassword ? "🙈" : "👁"}
                </button>
              </div>
              {pwdErrVisible && (
                <div className="error-message" id="passwordError">
                  Please enter your password.
                </div>
              )}
            </div>

            <div className="form-options">
              <label className="checkbox-container">
                <input
                  type="checkbox"
                  className="checkbox"
                  checked={remember}
                  onChange={(e) => setRemember(e.target.checked)}
                />
                <span className="checkbox-label">Remember me</span>
              </label>

              <button
                type="button"
                className="forgot-link"
                onClick={() => setForgotOpen(true)}
              >
                Forgot password?
              </button>
            </div>

            <button
              type="submit"
              className="btn-primary"
              id="signInBtn"
              disabled={!canSubmit}
            >
              <div
                className="spinner"
                style={{ display: loading ? "inline-block" : "none" }}
              />
              <span id="btnText">
                {loading ? "Signing in..." : "Sign in"}
              </span>
            </button>
          </form>

          <button
            type="button"
            className="btn-secondary"
            onClick={() => setSignupOpen(true)}
          >
            Create account
          </button>

          <p className="footer-text">
            By signing in you agree to our Terms &amp; Privacy.
          </p>
        </div>
      </div>
    </div>
  );
}
