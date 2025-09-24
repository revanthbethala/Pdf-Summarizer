import streamlit as st
from PyPDF2 import PdfReader
import google.generativeai as genai
import mammoth
import json
from dotenv import load_dotenv
import re
import os

load_dotenv()

# Custom CSS for better UI
st.markdown(
    """
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    
    .sub-header {
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .topic-card {
        padding: 1rem;
        margin: 0.3rem 0;
    }
    
    .summary-box {
        border-left: 4px solid #007bff;
        padding: 1.5rem;
    }
    
    .quiz-question {
        padding: 1.5rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .quiz-option {
        background: white;
        border: 2px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .quiz-option:hover {
        border-color: #007bff;
        box-shadow: 0 2px 8px rgba(0,123,255,0.2);
    }
    
    .score-excellent {
        background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 1rem 0;
    }
    
    .score-good {
        background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 1rem 0;
    }
    
    .score-needs-improvement {
        background: linear-gradient(135deg, #fd79a8 0%, #e84393 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 1rem 0;
    }
    
    .upload-area {
        border: 2px dashed #007bff;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        background: linear-gradient(135deg, #f8f9ff 0%, #e6f3ff 100%);
        margin: 1rem 0;
    }
    
    .stButton > button {
        border-radius: 25px;
        border: none;
        padding: 0.5rem 1.5rem;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    .progress-container {
        background: #e9ecef;
        border-radius: 25px;
        padding: 0.25rem;
        margin: 1rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)

SUMMARY_SYSTEM_MESSAGE = """
You are an intelligent AI assistant. Your task is to process user-provided content and create a comprehensive summary.

Generate a summary in the following JSON format:
{
  "title": "Main content or subject the file focuses on",
  "topics": ["List of all key topics covered at a high level. Only include main topics, not subtypes or granular details. For example, for memory consistency models, just include 'Memory Consistency Models', not strong, weak, or other types."],
  "summary": "A clear and detailed summary covering important information, insights, or events. Make this comprehensive and well-structured."
}

The response must be strictly valid JSON (no extra text, no markdown). Only provide high-level topics in the topics array.
"""

QUIZ_SYSTEM_MESSAGE = """
You are an intelligent quiz generator. Based on the provided content, generate exactly 10 multiple-choice questions.

Generate quizzes in the following JSON format:
{
  "quiz": [
    {
      "question": "Clear MCQ question based on the content",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Correct option (must match exactly one of the options)",
      "explanation": "Brief explanation why this answer is correct"
    }
  ]
}

Requirements:
- Generate exactly 10 questions
- Each question must have exactly 4 options
- Questions should cover different aspects of the content
- Vary the difficulty level
- The response must be strictly valid JSON (no extra text, no markdown).
"""

model_name = "gemini-2.0-flash"

# -------------------- FILE EXTRACTORS --------------------


def extract_pdf(uploaded_file):
    extracted_text = ""
    reader = PdfReader(uploaded_file)
    for page in reader.pages:
        extracted_text += page.extract_text()
    return extracted_text


def extract_doc(uploaded_file):
    pages = mammoth.extract_raw_text(uploaded_file)
    text = pages.value
    extracted_text = re.sub(r"\s+", " ", text)
    return extracted_text


def extract_text(uploaded_file):
    lines = uploaded_file.readlines()
    decoded_lines = [line.decode("utf-8").strip() for line in lines]
    return " ".join(decoded_lines)


# -------------------- AI FUNCTIONS --------------------


# -------------------- HELPER: CHUNKING --------------------
def chunk_text(text, max_tokens=2000):
    """
    Splits the text into smaller chunks.
    max_tokens is approximate number of words per chunk.
    """
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_tokens):
        chunk = " ".join(words[i : i + max_tokens])
        chunks.append(chunk)
    return chunks


# -------------------- AI FUNCTIONS WITH CHUNKING --------------------
@st.cache_data(show_spinner=False)
def generate_summary(text):
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        chunks = chunk_text(text, max_tokens=1000)  # smaller chunks for long docs
        chunk_summaries = []

        for chunk in chunks:
            prompt = f"{SUMMARY_SYSTEM_MESSAGE}\n\nContent to summarize:\n{chunk}"
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                ),
            )
            formatted_response = response.text.replace("```json", "").replace("```", "")
            chunk_summary = json.loads(formatted_response)
            chunk_summaries.append(chunk_summary)

        # Combine chunk summaries into a final summary
        combined_summary_text = " ".join([c["summary"] for c in chunk_summaries])
        combined_topics = []
        for c in chunk_summaries:
            for t in c.get("topics", []):
                if t not in combined_topics:
                    combined_topics.append(t)

        final_summary = {
            "title": chunk_summaries[0].get("title", "Untitled"),
            "topics": combined_topics,
            "summary": combined_summary_text,
        }
        return final_summary

    except Exception as e:
        print(str(e))
        return {"error": str(e)}

@st.cache_data(show_spinner=False)
def generate_quiz(text):
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        chunks = chunk_text(text, max_tokens=1000)
        all_quizzes = []

        for chunk in chunks:
            prompt = f"{QUIZ_SYSTEM_MESSAGE}\n\nContent for quiz generation:\n{chunk}"
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                ),
            )
            formatted_response = response.text.replace("```json", "").replace("```", "")
            chunk_quiz = json.loads(formatted_response)
            all_quizzes.extend(chunk_quiz.get("quiz", []))

        # Keep only 10 questions max
        final_quiz = {"quiz": all_quizzes[:10]}
        return final_quiz

    except Exception as e:
        return {"error": str(e)}


# -------------------- STREAMLIT UI --------------------

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "home"
if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = ""
if "summary_data" not in st.session_state:
    st.session_state.summary_data = None
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "current_question" not in st.session_state:
    st.session_state.current_question = 0
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "quiz_completed" not in st.session_state:
    st.session_state.quiz_completed = False


def reset_app():
    st.session_state.page = "home"
    st.session_state.extracted_text = ""
    st.session_state.summary_data = None
    st.session_state.quiz_data = None
    st.session_state.current_question = 0
    st.session_state.user_answers = {}
    st.session_state.quiz_completed = False


# HOME PAGE
if st.session_state.page == "home":
    st.markdown(
        '<h1 class="main-header">AI-Powered Document Summarization and Assessment Tool</h1>',
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Choose a file",
        accept_multiple_files=False,
        type=["pdf", "docx", "txt"],
        help="Upload PDF, DOCX, TXT files for analysis",
    )

    if uploaded_file:
        st.success(f"✅ File uploaded: {uploaded_file.name}")

        with st.spinner("🔄 Processing your file..."):
            if uploaded_file.name.endswith("pdf"):
                st.session_state.extracted_text = extract_pdf(uploaded_file)
            elif uploaded_file.name.endswith("docx"):
                st.session_state.extracted_text = extract_doc(uploaded_file)
            elif uploaded_file.name.endswith("txt"):
                st.session_state.extracted_text = extract_text(uploaded_file)
        if st.session_state.extracted_text:
            with st.spinner("🧠 Generating intelligent summary..."):
                st.session_state.summary_data = generate_summary(
                    st.session_state.extracted_text
                )
                st.session_state.page = "summary"
                st.rerun()

# SUMMARY PAGE
elif st.session_state.page == "summary":
    if st.session_state.summary_data and "error" not in st.session_state.summary_data:
        # st.markdown(
        #     '<h1 class="main-header">📋 Document Summary</h1>', unsafe_allow_html=True
        # )

        doc_title = st.session_state.summary_data.get("title", "Untitled")
        doc_topics = st.session_state.summary_data.get("topics", [])
        doc_summary = st.session_state.summary_data.get("summary", "")

        # Display title with custom styling
        st.markdown(
            f'<h2 class="main-header"> {doc_title}</h2>', unsafe_allow_html=True
        )

        # Display topics in cards
        st.markdown(
            '<h3 class="sub-header">🎯 Key Topics Covered</h3>', unsafe_allow_html=True
        )
        if doc_topics:
            cols = st.columns(2)
            for i, topic in enumerate(doc_topics):
                col = cols[i % 2]
                with col:
                    st.markdown(
                        f'<div class="topic-card"><strong>{i+1}.</strong> {topic}</div>',
                        unsafe_allow_html=True,
                    )

        # Display summary in a styled box
        st.markdown(
            '<h3 class="sub-header">📖 Comprehensive Summary</h3>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="summary-box">{doc_summary}</div>', unsafe_allow_html=True
        )

        # Action buttons with better spacing
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if st.button("🏠 Home", use_container_width=True, type="secondary"):
                reset_app()
                st.rerun()

        with col2:
            if st.button("🎯 Generate Quiz", use_container_width=True, type="primary"):
                with st.spinner("🔄 Creating quiz questions..."):
                    st.session_state.quiz_data = generate_quiz(
                        st.session_state.extracted_text
                    )
                    st.session_state.current_question = 0
                    st.session_state.user_answers = {}
                    st.session_state.quiz_completed = False
                    st.session_state.page = "quiz"
                    st.rerun()
    else:
        st.error("❌ Failed to generate summary. Please try again.")
        if st.button("🏠 Back to Home", type="primary"):
            reset_app()
            st.rerun()

# QUIZ PAGE
elif st.session_state.page == "quiz":
    if st.session_state.quiz_data and "error" not in st.session_state.quiz_data:
        quizzes = st.session_state.quiz_data.get("quiz", [])

        if quizzes and st.session_state.current_question < len(quizzes):
            current_q = quizzes[st.session_state.current_question]

            st.markdown(
                '<h1 class="main-header">🎯 Knowledge Quiz</h1>', unsafe_allow_html=True
            )

            # Enhanced progress bar
            progress = (st.session_state.current_question + 1) / len(quizzes)
            st.markdown(
                f"""
            <div style="text-align: center; margin: 1rem 0;">
                <h4>Question {st.session_state.current_question + 1} of {len(quizzes)}</h4>
            </div>
            """,
                unsafe_allow_html=True,
            )

            st.progress(progress)

            # Question display with custom styling
            st.markdown(
                f'<div class="quiz-question"><h3>{current_q["question"]}</h3></div>',
                unsafe_allow_html=True,
            )

            # Options without auto-selection
            options = current_q.get("options", [])

            # Create a unique key for this question that doesn't auto-select
            answer_key = f"quiz_answer_{st.session_state.current_question}"

            # Get previously selected answer for this question, if any
            previously_selected = st.session_state.user_answers.get(
                st.session_state.current_question, None
            )

            # Display options
            st.markdown("### Choose your answer:")
            user_answer = st.radio(
                "Select one option:",
                options,
                index=(
                    options.index(previously_selected)
                    if previously_selected in options
                    else None
                ),
                key=answer_key,
                label_visibility="collapsed",
            )

            st.markdown("<br>", unsafe_allow_html=True)

            # Navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])

            with col1:
                if st.session_state.current_question > 0:
                    if st.button(
                        "← Previous", use_container_width=True, type="secondary"
                    ):
                        # Save current answer before moving
                        if user_answer:
                            st.session_state.user_answers[
                                st.session_state.current_question
                            ] = user_answer
                        st.session_state.current_question -= 1
                        st.rerun()

            with col3:
                button_text = (
                    "Finish Quiz"
                    if st.session_state.current_question == len(quizzes) - 1
                    else "Next →"
                )
                button_disabled = user_answer is None

                if st.button(
                    button_text,
                    use_container_width=True,
                    type="primary",
                    disabled=button_disabled,
                ):
                    # Save the answer
                    st.session_state.user_answers[st.session_state.current_question] = (
                        user_answer
                    )

                    if st.session_state.current_question < len(quizzes) - 1:
                        st.session_state.current_question += 1
                        st.rerun()
                    else:
                        st.session_state.quiz_completed = True
                        st.session_state.page = "results"
                        st.rerun()

                if button_disabled:
                    st.caption("Please select an answer to continue")

        else:
            st.error("❌ No quiz questions available.")
            if st.button("🏠 Back to Home"):
                reset_app()
                st.rerun()
    else:
        st.error("❌ Failed to generate quiz. Please try again.")
        if st.button("🏠 Back to Home"):
            reset_app()
            st.rerun()

# RESULTS PAGE
elif st.session_state.page == "results":
    st.markdown('<h1 class="main-header">🎉 Quiz Results</h1>', unsafe_allow_html=True)

    if st.session_state.quiz_data and st.session_state.user_answers:
        quizzes = st.session_state.quiz_data.get("quiz", [])
        correct_count = 0
        total_questions = len(quizzes)

        # Calculate score
        for i, quiz in enumerate(quizzes):
            user_answer = st.session_state.user_answers.get(i, "")
            if user_answer == quiz["correct_answer"]:
                correct_count += 1

        score_percentage = (correct_count / total_questions) * 100

        # Display score with custom styling
        if score_percentage >= 80:
            st.markdown(
                f"""
            <div class="score-excellent">
                <h2>🎉 Excellent Performance!</h2>
                <h3>Your Score: {correct_count}/{total_questions} ({score_percentage:.1f}%)</h3>
                <p>Outstanding! You have a great understanding of the material!</p>
            </div>
            """,
                unsafe_allow_html=True,
            )
        elif score_percentage >= 60:
            st.markdown(
                f"""
            <div class="score-good">
                <h2>👍 Good Job!</h2>
                <h3>Your Score: {correct_count}/{total_questions} ({score_percentage:.1f}%)</h3>
                <p>Well done! Keep up the good work!</p>
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
            <div class="score-needs-improvement">
                <h2>📚 Keep Learning!</h2>
                <h3>Your Score: {correct_count}/{total_questions} ({score_percentage:.1f}%)</h3>
                <p>You might want to review the material again. Don't give up!</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

        # Detailed results
        st.markdown(
            '<h3 class="sub-header">📊 Detailed Review</h3>', unsafe_allow_html=True
        )

        for i, quiz in enumerate(quizzes):
            user_answer = st.session_state.user_answers.get(i, "No answer")
            is_correct = user_answer == quiz["correct_answer"]

            status = "✅ Correct" if is_correct else "❌ Incorrect"
            with st.expander(f"Question {i+1} - {status}", expanded=False):
                st.markdown(f"**❓ Question:** {quiz['question']}")
                st.markdown(f"**👤 Your Answer:** {user_answer}")
                st.markdown(f"**✅ Correct Answer:** {quiz['correct_answer']}")
                st.markdown(f"**💡 Explanation:** {quiz['explanation']}")

        # Action buttons
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("🏠 Home", use_container_width=True, type="secondary"):
                reset_app()
                st.rerun()

        with col2:
            if st.button("🔄 Retry Quiz", use_container_width=True, type="primary"):
                st.session_state.current_question = 0
                st.session_state.user_answers = {}
                st.session_state.quiz_completed = False
                st.session_state.page = "quiz"
                st.rerun()

        with col3:
            if st.button(
                "📖 Back to Summary", use_container_width=True, type="secondary"
            ):
                st.session_state.page = "summary"
                st.rerun()

else:
    reset_app()
    st.rerun()
