# 📄 PDF/Docx/Txt Summarizer with Gemini AI

A powerful Streamlit web app that allows you to upload documents (`.pdf`, `.docx`, or `.txt`) and receive a structured, intelligent summary using **Google's Gemini AI**.

---

## 🚀 Features

- 📤 Upload files in **PDF**, **DOCX**, or **TXT** format
- 📄 Automatically extracts and cleans the text from the uploaded document
- 🤖 Uses **Google Gemini 2.0 Flash** to summarize the document content
- 📊 Outputs results in structured **JSON format** with:
  - **Title** of the document
  - List of **topics** covered
  - **Detailed summary** of the text
- 🧱 Clean and intuitive UI built with Streamlit
- 🪄 Neatly displays topics in 3 columns for better readability

---

## 🛠️ Tech Stack

- [Streamlit](https://streamlit.io/) – UI and app framework
- [PyPDF2](https://pypi.org/project/PyPDF2/) – PDF parsing and text extraction
- [Mammoth](https://pypi.org/project/mammoth/) – DOCX text extraction
- [Google Generative AI (Gemini)](https://ai.google.dev/) – For summarization
- [dotenv](https://pypi.org/project/python-dotenv/) – Environment variable management
- `re`, `json`, and `os` – Native Python libraries for processing and file handling

---

## 🧠 Gemini Prompt Structure

The Gemini model is prompted with:

```json
{
  "title": "main content name that document focuses",
  "topics": ["all the topics covered in the document"],
  "summary": "detailed and informative summary of the document"
}
```
---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/revanthbethala/pdf-summarizer.git
cd pdf-summarizer
```
### 2. Create and Activate a Virtual Environment (Recommended)

```bash
python -m venv venv
venv\Scripts\activate
```
### 3. Install Dependencies

```bash
pip install -r requirements.txt
```
### 4. Add Your Gemini API Key  in .env file

```bash
GEMINI_API_KEY=your_api_key_here
```

### 5. Run the app
```bash
streamlit run app.py
```
