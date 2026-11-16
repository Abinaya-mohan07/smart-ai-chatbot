"""
app.py
------
The Streamlit web interface.  Run it with:   streamlit run app.py

Streamlit re-runs this whole file after every click or message, so anything
we want to REMEMBER between runs is saved in `st.session_state`.
"""

import streamlit as st

import config
from chatbot import ChatbotError, SmartChatbot

# ---------------------------------------------------------------------------
# Page setup + a little custom styling
# ---------------------------------------------------------------------------
st.set_page_config(page_title=config.APP_TITLE, page_icon="🤖", layout="centered")

st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem; font-weight: 800; margin-bottom: 0;
        background: linear-gradient(90deg, #4f46e5, #06b6d4);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .sub-title { color: #6b7280; margin-top: 0.2rem; margin-bottom: 1rem; }
    [data-testid="stChatMessage"] { border-radius: 12px; padding: 0.6rem 0.8rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Session state (the app's memory between reruns)
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    # Messages shown on screen: {"role": "user"/"assistant", "content": "...", "is_error": bool}
    st.session_state.messages = []

if "chatbot" not in st.session_state:
    st.session_state.chatbot = None

startup_error = None
if st.session_state.chatbot is None:
    try:
        st.session_state.chatbot = SmartChatbot()
    except ChatbotError as error:
        startup_error = error.user_message

chatbot = st.session_state.chatbot

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    st.write(f"**Model:** `{config.MODEL_NAME}`")

    use_summary = st.toggle(
        "Summarize older messages (advanced)",
        value=config.ENABLE_SUMMARY,
        help="When on, messages removed from the context window are compressed "
        "into a short summary by the AI. Uses one extra API call when needed.",
    )
    if chatbot:
        chatbot.enable_summary = use_summary

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        if chatbot:
            chatbot.clear()
        st.rerun()

    st.divider()
    st.subheader("🧠 Memory status")
    if chatbot:
        stats = chatbot.get_stats()
        st.write(
            f"Messages in context: **{stats['messages_in_context']}** "
            f"/ {stats['max_context_messages']}"
        )
        st.write(f"Older messages removed: **{stats['messages_removed']}**")
        if stats["key_facts"]:
            st.write("Remembered facts:")
            for fact in stats["key_facts"]:
                st.caption(f"• {fact}")
        if stats["has_summary"]:
            st.caption("📝 A summary of older messages is active.")
    else:
        st.caption("Chatbot not started.")

# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------
st.markdown(f'<p class="main-title">🤖 {config.APP_TITLE}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-title">{config.APP_SUBTITLE}</p>', unsafe_allow_html=True)

if startup_error:
    st.error(startup_error)
    st.info("Fix the problem, then stop (Ctrl+C) and run `streamlit run app.py` again.")

if not st.session_state.messages and not startup_error:
    st.info("👋 Say hello! Try: *My name is Abinaya.* then later ask *What is my name?*")

# Show the conversation history
for message in st.session_state.messages:
    if message.get("is_error"):
        with st.chat_message("assistant", avatar="⚠️"):
            st.error(message["content"])
    else:
        with st.chat_message(message["role"], avatar="🧑" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])

# Chat input box (press Enter or click the arrow button to send)
prompt = st.chat_input("Type your message here...", disabled=chatbot is None)

if prompt and chatbot is not None:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            try:
                reply = chatbot.send_message(prompt)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except ChatbotError as error:
                st.session_state.messages.append(
                    {"role": "assistant", "content": error.user_message, "is_error": True}
                )
    st.rerun()  # redraw the page so the sidebar status is up to date
