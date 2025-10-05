import streamlit as st
from utils import write_message
from agent import generate_response

# AVATARS = {
#     "user": "🧑‍💻",
#     "assistant": "🕸️",
#     "network_ai": "📡"
# }


# Page Config
st.set_page_config("KnowledgeGraph AI Agent", page_icon=":spider_web:")
st.title("🕸️ LLM-Augmented Knowledge Graphs")
st.caption("A RAG layer build for telecom intelligence, root cause analysis, and topology-aware reasoning.")

# Set up Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "avatar":"🕸️", "content": "Hello. I am here to help you find network related insights!"},
    ]

# Submit handler
def handle_submit(message):
    """
    Submit handler:

    You will modify this method to talk with an LLM and provide
    context using data from Neo4j.
    """

    # Handle the response
    with st.spinner('Thinking...'):
        # # TODO: Replace this with a call to your LLM
        response = generate_response(message)
        # from time import sleep
        # sleep(1)
        write_message('assistant', '🕸️', response)


# Display messages in Session State
for message in st.session_state.messages:
    write_message(message['role'], message['avatar'], message['content'], save=False)

# Handle any user input
if prompt := st.chat_input("What is up?"):
    # Display user message in chat message container
    write_message('user', '🧑‍💻',prompt)

    # Generate a response
    handle_submit(prompt)
    
    # loop.run_until_complete(handle_submit(prompt))

    # asyncio.run(handle_submit(prompt))
