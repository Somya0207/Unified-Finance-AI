import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import PyPDF2
import io
import pandas as pd
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4

from app.tutor.utils.voice_utils import speech_to_text, text_to_speech
from app.tutor.quiz.tutor_engine import ask_tutor
from app.tutor.quiz.quiz_generator import generate_quiz
from app.tutor.quiz.evaluator import evaluate_answer
from app.tutor.notes.notes_generator import generate_notes

from app.triage.crew import run_crew
from app.triage.database import collection

# SESSION STATE
if "quiz" not in st.session_state:
    st.session_state.quiz = []
if "user_answers" not in st.session_state:
    st.session_state.user_answers = []
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# PAGE CONFIG
st.set_page_config(
    page_title="Unified Finance AI",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Unified Finance AI Platform")

menu = st.sidebar.selectbox(
    "Select Feature",
    [
        "Ask Finance Question",
        "Generate Quiz",
        "Finance Chatbot",
        "Study Notes",
        "Triage Analyzer",
        "Tickets Dashboard"
    ]
)

# ASK FINANCE QUESTION
if menu == "Ask Finance Question":
    st.header("Ask Finance Question")
    if "question" not in st.session_state:
        st.session_state.question = ""
    text_input = st.text_input("Enter your finance question")
    if st.button("🎤 Speak Question"):
        voice_text = speech_to_text()
        st.session_state.question = voice_text
        st.write("You said:", voice_text)
    if text_input:
        st.session_state.question = text_input
    st.divider()
    if st.button("Get Answer") and st.session_state.question:
        answer = ask_tutor(f"You are a finance tutor.\nAnswer clearly in 3-4 sentences.\nQuestion: {st.session_state.question}")
        answer_text = answer.content if hasattr(answer, "content") else answer
        st.subheader("AI Tutor Answer")
        st.write(answer_text)
        audio_file = text_to_speech(answer_text)
        with open(audio_file, "rb") as f:
            audio_bytes = f.read()
        st.audio(audio_bytes, format="audio/mp3")

# GENERATE QUIZ
elif menu == "Generate Quiz":
    st.header("Generate Finance Quiz")
    uploaded_report = st.file_uploader("Upload Investment Report (PDF)", type=["pdf"])
    report_text = None
    if uploaded_report is not None:
        pdf_reader = PyPDF2.PdfReader(uploaded_report)
        report_text = ""
        for page in pdf_reader.pages:
            report_text += page.extract_text()
        st.success("Investment Report Uploaded Successfully")
    topic = st.text_input("Enter Topic")
    col1, col2 = st.columns(2)
    with col1:
        difficulty = st.radio("Select Difficulty", ["easy", "medium", "hard"], horizontal=True)
    with col2:
        num_questions = st.slider("Number of Questions", 3, 15, 5)
    if st.button("Generate Quiz"):
        if not topic:
            st.warning("Please enter a topic first.")
            st.stop()
        st.session_state.difficulty = difficulty
        st.session_state.num_questions = num_questions
        quiz_data = generate_quiz(topic, report_text, difficulty, num_questions)
        if not quiz_data:
            st.error("Quiz could not be generated.")
        else:
            st.session_state.quiz = quiz_data
            st.session_state.submitted = False
            st.success("Quiz generated successfully!")

    if st.session_state.get("quiz"):
        st.info(f"📊 Difficulty: {st.session_state.difficulty.upper()}\n📝 Questions: {st.session_state.num_questions}")
        st.subheader("Generated Quiz")
        user_answers = []
        for i, q in enumerate(st.session_state.quiz):
            st.write(f"### Question {i+1}")
            st.write(q["question"])
            answer = st.radio("Select your answer:", q["options"], key=f"q{i}")
            user_answers.append(answer)
        if st.button("Submit Quiz"):
            st.session_state.submitted = True
            st.session_state.user_answers = user_answers

    if st.session_state.get("submitted"):
        score = 0
        st.header("Quiz Results")
        for i, q in enumerate(st.session_state.quiz):
            user = st.session_state.user_answers[i]
            correct = q["answer"]
            if correct in ["A", "B", "C", "D"]:
                correct_index = ord(correct) - ord("A")
                correct_text = q["options"][correct_index]
            else:
                correct_text = correct
            evaluation = evaluate_answer(q["question"], correct_text, user)
            if user.strip().lower() == correct_text.strip().lower():
                score += 1
                st.markdown(f"### Question {i+1} 🟢 Correct")
            else:
                st.markdown(f"### Question {i+1} 🔴 Incorrect")
            st.write("Your Answer:", user)
            st.write("Correct Answer:", correct_text)
            st.write("AI Evaluation:", evaluation)
            st.write("Explanation:", q["explanation"])
            st.divider()
        st.success(f"Final Score: {score}/{len(st.session_state.quiz)}")
        
        buffer = io.BytesIO()
        styles = getSampleStyleSheet()
        pdf = SimpleDocTemplate(buffer)
        story = []
        story.append(Paragraph("Finance Quiz Results", styles["Title"]))
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Final Score: {score}/{len(st.session_state.quiz)}", styles["Heading2"]))
        story.append(Spacer(1, 20))
        for i, q in enumerate(st.session_state.quiz):
            story.append(Paragraph(f"Question {i+1}: {q['question']}", styles["Heading3"]))
            story.append(Spacer(1, 5))
            story.append(Paragraph(f"Your Answer: {st.session_state.user_answers[i]}", styles["Normal"]))
            story.append(Paragraph(f"Correct Answer: {q['answer']}", styles["Normal"]))
            story.append(Paragraph(f"Explanation: {q['explanation']}", styles["Normal"]))
            story.append(Spacer(1, 15))
        pdf.build(story)
        buffer.seek(0)
        st.download_button("Download Quiz Results as PDF", data=buffer, file_name="finance_quiz_results.pdf", mime="application/pdf")

# FINANCE CHATBOT
elif menu == "Finance Chatbot":
    st.header("💬 Finance Chatbot")
    uploaded_report = st.file_uploader("Upload Finance Report (PDF)", type=["pdf"])
    if uploaded_report is not None:
        pdf_reader = PyPDF2.PdfReader(uploaded_report)
        report_text = ""
        for page in pdf_reader.pages:
            report_text += page.extract_text()
        st.session_state.report_text = report_text
        st.success("Finance Report Uploaded Successfully")
    st.subheader("🎤 Voice Question")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if st.button("Start Voice Chat"):
        voice_text = speech_to_text()
        if voice_text:
            st.session_state.chat_history.append({"role": "user", "content": voice_text})
            with st.chat_message("user"):
                st.markdown(voice_text)
            report_context = st.session_state.get("report_text", "")[:3000]
            prompt = f"Finance Report Content:\n{report_context}\n\nQuestion:\n{voice_text}"
            response = ask_tutor(prompt)
            response_text = response.content if hasattr(response, "content") else response
            with st.chat_message("assistant"):
                st.markdown(response_text)
            st.session_state.chat_history.append({"role": "assistant", "content": response_text})
            audio_response = text_to_speech(response_text)
            with open(audio_response, "rb") as f:
                audio_bytes = f.read()
            st.audio(audio_bytes, format="audio/mp3")
    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    user_input = st.chat_input("Ask anything about finance...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        report_context = st.session_state.get("report_text", "")[:3000]
        prompt = f"Finance Report Content:\n{report_context}\n\nQuestion:\n{user_input}"
        response = ask_tutor(prompt)
        response_text = response.content if hasattr(response, "content") else response
        with st.chat_message("assistant"):
            st.markdown(response_text)
        st.session_state.chat_history.append({"role": "assistant", "content": response_text})

# STUDY NOTES
elif menu == "Study Notes":
    st.header("Finance Study Notes")
    topic = st.text_input("Enter topic")
    if st.button("Generate Notes"):
        notes = generate_notes(topic)
        st.subheader("Generated Notes")
        st.write(notes)
        st.session_state.notes = notes
    if "notes" in st.session_state:
        if st.button("Download Notes"):
            buffer = io.BytesIO()
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle("Title", parent=styles["Title"], alignment=1, spaceAfter=20)
            heading_style = ParagraphStyle("Heading", parent=styles["Heading2"], spaceBefore=12, spaceAfter=6)
            text_style = ParagraphStyle("Text", parent=styles["Normal"], leftIndent=10, spaceAfter=5, leading=14)
            bullet_style = ParagraphStyle("Bullet", parent=styles["Normal"], leftIndent=25, spaceAfter=4, leading=14)
            pdf = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            story = []
            story.append(Paragraph("Finance Study Notes", title_style))
            story.append(Spacer(1,15))
            lines = st.session_state.notes.split("\n")
            for line in lines:
                line = line.strip()
                if not line:
                    story.append(Spacer(1,8))
                elif line.startswith(("I.", "II.", "III.", "IV.", "V.", "VI.", "VII.")):
                    story.append(Spacer(1,10))
                    story.append(Paragraph(f"<b>{line}</b>", heading_style))
                elif line.startswith("**") and line.endswith("**"):
                    text = line.replace("**", "")
                    story.append(Paragraph(f"<b>{text}</b>", heading_style))
                elif len(line) > 2 and line[0].isdigit() and "." in line:
                    story.append(Paragraph(line, text_style))
                elif line.startswith("-"):
                    bullet = line.replace("-", "•", 1)
                    story.append(Paragraph(bullet, bullet_style))
                elif line.startswith("*"):
                    bullet = "• " + line.replace("*","",1)
                    story.append(Paragraph(bullet, bullet_style))
                else:
                    story.append(Paragraph(line, text_style))
            pdf.build(story)
            buffer.seek(0)
            st.download_button("Download PDF", data=buffer, file_name="finance_notes.pdf", mime="application/pdf")

# TRIAGE ANALYZER
elif menu == "Triage Analyzer":
    st.header("Triage Analyzer")
    st.write("Paste a customer message to classify intent, urgency, and extract entities.")
    query = st.text_area("Customer Message", height=200, placeholder="Example: I was charged twice for my subscription...")
    
    if st.button("Run Triage"):
        if query:
            with st.spinner("Analyzing message..."):
                try:
                    raw_result = run_crew(query)
                    parsed = {
                        "category": raw_result.get("intent", "general"),
                        "urgency": raw_result.get("urgency", "low"),
                        "amount": raw_result.get("entities", {}).get("amount", ""),
                    }
                    response_output = raw_result.get("response", "")

                    ticket = {
                        "query": query,
                        "parsed": parsed,
                        "response": response_output,
                        "status": "PROCESSING",
                        "created_at": datetime.utcnow()
                    }
                    result = collection.insert_one(ticket)
                    
                    st.success(f"Ticket saved with ID: {result.inserted_id}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Intent Classification")
                        st.info(parsed["category"].upper())
                    with col2:
                        st.subheader("Urgency Level")
                        urgency_color = "red" if parsed["urgency"] == "high" else "orange" if parsed["urgency"] == "medium" else "green"
                        st.markdown(f"**:{urgency_color}[{parsed['urgency'].upper()}]**")
                    
                    st.subheader("Extracted Entities")
                    st.json(raw_result.get("entities", {}))
                    
                    st.subheader("AI Response")
                    st.write(response_output)
                    
                except Exception as e:
                    st.error(f"Error during triage: {e}")
        else:
            st.warning("Please enter a query to run triage.")

# TICKETS DASHBOARD
elif menu == "Tickets Dashboard":
    st.header("Tickets Dashboard")
    st.write("All triaged support queries and their AI analysis results.")
    
    if st.button("Refresh Tickets"):
        st.rerun()

    try:
        tickets_cursor = collection.find().sort("created_at", -1).limit(50)
        tickets = list(tickets_cursor)
        
        if tickets:
            df = pd.DataFrame([{
                "ID": str(t["_id"])[-8:],
                "Query": t.get("query", "")[:60] + "..." if len(t.get("query", "")) > 60 else t.get("query", ""),
                "Intent": t.get("parsed", {}).get("category", ""),
                "Urgency": t.get("parsed", {}).get("urgency", ""),
                "Status": t.get("status", "PROCESSING"),
                "Date": t.get("created_at", datetime.utcnow()).strftime("%Y-%m-%d %H:%M")
            } for t in tickets])
            
            st.dataframe(df, use_container_width=True)
            
            st.subheader("Ticket Details")
            selected_ticket_id = st.selectbox("Select a ticket ID to view details", [str(t["_id"])[-8:] for t in tickets])
            if selected_ticket_id:
                selected_ticket = next((t for t in tickets if str(t["_id"])[-8:] == selected_ticket_id), None)
                if selected_ticket:
                    st.markdown(f"**Query:** {selected_ticket.get('query')}")
                    st.markdown(f"**Intent:** {selected_ticket.get('parsed', {}).get('category')}")
                    st.markdown(f"**Urgency:** {selected_ticket.get('parsed', {}).get('urgency')}")
                    st.markdown("**AI Response:**")
                    st.info(selected_ticket.get("response", "No response generated."))
        else:
            st.info("No tickets found. Use the Triage Analyzer to process some queries.")
    except Exception as e:
        st.error(f"Error connecting to database. Make sure MongoDB is running and MONGO_URI is set. ({e})")