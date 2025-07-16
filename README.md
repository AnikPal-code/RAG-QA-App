# 🧠 RAG-QA App

A Retrieval-Augmented Generation (RAG) based Question Answering system that leverages your own documents and **open-source Hugging Face models** to generate accurate, context-aware answers.

> 📌 Built using FastAPI, ChromaDB, Hugging Face Transformers — deployed for demo purposes only.

---

## 🎥 Demo Video

▶️ Check out "testing.mp4" to view the working of my application.
I had used "Render" to deploy my backend for it's memory limit for free trial exceeded.

---

## 🚀 Live Frontend

🌐 [Frontend Hosted on Vercel](https://your-vercel-url.vercel.app)

---

## ⚙️ Features

- 🔍 **Document-based QA** with RAG architecture
- 🤖 Uses **Hugging Face Transformers** for generation
- 🧠 Retrieves relevant context using **ChromaDB vector store**
- 🧾 Upload or use pre-indexed PDF/text documents
- ⚡ FastAPI backend + Vercel frontend
- 📦 Docker + Railway deployment (backend)

---

## 🛠️ Tech Stack

| Layer      | Tech                                 |
|------------|--------------------------------------|
| 🧠 Backend | FastAPI, Hugging Face Transformers   |
| 📚 Retrieval | ChromaDB (embedding + storage)      |
| 🎯 Frontend| React (Vercel)                        |
| 🐳 Deployment | Render (backend), Vercel (frontend) |
| 🔐 Env Vars | Hugging Face model token, etc.       |

---

## 📁 Project Structure

RAG-QA-App/

├── backend/ # FastAPI + QA system + Docker + Chroma_DB, etc.

├── frontend/ # Frontend (hosted on Vercel)

├── .gitignore (untracked files)

├── testing.mp4 (Demo Video)
