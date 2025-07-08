import streamlit as st
import requests
from PIL import Image

# --- App Config ---
st.set_page_config(page_title="KRCL RuleBot", page_icon="frontend/Konkan_Railway_logo.svg.png")

# --- Sidebar: Backend Selector ---
st.sidebar.title("⚙️ Settings")
backend_choice = st.sidebar.radio(
    "Choose backend mode:",
    ("Internet (Render)", "Localhost"),
    index=0
)

# Set backend URL based on user selection
BACKEND_URL = (
    "https://upload-rn8u.onrender.com/ask" if backend_choice == "Internet (Render)" else "http://127.0.0.1:8000/ask"
)

# --- Logo ---
try:
    logo = Image.open("frontend/Konkan_Railway_logo.svg.png")
    st.image(logo, width=50)
except FileNotFoundError:
    st.warning("Konkan Railway logo not found.")

st.title("🚦 KRCL RuleBot")
st.markdown("Ask me about **General & Subsidiary Rules** or **Accident Manual**.")

# --- Session State Init ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pending_clear" not in st.session_state:
    st.session_state.pending_clear = False

# --- Input clearing logic ---
if st.session_state.pending_clear:
    st.session_state.input_text = ""
    st.session_state.pending_clear = False
    st.rerun()

# --- Text Input ---
query = st.text_input("Enter your question:", key="input_text")

# --- Show Chat History ---
for chat in st.session_state.chat_history:
    if chat["role"] == "user":
        st.markdown(f"**👤 You:** {chat['content']}")
    else:
        st.markdown(f"**🤖 RuleBot:** {chat['content']}")

# --- Ask Button ---
if st.button("Ask") and query:
    st.session_state.chat_history.append({"role": "user", "content": query})

    with st.spinner("Querying backend..."):
        try:
            response = requests.post(BACKEND_URL, json={"input": query})
            if response.status_code == 200:
                data = response.json()
                if "answer" in data:
                    answer = data["answer"]
                    if data.get("action"):
                        answer += f"\n\n**Used Tool:** {data['action']}"
                    if data.get("observation"):
                        answer += f"\n\n**Retrieved:**\n{data['observation']}"
                    st.session_state.chat_history.append({"role": "assistant", "content": answer})
                elif "error" in data:
                    st.session_state.chat_history.append({"role": "assistant", "content": f"Error: {data['error']}"})
                else:
                    st.session_state.chat_history.append({"role": "assistant", "content": "Unexpected response format."})
            else:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"Backend returned status {response.status_code}: {response.text}"
                })
        except Exception as e:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"Request failed: {str(e)}"
            })

    st.session_state.pending_clear = True
    st.rerun()

