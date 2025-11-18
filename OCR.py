import pdfplumber
import pytesseract
from PIL import Image
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# For Windows users (uncomment if needed)
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# --- MAIN FUNCTIONS ---

def extract_text_from_pdf(path):
    text_output = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()

            if text and text.strip():
                text_output.append(text)
            else:
                # OCR fallback
                pil_img = page.to_image(resolution=300).original
                ocr_text = pytesseract.image_to_string(pil_img)
                text_output.append(ocr_text)

    return "\n".join(text_output)

def clean_text(text):
    return " ".join(text.split())

def chunk_text(text, chunk_size=500):
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_chunks(chunks):
    return model.encode(chunks, convert_to_numpy=True)

def build_faiss_index(embeddings):
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index

# --- RUN PIPELINE ---

pdf_path = "your_document.pdf"

raw_text = extract_text_from_pdf(pdf_path)
cleaned_text = clean_text(raw_text)
chunks = chunk_text(cleaned_text, chunk_size=300)

embeddings = embed_chunks(chunks)
index = build_faiss_index(embeddings)

print("Done! Embeddings generated.")
print("Chunks:", len(chunks))
print("Embedding shape:", embeddings.shape)
