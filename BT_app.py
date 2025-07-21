# bt_app.py

import streamlit as st
import time
import json
import os
import pdfplumber
from datetime import datetime

import ollama
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.ollama import OllamaEmbeddings
from langchain.vectorstores import FAISS

import speech_recognition as sr
import pyttsx3

# ==== CONFIG ====
MODEL_NAME = "llama3.1:8b"
USER_CREDENTIALS = st.secrets["users"]
HISTORY_FOLDER = "chat_histories"

# ==== SESSION STATE SETUP ====
for key, default in {
    "language": "en",
    "logged_in": False,
    "username": None,
    "chat_history": [],
    "doc_db": None,
    "voice_input": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ==== TTS INIT ====
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150)

def speak_text(text):
    try:
        tts_engine.say(text)
        tts_engine.runAndWait()
    except:
        st.warning("🔇 Unable to play voice output on this device.")

# ==== STT ====
def recognize_speech_from_mic():
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            st.info("🎤 Listening... Speak now.")
            audio = r.listen(source, phrase_time_limit=5)
        transcription = r.recognize_google(audio)
        st.success(f"✅ You said: {transcription}")
        return transcription
    except sr.UnknownValueError:
        st.error("🤔 Sorry, I couldn't understand.")
    except sr.RequestError:
        st.error("🌐 Network issue during speech recognition.")
    except:
        st.error("🎤 Microphone not accessible.")
    return None

# ==== HISTORY FILE HANDLERS ====
def get_user_history_path(username):
    os.makedirs(HISTORY_FOLDER, exist_ok=True)
    return os.path.join(HISTORY_FOLDER, f"{username}.json")

def load_user_history(username):
    path = get_user_history_path(username)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_user_history(username, history):
    path = get_user_history_path(username)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

# ==== DOC PROCESS ====
def process_uploaded_file(uploaded_file):
    text = ""
    if uploaded_file.name.endswith(".pdf"):
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    elif uploaded_file.name.endswith(".txt"):
        text = uploaded_file.read().decode("utf-8")
    else:
        st.error("❌ Unsupported file type.")
        return None

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    docs = splitter.create_documents([text])
    embeddings = OllamaEmbeddings(model=MODEL_NAME)
    db = FAISS.from_documents(docs, embeddings)
    return db

# ==== LOGIN ====
def login():
    st.title("🔒 BT Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["chat_history"] = load_user_history(username)
            st.success(f"Welcome {username}!")
            st.rerun()
        else:
            st.error("❌ Invalid login.")

if not st.session_state["logged_in"]:
    login()
    st.stop()

# ==== LANGUAGE TOGGLE ====
def toggle_language():
    st.session_state["language"] = "ar" if st.session_state["language"] == "en" else "en"

st.sidebar.button("🌐 Change Language", on_click=toggle_language)

# ==== DOCUMENT UPLOAD ====
st.sidebar.subheader("📄 Upload Document (PDF or TXT)")
uploaded_file = st.sidebar.file_uploader("Choose a file", type=["pdf", "txt"])
if uploaded_file:
    with st.spinner("Processing document..."):
        st.session_state["doc_db"] = process_uploaded_file(uploaded_file)
    st.sidebar.success("✅ Document ready!")

if st.sidebar.button("❌ Remove Uploaded Document"):
    st.session_state["doc_db"] = None
    st.sidebar.success("Document removed.")

# ==== VOICE INPUT ====
if st.sidebar.button("🎤 Speak to BT"):
    voice_input = recognize_speech_from_mic()
    if voice_input:
        st.session_state["voice_input"] = voice_input

# ==== PROMPTS ====
PROMPTS = {
    "en": "You are a helpful and friendly AI assistant named BT. Reply in English.",
    "ar": "أنت مساعد ذكي وودود اسمه BT. أجب باللغة العربية."
}

# ==== RATE LIMITING ====
def is_rate_limited(cooldown=10):
    last_time = st.session_state.get("last_message_time", 0)
    now = time.time()
    if now - last_time < cooldown:
        st.warning(f"⏳ Please wait {int(cooldown - (now - last_time))} seconds.")
        return True
    st.session_state["last_message_time"] = now
    return False

# ==== RESPONSE (with RAG) ====
def get_response(prompt):
    if st.session_state["doc_db"]:
        docs = st.session_state["doc_db"].similarity_search(prompt, k=3)
        context = "\n\n".join([doc.page_content for doc in docs])
        full_prompt = f"{PROMPTS[st.session_state['language']]}\n\nContext:\n{context}\n\nUser: {prompt}\nBT:"
    else:
        full_prompt = f"{PROMPTS[st.session_state['language']]}\n\nUser: {prompt}\nBT:"

    response = ollama.chat(model=MODEL_NAME, messages=[
        {"role": "user", "content": full_prompt}
    ])
    return response["message"]["content"]

# ==== MAIN UI ====
st.title("🤖 BT – Your AI Assistant")
st.markdown(f"Welcome **{st.session_state['username']}**!")

# Show history
for entry in st.session_state["chat_history"]:
    st.markdown(f"**You:** {entry['user']}")
    st.markdown(f"**BT:** {entry['bot']}")

# Get final user input (text box OR voice)
default_input = st.session_state.pop("voice_input", "")
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("Your Message", value=default_input, placeholder="Type or use voice")
    submitted = st.form_submit_button("Send")

# On submit
if submitted and user_input:
    if is_rate_limited():
        st.stop()

    with st.spinner("BT is thinking..."):
        response = get_response(user_input)

    # Typing animation
    bt_placeholder = st.empty()
    typed = ""
    for ch in response:
        typed += ch
        bt_placeholder.markdown(f"**BT:** {typed}")
        time.sleep(0.02)

    # Save and speak
    st.session_state["chat_history"].append({"user": user_input, "bot": response})
    save_user_history(st.session_state["username"], st.session_state["chat_history"])
    speak_text(response)
    st.rerun()