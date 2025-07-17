# bt_app.py

import streamlit as st
import time
import json
from datetime import datetime
import ollama  # or OpenAI if you're using their API

# Set your model name
MODEL_NAME = "mistral"  # Change to your preferred model like "llama3", "gemma", etc.

# Load language preference
if "language" not in st.session_state:
    st.session_state["language"] = "en"

# Load login state
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# Shared login password (stored securely in Streamlit secrets)
PASSWORD = st.secrets["login_password"]

# Login function
def login():
    st.title("🔒 BT Login")
    pwd = st.text_input("Enter password", type="password")
    if pwd == PASSWORD:
        st.session_state["logged_in"] = True
        st.experimental_rerun()
    elif pwd:
        st.error("Incorrect password.")

if not st.session_state["logged_in"]:
    login()
    st.stop()

# Language toggle
def toggle_language():
    st.session_state["language"] = "ar" if st.session_state["language"] == "en" else "en"

st.sidebar.button("🌐 Change Language", on_click=toggle_language)

# Language prompts
PROMPTS = {
    "en": "You are a helpful and friendly AI assistant named BT. Reply in English.",
    "ar": "أنت مساعد ذكي وودود اسمه BT. أجب باللغة العربية."
}

# Rate limiting
def is_rate_limited(cooldown=10):
    last_time = st.session_state.get("last_message_time", 0)
    now = time.time()
    if now - last_time < cooldown:
        st.warning(f"⏳ Please wait {int(cooldown - (now - last_time))} seconds.")
        return True
    st.session_state["last_message_time"] = now
    return False

# Save chat history
def save_chat(user, bot, file="chat_history.json"):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "user": user,
        "bot": bot
    }
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = []
    data.append(entry)
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Generate response using Ollama
def get_response(prompt):
    full_prompt = PROMPTS[st.session_state["language"]] + "\n\nUser: " + prompt + "\nBT:"
    response = ollama.chat(model=MODEL_NAME, messages=[
        {"role": "user", "content": full_prompt}
    ])
    return response["message"]["content"]

# UI
st.title("🤖 BT – Your AI Assistant")
st.markdown("Ask me anything! I'm here to help.")

user_input = st.text_input("💬 Your Message")

if st.button("Send") and user_input:
    if is_rate_limited():
        st.stop()

    with st.spinner("BT is thinking..."):
        response = get_response(user_input)
    bt_placeholder = st.empty()
    typed_text = ""
    for char in response:
        typed_text += char
        bt_placeholder.markdown(f"**BT** {typed_text}")
        time.sleep(0.02)
    save_chat(user_input, response)