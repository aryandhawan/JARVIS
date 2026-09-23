"""
JARVIS — Streamlit frontend.

MVP scope: chat with the judgement agent, and a one-click "Routine Check"
action for the read-and-report flow that's already fully working. The
"fire up the arc" trigger is included since it's part of the same chat
flow, but the registry-matching backend behind it is still being fixed —
this UI doesn't need to know that; it just sends messages to /chat.
"""

import uuid

import requests
import streamlit as st

BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="JARVIS", page_icon="🔷", layout="centered")

# ---------- theme ----------

st.markdown(
    """
    <style>
    :root {
        --jarvis-blue: #4FD8EB;
        --jarvis-blue-dim: #2A7A85;
        --bg-dark: #0B0F14;
        --panel-dark: #10161D;
    }

    .stApp {
        background: radial-gradient(circle at 50% -10%, #0F1A22 0%, var(--bg-dark) 60%);
    }

    h1, h2, h3 {
        color: var(--jarvis-blue) !important;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        font-weight: 600 !important;
    }

    [data-testid="stChatMessage"] {
        background: var(--panel-dark);
        border: 1px solid rgba(79, 216, 235, 0.15);
        border-radius: 10px;
    }

    .stButton > button {
        background: transparent;
        border: 1px solid var(--jarvis-blue-dim);
        color: var(--jarvis-blue);
        border-radius: 6px;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        border-color: var(--jarvis-blue);
        box-shadow: 0 0 12px rgba(79, 216, 235, 0.35);
        color: var(--jarvis-blue);
    }

    .status-dot {
        height: 9px;
        width: 9px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
    }
    .status-online { background: var(--jarvis-blue); box-shadow: 0 0 8px var(--jarvis-blue); }
    .status-offline { background: #E5484D; box-shadow: 0 0 8px #E5484D; }

    [data-testid="stSidebar"] {
        background: var(--panel-dark);
        border-right: 1px solid rgba(79, 216, 235, 0.1);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- session state ----------

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())
if "display_history" not in st.session_state:
    st.session_state.display_history = []


def check_backend_online() -> bool:
    try:
        requests.get(f"{BACKEND_URL}/docs", timeout=2)
        return True
    except requests.exceptions.RequestException:
        return False


def send_message(message: str) -> dict:
    response = requests.post(
        f"{BACKEND_URL}/chat",
        json={"conversation_id": st.session_state.conversation_id, "user_message": message},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


# ---------- sidebar ----------

with st.sidebar:
    st.markdown("### System")
    online = check_backend_online()
    status_class = "status-online" if online else "status-offline"
    status_text = "ONLINE" if online else "OFFLINE"
    st.markdown(
        f'<span class="status-dot {status_class}"></span>**{status_text}**',
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("### Quick Actions")
    if st.button("🔍 Run Routine Check", use_container_width=True):
        st.session_state.pending_message = "do a routine check"

    st.divider()

    if st.button("🗑️ New Conversation", use_container_width=True):
        st.session_state.conversation_id = str(uuid.uuid4())
        st.session_state.display_history = []
        st.rerun()

    st.caption(f"Session: `{st.session_state.conversation_id[:8]}`")

# ---------- header ----------

st.markdown("# 🔷 J.A.R.V.I.S.")
st.caption("Personal infrastructure maintenance system")

# ---------- chat history ----------

for entry in st.session_state.display_history:
    avatar = "🔷" if entry["role"] == "assistant" else None
    with st.chat_message(entry["role"], avatar=avatar):
        st.markdown(entry["content"])

# ---------- handle a pending quick-action message ----------

if "pending_message" in st.session_state:
    pending = st.session_state.pop("pending_message")
    st.session_state.display_history.append({"role": "user", "content": pending})
    with st.chat_message("user"):
        st.markdown(pending)
    with st.chat_message("assistant", avatar="🔷"):
        with st.spinner("Investigating..."):
            try:
                data = send_message(pending)
                reply = data.get("message") or data.get("result") or data.get("error", "No response.")
            except requests.exceptions.RequestException as e:
                reply = f"Connection error: {e}"
        st.markdown(reply)
    st.session_state.display_history.append({"role": "assistant", "content": reply})

# ---------- chat input ----------

user_input = st.chat_input("Talk to JARVIS, or say 'fire up the arc' to act on a decision...")

if user_input:
    st.session_state.display_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🔷"):
        with st.spinner("Thinking..."):
            try:
                data = send_message(user_input)
                reply = data.get("message") or data.get("result") or data.get("error", "No response.")
            except requests.exceptions.RequestException as e:
                reply = f"Connection error: {e}"
        st.markdown(reply)

    st.session_state.display_history.append({"role": "assistant", "content": reply})