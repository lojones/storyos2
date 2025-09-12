import streamlit as st
import openai
import os
from dotenv import load_dotenv

st.title("Chat with Grok4")

load_dotenv()
api_key = os.getenv("XAI_API_KEY")

if not api_key:
    st.error("API key not found in .env file. Please set XAI_API_KEY in your .env file.")
else:
    client = openai.OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("Say something"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Prepare messages for API
        messages = st.session_state.messages.copy()

        # Get response from Grok
        response = client.chat.completions.create(
            model="grok-3-mini",
            messages=messages
        )
        assistant_response = response.choices[0].message.content

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(assistant_response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
