import streamlit as st
import requests

# Set up the page
st.set_page_config(page_title="TailorTalk Booking Assistant", layout="wide")
st.title("TailorTalk Booking Assistant")

# Initialize session state for messages
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add initial greeting
    st.session_state.messages.append(("Assistant", "Hello! I'm your scheduling assistant. How can I help you today?"))

# Chat container
chat_container = st.container()

# Display conversation history at the top
with chat_container:
    for sender, message in st.session_state.messages:
        if sender == "Assistant":
            with st.chat_message("Assistant"):
                st.write(message)
        else:
            with st.chat_message("User"):
                st.write(message)

# Input area at the bottom
with st.form("chat_form", clear_on_submit=True):
    col1, col2 = st.columns([6, 1])
    with col1:
        user_input = st.text_input(
            "Type your message...",
            key="user_input",
            label_visibility="collapsed",
            placeholder="e.g. 'Book a meeting tomorrow at 2pm' or 'Check my availability on Friday'"
        )
    with col2:
        submitted = st.form_submit_button("Send")

# Handle form submission
if submitted and user_input:
    # Add user message to chat
    st.session_state.messages.append(("User", user_input))
    
    # Get bot response
    try:
        response = requests.post(
            "https://slotify-zmfm.onrender.com/chat",
            json={"user_input": user_input},
            timeout=10  # Add timeout for better UX
        )
        response.raise_for_status()  # Raise exception for bad status codes
        response_data = response.json()
        reply = response_data.get("response", "I couldn't process that request. Please try again.")
    except requests.exceptions.RequestException as e:
        reply = f"Sorry, I'm having trouble connecting to the service. Please try again later."
    except Exception as e:
        reply = "An unexpected error occurred. Please try again."

    # Add assistant response to chat
    st.session_state.messages.append(("Assistant", reply))
    
    # Rerun to update the chat display
    st.rerun()

# Help section in sidebar
with st.sidebar:
    st.subheader("How to use")
    st.markdown("""
    - **Book appointments**: "Book a meeting tomorrow at 2pm"
    - **Check availability**: "Is Friday at 3pm available?"
    - **General help**: Type "help" for assistance
    """)
    st.markdown("---")
    st.markdown("Examples:")
    st.markdown("- *Team meeting next Tuesday at 11am*")
    st.markdown("- *Doctor appointment this Friday afternoon*")
    st.markdown("- *What's my schedule looking like tomorrow?*")
