## 🚀 Adaptive LLM-Based Conversational AI

A research-grade chatbot system designed to adapt responses based on **user personality**, using local LLMs (like Gemma 3B), long-term memory, sentiment tracking, and persona-aware responses. Built using **FastAPI** (backend) and **React + Bootstrap** (frontend).

<!-- ![screenshot](https://user-images.githubusercontent.com/your-screenshot.png) -->

---

### 📦 Features

* 🔁 **Adaptive LLM responses** based on personality types
* 💡 **Memory and sentiment-aware context**
* 🧠 Persona distribution chart + conversation insights
* 📜 Full chat history display
* 🎨 Clean and responsive UI using React-Bootstrap
* 📊 Recharts & Chart.js for personality and intelligence graphs
* 💬 Integrated API with FastAPI backend

---

### 🛠️ Technologies

**Backend (FastAPI):**

* LangChain
* Ollama (LLMs like Gemma 3B)
* SQLite (chat + persona memory)
* pydantic + CORS setup

**Frontend (React):**

* React.js (Vite or Create React App)
* Bootstrap 5 & React-Bootstrap
* Chart.js + Recharts
* FontAwesome for UI icons

---

### 🖥️ Installation

#### 1. Clone the repository

```bash
git clone https://github.com/alihassanml/Adaptive-LLM-Based-Conversational-AI.git
cd Adaptive-LLM-Based-Conversational-AI
```

#### 2. Backend Setup (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

> Make sure Ollama is running locally and a supported model like `gemma:3b` is downloaded.

#### 3. Frontend Setup (React)

```bash
cd frontend
npm install
npm run dev  # or npm start if using CRA
```

---

### 📊 Dashboard Overview

* **🧠 Conversation Insights**: Shows last 5 conversations with user and bot messages.
* **📈 Persona Distribution**: Real-time bar chart showing frequency of detected personality types.
* **💡 Intelligence Stats**: Bar chart (Chart.js) showing model size, memory depth, and persona-awareness level.

---

### 📁 Project Structure

```
Adaptive-LLM-Based-Conversational-AI/
│
├── backend/              # FastAPI + LLM logic
│   ├── main.py
│   ├── memory.py
│   └── models/
│
├── frontend/             # React UI
│   ├── src/
│   └── Home.jsx
│
└── README.md
```

---

### 🔗 API Endpoints

```http
POST   /chat                # Handle user message
GET    /chat/history        # Get conversation history
GET    /persona-counts      # Persona distribution for charts
```

---

### 🧪 Future Additions

* 📥 Export chats as JSON/PDF
* 🧩 Integrate multiple persona models (MBTI, Big Five)
* 🧠 Add vector database for semantic memory
* 📱 Mobile-friendly UI and dark mode toggle

---

### 🤖 Maintainer

**Ali Hassan** – [@alihassanml](https://github.com/alihassanml)
*BS Computer Science | Data Science Specialist*

---

### 🪪 License

MIT License