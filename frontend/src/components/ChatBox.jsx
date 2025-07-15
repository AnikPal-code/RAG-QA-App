import React, { useState, useEffect, useRef } from "react";
import "./ChatBox.css";

const ChatBox = () => {
  const [question, setQuestion] = useState("");
  const [answerList, setAnswerList] = useState([]); // track multiple Q&A
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [hasDocument, setHasDocument] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    checkStatus();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [answerList]);

  const checkStatus = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/status");
      const data = await response.json();
      setHasDocument(data.has_document);
    } catch (error) {
      console.error("Error checking status:", error);
    }
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setUploadStatus(null);
  };

  const handleUpload = async () => {
    if (!file) {
      setUploadStatus({ success: false, message: "Please select a file." });
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://127.0.0.1:8000/upload", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setUploadStatus({ success: true, message: data.message });
        setHasDocument(true);
        setFile(null);
        document.getElementById("file-input").value = "";
      } else {
        setUploadStatus({ success: false, message: data.detail || "Upload failed" });
      }
    } catch (error) {
      setUploadStatus({ success: false, message: "Upload error" });
    } finally {
      setIsUploading(false);
    }
  };

  const handleAsk = async () => {
    if (!question.trim()) return;

    const currentQuestion = question;
    setAnswerList([...answerList, { type: "question", text: currentQuestion }]);
    setQuestion("");

    try {
      const response = await fetch("http://127.0.0.1:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: currentQuestion }),
      });

      const data = await response.json();

      let reply = "";

      if (typeof data.answer === "object" && data.answer !== null) {
        reply =
          typeof data.answer.result === "string"
            ? data.answer.result
            : JSON.stringify(data.answer.result);
      } else {
        reply = typeof data.answer === "string"
          ? data.answer
          : JSON.stringify(data.answer);
      }

      setAnswerList((prev) => [...prev, { type: "answer", text: reply }]);
    } catch (error) {
      setAnswerList((prev) => [
        ...prev,
        { type: "answer", text: "❌ Failed to get response from server." },
      ]);
    }
  };


  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  return (
    <div className="chat-wrapper">
      <header className="upload-header">
        <h2>📁 Upload .txt Document</h2>

        <div
          className="dropzone"
          onClick={() => document.getElementById("file-input").click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            const droppedFile = e.dataTransfer.files[0];
            setFile(droppedFile);
            setUploadStatus(null);
          }}
        >
          <p>📄 Drag and drop your `.txt` file here or click to select</p>
          <input
            id="file-input"
            type="file"
            accept=".txt"
            onChange={handleFileChange}
            className="file-input-hidden"
          />
        </div>

        {file && (
          <div className="filename-preview">
            Selected file: <strong>{file.name}</strong>
          </div>
        )}

        <div className="upload-button-container">
          <button
            onClick={handleUpload}
            disabled={isUploading || !file}
            className="upload-button"
          >
            {isUploading ? "Uploading..." : "Upload"}
          </button>
        </div>

        <p className="format-info">Supported format: .txt</p>

        {uploadStatus && (
          <div className={`status ${uploadStatus.success ? "success" : "error"}`}>
            {uploadStatus.message}
          </div>
        )}
        {hasDocument && (
          <div className="status success">✅ Document ready. Ask your question below.</div>
        )}
      </header>


      <main className="chat-area">
        {answerList.map((msg, idx) => (
          <div key={idx} className={`chat-bubble ${msg.type}`}>
            {msg.text}
          </div>
        ))}
        <div ref={chatEndRef} />
      </main>

      <footer className="chat-input-area">
        <textarea
          rows={2}
          placeholder={
            hasDocument
              ? "Type your question..."
              : "Upload a document first..."
          }
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyPress}
          disabled={!hasDocument}
        />
        <button onClick={handleAsk} disabled={!hasDocument || !question.trim()}>
          Send
        </button>
      </footer>
    </div>
  );
};

export default ChatBox;
