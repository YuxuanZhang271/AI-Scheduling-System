import React, { useState } from "react";
import "./Chatbot.css";

export default function Chatbot() {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "👋 Hello! I'm your AI Scheduling Assistant. How can I help you today?" },
  ]);
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;

    const newMsg = { sender: "user", text: input };
    setMessages((prev) => [...prev, newMsg]);
    setInput("");

    // 模拟 AI 回复
    setTimeout(() => {
      const reply = { sender: "bot", text: "🤖 I'm processing your request..." };
      setMessages((prev) => [...prev, reply]);
    }, 800);
  };

  return (
    <div className="chatbot-container">
      <div className="chat-header">
        <h2>AI Chatbot 💬</h2>
        <p>Ask me about your schedule, tasks, or reports.</p>
      </div>

      <div className="chat-window">
        {messages.map((msg, index) => (
          <div key={index} className={`chat-message ${msg.sender}`}>
            <div className="message-bubble">{msg.text}</div>
          </div>
        ))}
      </div>

      <div className="chat-input-area">
        <input
          type="text"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <button onClick={handleSend}>Send</button>
      </div>
    </div>
  );
}
