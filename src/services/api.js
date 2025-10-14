import React, { useState } from "react";
import "./Chatbot.css";
import { chatWithBot } from "../services/api";  // ← 確保 import 這條

export default function Chatbot() {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "👋 Hello! I'm your AI Scheduling Assistant. How can I help you today?" },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    if (!input.trim() || sending) return;

    const userText = input.trim();
    const userMsg = { sender: "user", text: userText };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setSending(true);

    try {
      const reply = await chatWithBot(userText);
      const botMsg = { sender: "bot", text: reply };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      console.error("Chatbot error:", err);
      const errMsg = { sender: "bot", text: "⚠️ Error: cannot reach server." };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setSending(false);
    }
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
          placeholder={sending ? "Sending..." : "Type your message..."}
          value={input}
          disabled={sending}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              handleSend();
            }
          }}
        />
        <button onClick={handleSend} disabled={sending}>
          Send
        </button>
      </div>
    </div>
  );
}
