import streamlit as st
from PyPDF2 import PdfReader
from google import genai
import json

SYSTEM_MESSAGE = """You are an intelligent text summarizer. Your task is to summarize the structured information
from the given text and convert it into a pure JSON format. The JSON format is as follows:
{
    "summarized_text": "data"
}"""

USER_MESSAGE = "Extract the following information from the provided text"

st.title("PDF SUMMARIZER")
uploaded_file = st.file_uploader(
    "Upload a file", accept_multiple_files=False, type=["pdf"]
)


def summarize_with_gemini(text):
    try:
        client = genai.Client(api_key="AIzaSyAl6IOxAGuL6gjKb2OTUTSy1g8KlUahuz0")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"{SYSTEM_MESSAGE}\n{USER_MESSAGE}\n{text}",
        )
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"


col1, col2 = st.columns(2)
extracted_text = ""
if uploaded_file:
    reader = PdfReader(uploaded_file)
    for page in reader.pages:
        extracted_text += page.extract_text()

    if extracted_text:
        with st.spinner("Summarizing..."):
            summary = summarize_with_gemini(extracted_text)
            formatted_summary = summary.replace("```json", "")
            formatted_summary = formatted_summary.replace("```", "")
        with col1:
            st.title("Extracted Text")
            st.write(extracted_text)
        try:
            summary_json = json.loads(formatted_summary)
            with col2:
                st.title("Summary")
                st.write(summary_json.get("summarized_text", "No summary found."))
        except json.JSONDecodeError:
            with col2:
                st.error("Error: Could not parse response from Gemini.")
                st.text(formatted_summary)
else:
    st.info("Please upload a PDF, DOC, DOCX, or TXT file.")
