# 📊 Unified Finance AI Platform

A comprehensive, AI-driven platform that integrates financial education (**Tutor**) and customer support automation (**Triage**) into a single, cloud-ready application.

---

## 🚀 Key Features

### 👨‍🏫 AI Finance Tutor
- **Voice Q&A**: Ask any financial question and get concise answers with text-to-speech support.
- **Smart Quiz Generator**: Upload Investment Reports (PDF) or select a topic to generate custom quizzes with AI evaluation.
- **Study Notes**: Instantly generate and download structured finance study notes in PDF format.
- **Context-Aware Chatbot**: Chat with an AI that understands your uploaded financial documents.

### 📥 AI Triage System
- **Automated Classification**: Uses **CrewAI** agents to analyze customer support messages for intent and urgency.
- **Entity Extraction**: Automatically extracts critical data like transaction amounts and dates.
- **Dashboard**: A centralized interface to track, manage, and review triaged support tickets.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | Streamlit |
| **AI Orchestration** | LangChain, CrewAI |
| **LLM Models** | Google Gemini, Groq (Llama 3) |
| **Database** | SQLite (Local & Persistent) |
| **Infrastructure** | AWS (EC2, VPC), Terraform |
| **DevOps** | Docker, GitHub Actions |

---

## 📦 Local Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Somya0207/Unified-Finance-AI.git
   cd unified-system
   ```

2. **Set up Environment Variables**:
   Create a `.env` file and add your API keys:
   ```env
   GROQ_API_KEY=your_key_here
   GOOGLE_API_KEY=your_key_here
   ```

3. **Run with Python**:
   ```bash
   pip install -r requirements.txt
   streamlit run main.py
   ```

4. **Run with Docker**:
   ```bash
   docker build -t unified-finance-ai .
   docker run -p 8501:8501 --env-file .env unified-finance-ai
   ```

---

## 🏗️ Architecture & CI/CD
This project is built with **Production-Grade DevOps**:
- **GitHub Actions**: Automated pipeline for building Docker images.
- **Terraform**: Infrastructure-as-Code for one-click deployment to AWS.
- **Containerization**: Fully Dockerized for consistent performance across environments.

---

## 📜 License
This project is licensed under the MIT License - see the LICENSE file for details.
