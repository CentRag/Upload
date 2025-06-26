# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate
from langchain_cohere import CohereEmbeddings
from dotenv import load_dotenv
import os
import diskcache as dc
import hashlib
import traceback

# Load environment variables
load_dotenv()

# Validate API keys
groq_api_key = os.getenv("GROQ_API_KEY")
cohere_api_key = os.getenv("COHERE_API_KEY")
if not groq_api_key or not cohere_api_key:
    raise ValueError("Missing GROQ_API_KEY or COHERE_API_KEY in environment.")

# Embeddings
embeddings = CohereEmbeddings(
    model="embed-english-light-v3.0",
    cohere_api_key=cohere_api_key,
    user_agent="krcl-rulebot"
)

# Load FAISS DBs
db1 = FAISS.load_local("faiss_krcl_cohere", embeddings, allow_dangerous_deserialization=True)
db2 = FAISS.load_local("faiss_manual_cohere", embeddings, allow_dangerous_deserialization=True)
db1.merge_from(db2)

# Retriever
retriever = db1.as_retriever(search_kwargs={"k": 6})

# Prompt
prompt = ChatPromptTemplate.from_template("""
You are a highly knowledgeable assistant specializing in the Konkan Railway's General & Subsidiary Rules (G&SR) and Accident Manual.

Your task is to answer user queries using **only the information in the retrieved documents**. You must not fabricate or assume any rules that are not explicitly present in the context.

However, you should:
- Elaborate on the meaning, intent, and operational implications of the rules **as stated**.
- Clarify railway-specific terms, procedures, and abbreviations.
- Break down complex information into clear, step-by-step explanations.
- You may paraphrase or simplify language, but only if the original meaning is preserved.

---

### Output Format:

**Answer:**
- Begin with a short summary sentence.
- Provide a detailed explanation or procedure using bullet points or numbered steps.
- Define any technical railway terms encountered in the rule text.
- Use plain, readable language without losing accuracy.

**References:**
- List the exact rules, clauses, or sections used (e.g., **S.R.2.4.1**, **G.R.1.2**, **2.31**).
- For each rule referenced, **include a brief explanation or summary of what that rule states** (based on retrieved documents).
- If no rule is relevant, write: **"No specific rules found based on current understanding."**

**Note:**
If the context does not contain sufficient information to answer the question, clearly state:  
**"I don’t know based on the available documents."**

---

### Question:
{input}

---

### Retrieved Documents:
{context}

---

### Your Answer:
Answer:
""")


# LLM
llm = ChatGroq(
    groq_api_key=groq_api_key,
    model_name="llama3-8b-8192"
)

# Chain
document_chain = create_stuff_documents_chain(llm, prompt)
retrieval_chain = create_retrieval_chain(retriever, document_chain)

# FastAPI app
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Input schema
class Query(BaseModel):
    input: str

# Initialize cache
cache = dc.Cache("./rulebot_cache")

def hash_query(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

@app.get("/")
def root():
    return {"message": "KRCL RuleBot backend is live with caching!"}

@app.post("/ask")
async def ask(query: Query):
    question = query.input.strip()
    key = hash_query(question)

    if key in cache:
        return {"answer": cache[key]}

    try:
        result = retrieval_chain.invoke({"input": question})
        answer = result.get("answer", "I don’t know based on the available documents.")
        cache[key] = answer
        return {"answer": answer}
    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}
