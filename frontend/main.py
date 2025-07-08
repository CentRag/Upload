import streamlit as st
import requests
from PIL import Image

# --- App Configuration ---
st.set_page_config(page_title="KRCL RuleBot", page_icon="frontend/Konkan_Railway_logo.svg.png")

# --- Load Logo ---
try:
    logo = Image.open("frontend/Konkan_Railway_logo.svg.png")
    st.image(logo, width=50)
except FileNotFoundError:
    st.warning("Konkan Railway logo not found.")

st.title("🚦 KRCL RuleBot")
st.markdown("Ask me about **General & Subsidiary Rules** or **Accident Manual**.")

# --- Backend Config ---
USE_LOCAL = True  # 🔁 Toggle this to True for local testing

BACKEND_URL = (
    "http://127.0.0.1:8000/ask" if USE_LOCAL else "https://upload-rn8u.onrender.com/ask"
)

# --- Session State Initialization ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "input_text" not in st.session_state:
    st.session_state.input_text = ""

# --- Chat Display ---
for chat in st.session_state.chat_history:
    if chat["role"] == "user":
        st.markdown(f"**👤 You:** {chat['content']}")
    else:
        st.markdown(f"**🤖 RuleBot:** {chat['content']}")

# --- Text Input ---
query = st.text_input("Enter your question:", key="input_text")

# --- Ask Button ---
if st.button("Ask") and query:
    st.session_state.chat_history.append({"role": "user", "content": query})

    with st.spinner("Querying the backend..."):
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

    # --- Clear input box after submission ---
    st.session_state.input_text = ""
