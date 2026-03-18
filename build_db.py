import os
import pickle
import pdfplumber
import re
from sklearn.feature_extraction.text import TfidfVectorizer

REFERENCE_DIR = "reference_docs"
VECTOR_DB_FILE = "vector_db.pkl"

def extract_chunks(filepath):
    try:
        text = ""
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t: text += t + " "
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        return [s.strip() for s in sentences if len(s.split()) > 4]
    except Exception as e:
        print(f" [!] Error reading {os.path.basename(filepath)}: {e}")
        return []

def build_database():
    print("\n" + "="*50)
    print("BUILDING STATISTICAL VECTOR DATABASE (CRASH-FREE)")
    print("="*50)
    
    if not os.path.exists(REFERENCE_DIR):
        os.makedirs(REFERENCE_DIR)
        print(f" [!] Created folder '{REFERENCE_DIR}'. Put reference PDFs here.")
        return

    files = [f for f in os.listdir(REFERENCE_DIR) if f.lower().endswith('.pdf')]
    if not files:
        print(" [x] No reference PDFs found.")
        return

    all_chunks = []
    metadata = []
    
    for filename in files:
        path = os.path.join(REFERENCE_DIR, filename)
        print(f" [>] Processing: {filename}...")
        chunks = extract_chunks(path)
        for c in chunks:
            all_chunks.append(c)
            metadata.append({"filename": filename, "text": c})

    if not all_chunks:
        print(" [x] No text extracted. Aborting.")
        return

    print(" [i] Training TF-IDF Vectorizer...")
    vectorizer = TfidfVectorizer().fit(all_chunks)
    
    print(" [i] Generating Dense Vector Matrix...")
    vector_matrix = vectorizer.transform(all_chunks)

    print(" [i] Saving Database to disk...")
    db_data = {
        "vectorizer": vectorizer,
        "matrix": vector_matrix,
        "metadata": metadata
    }
    
    with open(VECTOR_DB_FILE, 'wb') as f:
        pickle.dump(db_data, f)
    
    print(f" SUCCESS! Database built with {len(all_chunks)} vectors.")

if __name__ == "__main__":
    build_database()