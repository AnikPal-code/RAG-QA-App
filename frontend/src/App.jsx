import React from "react";
import ChatBox from "./components/ChatBox";
import "./App.css";

function App() {
  return (
    <div className="App">
      <header>
        <h1>🧠 RAG QA Bot</h1>
        <p>Your personalized document assistant</p>
      </header>
      <main>
        <ChatBox />
      </main>
    </div>
  );
}

export default App;
