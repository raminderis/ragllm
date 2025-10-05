import streamlit as st
# from streamlit.runtime.scriptrunner.script_run_context import get_script_run_ctx

import uuid

def get_session_id():
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id




def write_message(role, avatar, content, save = True):
    """
    This is a helper function that saves a message to the
     session state and then writes a message to the UI
    """
    # Append to session state
    if save:
        st.session_state.messages.append({"role": role, "avatar": avatar, "content": content})

    # Write to UI
    with st.chat_message(role, avatar=avatar):
        st.markdown(content)

# def get_session_id():
#     return get_script_run_ctx().session_id
