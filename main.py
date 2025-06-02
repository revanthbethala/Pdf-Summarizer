import streamlit as st
from PyPDF2 import PdfReader
import google.generativeai as genai
import mammoth
import json
from dotenv import load_dotenv
import re
import os

load_dotenv()
SYSTEM_MESSAGE = """You are an intelligent text summarizer. Your task is to summarize the structured information
from the given text and convert it into a pure JSON format. The JSON format is as follows:
{
    "title":"main content name that document focuses" ,
    "topics":["all the topics that are covered in the document in the form of a array"]
    "summary": "summarized text of the document in a detailed way by representing the necessary data from the document"
}"""

USER_MESSAGE = "Extract the following information from the provided text"
model_name = "gemini-2.0-flash"


def extract_pdf(uploaded_file):
    extracted_text = ""
    reader = PdfReader(uploaded_file)
    for page in reader.pages:
        extracted_text += page.extract_text()
    return extracted_text


def extract_doc(uploaded_file):
    pages = mammoth.extract_raw_text(uploaded_file)
    text = pages.value
    extracted_text = re.sub(r"\s+", "  ", text)
    return extracted_text


def extract_text(uploaded_file):
    lines = uploaded_file.readlines()
    decoded_lines = [line.decode("utf-8").strip() for line in lines]
    full_text = " ".join(decoded_lines)
    return full_text


def summarize_with_gemini(text):
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        prompt = f"{SYSTEM_MESSAGE}\n {USER_MESSAGE}\n{text}"
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
            ),
        )
        formatted_response = response.text.replace("```json", "")
        formatted_response = formatted_response.replace("```", "")
        formatted_response = json.loads(formatted_response)
        return formatted_response
    except Exception as e:
        return f"Error: {str(e)}"


st.title("PDF SUMMARIZER")
uploaded_file = st.file_uploader(
    "Upload a file", accept_multiple_files=False, type=["pdf", "docx", "txt"]
)
extracted_text = ""


if uploaded_file and uploaded_file.name.endswith("pdf"):
    extracted_text = extract_pdf(uploaded_file)
elif uploaded_file and uploaded_file.name.endswith("docx"):
    extracted_text = extract_doc(uploaded_file)
elif uploaded_file and uploaded_file.name.endswith("txt"):
    extracted_text = extract_text(uploaded_file)

if uploaded_file and extracted_text:
    with st.spinner("Summarizing"):
        try:
            summarized_data = summarize_with_gemini(extracted_text)
            print(summarized_data)
            doc_title = summarized_data["title"]
            doc_topics = summarized_data["topics"]
            doc_summary = summarized_data["summary"]
            st.title("Summarized Data")
            st.title(f"Topic Name: {doc_title}")
            st.subheader("Topics Covered:")
            cols = st.columns(3)
            for index, topic in enumerate(doc_topics):
                col = cols[index % 3]
                col.write(f"{index + 1}. {topic}")
            st.write("**Summarized Text**")
            st.write(doc_summary)
        except Exception as e:
            st.error(f"Error Occurred: {e}")
else:
    st.info("Please upload the file in doc or pdf or txt formats")
