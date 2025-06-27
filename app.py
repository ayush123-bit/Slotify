import streamlit as st
import requests

st.set_page_config(page_title="TailorTalk Bot")
st.title("🧵 TailorTalk Booking Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Use a form so enter key doesn't re-submit automatically
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("Your message", key="user_input_form")
    submitted = st.form_submit_button("Send")

if submitted and user_input:
    st.session_state.messages.append(("🧑 You", user_input))

    try:
        res = requests.post("http://localhost:8000/chat", json={"user_input": user_input})
        response_data = res.json()
        reply = response_data.get("response", "⚠️ No 'response' field.")
    except Exception as e:
        reply = f"❌ Error: {e}"

    st.session_state.messages.append(("🤖 Bot", reply))

# Display conversation history
for sender, msg in st.session_state.messages:
    st.markdown(f"**{sender}:** {msg}")
