import React, { useState } from "react";
import axios from "axios";
import "./Chatbot.css";

export default function Chatbot() {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "👋 Hello! I'm your AI Scheduling Assistant. Describe a task and I’ll add it for you." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const userId = localStorage.getItem("user_id"); // ✅ 从登录信息中获取
      const res = await axios.post(
        `http://127.0.0.1:8000/chatbot/reply?user_id=${userId}`,
        { message: input }
      );

      if (res.data && res.data.task_data) {
        const task = res.data.task_data;
        const botText = `✅ Task "${task.task_name}" created!\n\n📅 Mode: ${task.task_mode}\n🕒 ${
          task.task_deadline || task.task_start_time
        }\n⏱ Duration: ${task.expected_duration || task.task_duration} min\n⭐ Priority: ${
          task.task_priority
        }\n🎯 Difficulty: ${task.expected_difficulty}`;
        setMessages((prev) => [...prev, { sender: "bot", text: botText }]);
      } else {
        const raw = res.data?.gpt_raw || "⚠️ No GPT output received.";
        const msg = res.data?.message
          ? `${res.data.message}\n\n🧠 GPT Raw Output:\n${raw}`
          : `🧠 GPT Raw Output:\n${raw}`;
        setMessages((prev) => [...prev, { sender: "bot", text: msg }]);
      }
    } catch (err) {
      console.error("❌ Chatbot error:", err);
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "⚠️ Sorry, I couldn’t process your request." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chatbot-container">
      <div className="chat-header">
        <h2>AI Task Chatbot 🤖</h2>
        <p>Describe your task in natural language — I’ll add it automatically!</p>
      </div>

      <div className="chat-window">
        {messages.map((msg, index) => (
          <div key={index} className={`chat-message ${msg.sender}`}>
            <div className="message-bubble">{msg.text}</div>
          </div>
        ))}
        {loading && (
          <div className="chat-message bot">
            <div className="message-bubble">🧠 Thinking...</div>
          </div>
        )}
      </div>

      <div className="chat-input-area">
        <input
          type="text"
          placeholder="E.g. Finish AI report by tomorrow night"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <button onClick={handleSend} disabled={loading}>
          {loading ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}
