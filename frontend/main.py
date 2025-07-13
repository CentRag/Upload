import streamlit as st
import requests
from PIL import Image

# --- App Config ---
st.set_page_config(page_title="KRCL RuleBot", page_icon="frontend/Konkan_Railway_logo.svg.png")

# --- Sidebar: Backend Selector ---
import streamlit as st
import requests
from PIL import Image

# --- App Config ---
st.set_page_config(page_title="KRCL RuleBot", page_icon="frontend/Konkan_Railway_logo.svg.png")

# --- Sidebar Settings ---
st.sidebar.title("⚙️ Settings")
backend_choice = st.sidebar.radio(
    "Choose backend mode:",
    ("Internet (Render)", "Localhost"),
    index=0
)

# Select backend URL
# Select backend URL
BACKEND_URL = (
    "https://upload-ai00.onrender.com/ask"
    if backend_choice == "Internet (Render)"
    else "http://127.0.0.1:8000/ask"
)



# --- Logo ---
try:
    logo = Image.open("frontend/Konkan_Railway_logo.svg.png")
    st.image(logo, width=50)
except FileNotFoundError:
    st.warning("Konkan Railway logo not found.")

# --- Title ---
st.title("KRCL RuleBot")
st.markdown("Ask about **General & Subsidiary Rules** or **Accident Manual**.")

# --- Session State Initialization ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "pending_clear" not in st.session_state:
    st.session_state.pending_clear = False

# --- Clear input if flagged ---
if st.session_state.pending_clear:
    st.session_state.input_text = ""
    st.session_state.pending_clear = False
    st.rerun()

# --- User Input ---
query = st.text_input("Enter your question:", key="input_text")

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
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": "Unexpected response format from backend."
                    })
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

    # Flag to clear input after rerun
    st.session_state.pending_clear = True
    st.rerun()

# --- Show Chat (Newest on Top) ---
for chat in reversed(st.session_state.chat_history):
    if chat["role"] == "user":
        st.markdown(f"**👤 You:** {chat['content']}")
    else:
        st.markdown(f"** RuleBot:** {chat['content']}")
    st.markdown("---")


