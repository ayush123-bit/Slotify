import streamlit as st
import requests

# Set up the page
st.set_page_config(page_title="TailorTalk Booking Assistant", layout="wide")
st.title("TailorTalk Booking Assistant")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I'm your scheduling assistant. How can I help you today?"}]

# Display chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Sidebar with help information
with st.sidebar:
    st.subheader("How to use")
    st.markdown("""
    - **Book appointments**: "Book a meeting tomorrow at 2pm"
    - **Check availability**: "Is Friday at 3pm available?"
    - **General help**: Type "help" for assistance
    """)
    st.markdown("---")
    st.subheader("Common Scenarios")
    st.markdown("""
    - When slots are booked, I'll suggest alternatives
    - I understand time ranges like '3-5pm'
    - Handles relative dates like 'next Tuesday'
    """)

# Handle user input
if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    "https://slotify-zmfm.onrender.com/chat",
                    json={"user_input": prompt},
                    timeout=10
                )
                response.raise_for_status()
                reply = response.json().get("response", "I couldn't process that request.")
                
                # Display assistant response
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                
            except requests.exceptions.RequestException:
                error_msg = "Sorry, I'm having connection issues. Please try again later."
                st.write(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                error_msg = "An unexpected error occurred. Please try again."
                st.write(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
