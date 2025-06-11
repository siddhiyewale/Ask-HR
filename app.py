import streamlit as st      # For web interface
import requests             # For API call
import os
from dotenv import load_dotenv       # Loads .env file
from pdf2image import convert_from_bytes      # Added for image-based PDF OCR
import pytesseract   
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"      # Added for OCR

# Helps to load the API Key
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"         # Chat completion url
MODEL = "mistralai/mistral-7b-instruct"                        # Model used(mistral 7B instruct by openrouter)

# Streamlit page setup
st.set_page_config(page_title="Your HR Chatbot", page_icon="🤖")                 # What is being display on the web page
st.title("🤖 Your HR Chatbot")                                                     # Title of the web page
st.write("Ask me anything about HR policies, leave, holidays, or career growth.")

# For uploading pdf file
uploaded_file = st.file_uploader("📄 Upload HR Policy PDF", type=["pdf"])    

# Extracting all the PDF text using OCR
pdf_text = ""
if uploaded_file and "pdf_text" not in st.session_state:
    try:
        from PyPDF2 import PdfReader      # For native text extraction
        pdf_text = ""
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            pdf_text += page.extract_text() or ""

        if not pdf_text.strip():         # If no text was extracted, fallback to OCR
            uploaded_file.seek(0)
            images = convert_from_bytes(
                uploaded_file.read(),
                poppler_path=r"C:\poppler\poppler-24.08.0\Library\bin"
            )
            for img in images:                                        # If pdf contains img format
                text = pytesseract.image_to_string(img)
                pdf_text += text + "\n"
        st.session_state.pdf_text = pdf_text
        st.success("Text successfully extracted from PDF.")
    except Exception as e:
        st.error(f"Error during PDF processing: {e}")
elif "pdf_text" in st.session_state:
    pdf_text = st.session_state.pdf_text

# Function to call LLM
def get_hr_answer(messages):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {                                  # Instructions for the chatbot
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a friendly HR assistant who answers clearly and politely. Answer employee questions based on typical HR policies like paid leaves, holidays, work-from-home, recruitment, etc."
            }
        ] + messages
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)                    
        response.raise_for_status()
        data = response.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        else:
            return f"⚠️ API responded but no choices found. Response: {data}"
    except requests.exceptions.HTTPError as http_err:
        return f"❌ HTTP error occurred: {http_err} - Response: {response.text}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# To store the chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# User Input questions
user_input = st.chat_input("👤 Your question:")

# Handle user input and model responses
if user_input:
    context = f"Use the HR policy document below to answer:\n---\n{pdf_text[:15000]}\n---\n{user_input}"
    st.session_state.chat_history.append({"role": "user", "content": context})

    with st.spinner("Fetching response from HR database..."):       # Loading
        answer = get_hr_answer(st.session_state.chat_history)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})

# Displaying chat history
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.chat_message("user").markdown(msg["content"].split('---')[-1].strip())  # shows only the question
    else:
        st.chat_message("assistant").markdown(msg["content"])
