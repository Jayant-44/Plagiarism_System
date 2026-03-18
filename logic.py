import os
import re
import pickle
import numpy as np
import shutil
import math
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from googlesearch import search
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

VECTOR_DB_FILE = "vector_db.pkl"
REFERENCE_DIR = "reference_docs"

_vectorizer = None
_matrix = None
_metadata = None

def load_engines():
    global _vectorizer, _matrix, _metadata
    if _vectorizer is None and os.path.exists(VECTOR_DB_FILE):
        print(" [i] Loading Statistical Vector Database...")
        with open(VECTOR_DB_FILE, 'rb') as f:
            data = pickle.load(f)
            _vectorizer = data['vectorizer']
            _matrix = data['matrix']
            _metadata = data['metadata']

def extract_raw_text(file_path):
    text = ""
    ext = file_path.lower().split('.')[-1]
    
    if ext == 'pdf':
        import pdfplumber
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted: 
                        text += extracted + " "
                    else:
                        # --- OCR FALLBACK FOR IMAGES ---
                        try:
                            import pytesseract
                            # Update this path if you installed Tesseract somewhere else!
                            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                            img = page.to_image(resolution=300).original
                            text += pytesseract.image_to_string(img) + " "
                        except Exception as ocr_e: 
                            pass
        except Exception as e: print(f" [!] PDF Error: {e}")
        
    elif ext == 'docx':
        try:
            import docx
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                if para.text.strip(): text += para.text + " "
        except: pass
        
    elif ext == 'txt':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except: pass
        
    return text 
def rebuild_database():
    global _vectorizer, _matrix, _metadata
    print("\n [i] --- BACKGROUND SELF-LEARNING INITIATED ---")
    files = [f for f in os.listdir(REFERENCE_DIR) if f.lower().endswith(('.pdf', '.docx', '.txt'))]
    all_chunks, metadata = [], []
    
    for filename in files:
        path = os.path.join(REFERENCE_DIR, filename)
        text = extract_raw_text(path) 
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        valid = [s.strip() for s in sentences if len(s.split()) > 4]
        all_chunks.extend(valid)
        metadata.extend([{"filename": filename, "text": c} for c in valid])

    if all_chunks:
        _vectorizer = TfidfVectorizer().fit(all_chunks)
        _matrix = _vectorizer.transform(all_chunks)
        _metadata = metadata
        with open(VECTOR_DB_FILE, 'wb') as f:
            pickle.dump({"vectorizer": _vectorizer, "matrix": _matrix, "metadata": _metadata}, f)
        print(" [i] --- SYSTEM LEARNED NEW DOCUMENTS SUCCESSFULLY ---\n")

def extract_text(file_path):
    text = ""
    ext = file_path.lower().split('.')[-1]
    print(f" [i] Extracting Document Text ({ext.upper()})...")
    
    if ext == 'pdf':
        import pdfplumber
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted: text += extracted + "\n\n"
        except Exception as e: print(f" [!] PDF Error: {e}")
    elif ext == 'docx':
        try:
            import docx
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                if para.text.strip(): text += para.text + "\n\n"
        except Exception as e: print(f" [!] DOCX Error: {e}")
    elif ext == 'txt':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e: print(f" [!] TXT Error: {e}")

    # Academic Filter
    biblio_match = re.search(r'\n(?:\d+\.\s*)?(?:References|Bibliography|REFERENCES|BIBLIOGRAPHY)\s*\n', text)
    if biblio_match:
        text = text[:biblio_match.start()]

    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    text = text.replace('\n\n', ' <br><br> ')
    return text.strip()

def calculate_shannon_entropy(words):
    """ Calculates Information Entropy. AI has low entropy (predictable). Humans have high entropy. """
    if not words: return 0
    word_counts = Counter(words)
    total_words = len(words)
    entropy = 0
    for count in word_counts.values():
        p = count / total_words
        entropy -= p * math.log2(p)
    return entropy

def analyze_linguistics(sentences):
    ai_flags, spun_flags = set(), set()
    
    ai_buzzwords = {'delve', 'multifaceted', 'testament', 'crucial', 'vital', 'underscore', 'seamless', 'robust', 'foster', 'aligns', 'comprehensive', 'pivotal', 'intricate', 'meticulous', 'leverage', 'paradigm', 'dynamic', 'tapestry', 'nuanced', 'landscape'}
    ai_transitions = {'furthermore', 'moreover', 'consequently', 'therefore', 'additionally', 'ultimately', 'notably', 'in conclusion', 'in summary'}
    spinbot_buzzwords = {'subsequently', 'henceforth', 'utilize', 'optimal', 'paramount', 'pertaining', 'ameliorate', 'facilitate', 'endeavor', 'procure', 'cognizant'}

    # Document Level Metrics
    all_words = []
    lengths = []
    for s in sentences:
        clean = re.sub(r'<[^>]+>', '', s).strip().lower()
        if not (clean.startswith('"') and clean.endswith('"')):
            w = [x.strip('.,!?"\'') for x in clean.split()]
            all_words.extend(w)
            lengths.append(len(w))
    
    # Mathematical Baselining
    doc_entropy = calculate_shannon_entropy(all_words)
    burstiness = np.var(lengths) / (np.mean(lengths) + 1) if len(lengths) > 2 else 100
    
    # Thresholds: AI is usually below 6.0 Entropy and below 4.5 Burstiness
    is_robotic_doc = doc_entropy < 6.5 and burstiness < 5.0

    for original_s in sentences:
        clean_s = re.sub(r'<[^>]+>', '', original_s).strip().lower()
        if clean_s.startswith('"') and clean_s.endswith('"'): continue
            
        words = [w.strip('.,!?"\'') for w in clean_s.split()]
        if len(words) < 6: continue

        ai_count = sum(1 for w in words if w in ai_buzzwords)
        trans_count = sum(1 for w in words if w in ai_transitions)
        spun_count = sum(1 for w in words if w in spinbot_buzzwords)
        avg_len = sum(len(w) for w in words) / len(words)
        
        # Sentence Level Entropy
        sent_entropy = calculate_shannon_entropy(words)

        is_ai = False
        
        # 1. High Buzzword Density
        if ai_count >= 2: 
            is_ai = True
        # 2. Structural AI (Transitions + Low Entropy)
        elif trans_count >= 1 and sent_entropy < 3.0 and is_robotic_doc:
            is_ai = True
        # 3. Shannon Entropy Check (Highly predictable wording)
        elif sent_entropy < 2.5 and avg_len > 5.0 and is_robotic_doc:
            is_ai = True

        if is_ai:
            ai_flags.add(original_s)
        elif spun_count >= 2 or (spun_count >= 1 and avg_len > 6.0):
            spun_flags.add(original_s)

    return ai_flags, spun_flags

def check_plagiarism(filepath):
    load_engines()
    text = extract_text(filepath)
    if not text: return "No text extracted", [], "Error", 0, "", []
    
    sentences = re.split(r'(?<=[.!?]) +', text.strip())
    valid_sentences = [s for s in sentences if len(re.sub(r'<[^>]+>', '', s).split()) > 5]
    
    plag_flags = {}
    matched_sources = set()

    print(" [i] Running Advanced Shannon Entropy Analysis...")
    ai_flags, spun_flags = analyze_linguistics(valid_sentences)

    print(" [i] Running Local Database Scan...")
    clean_valid_sentences = []
    sentence_map = [] 
    
    for s in valid_sentences:
        clean_s = re.sub(r'<[^>]+>', '', s).strip()
        if not (clean_s.startswith('"') and clean_s.endswith('"')):
            clean_valid_sentences.append(clean_s)
            sentence_map.append(s)

    # Calculate Sentence Rarity using TF-IDF for Smart Web Search
    sentence_rarity = []

    if _vectorizer and _matrix is not None and clean_valid_sentences:
        try:
            query_vectors = _vectorizer.transform(clean_valid_sentences)
            
            # Map rarity (sum of TF-IDF scores) for web search targeting
            for i, vector in enumerate(query_vectors.toarray()):
                sentence_rarity.append((sentence_map[i], np.sum(vector)))

            similarities = cosine_similarity(query_vectors, _matrix)
            for idx, sentence_scores in enumerate(similarities):
                best_match_idx = np.argmax(sentence_scores)
                best_score = sentence_scores[best_match_idx]
                
                original_s = sentence_map[idx]
                if best_score > 0.65 and original_s not in ai_flags and original_s not in spun_flags:
                    src = _metadata[best_match_idx]['filename']
                    plag_flags[original_s] = (src, best_score)
                    matched_sources.add((src, round(best_score * 100)))
        except Exception as e: print(f" [!] Local Plagiarism Error: {e}")
    else:
        # Fallback rarity calculation if DB is empty
        sentence_rarity = [(s, len(s)) for s in sentence_map]

    print(" [i] Running Smart Internet Scan (TF-IDF Targeted)...")
    # Search the 4 most "statistically rare/unique" sentences, not just the longest ones
    top_targets = sorted(sentence_rarity, key=lambda x: x[1], reverse=True)[:4]
    
    for original_s, score in top_targets:
        if original_s in plag_flags or original_s in ai_flags or original_s in spun_flags: continue 
        clean_s = re.sub(r'<[^>]+>', '', original_s).strip()
        
        try:
            # Added User-Agent headers to bypass Google blocks
            results = list(search(f'"{clean_s}"', num_results=1, stop=1, pause=2.0))
            if results:
                display_url = results[0].split("://")[-1][:40] + "..."
                plag_flags[original_s] = (display_url, 0.99)
                matched_sources.add((display_url, 99))
                print(f"      -> Web Match (High Rarity): {display_url}")
        except: pass

    highlighted_html = ""
    pdf_data = []
    for s in sentences:
        clean_s = re.sub(r'<[^>]+>', '', s).strip()
        if len(clean_s.split()) <= 5:
            highlighted_html += s + " "
            pdf_data.append({"text": s + " ", "type": "clean"})
            continue

        if s in ai_flags:
            highlighted_html += f'<span class="highlight-ai" style="color: #a855f7; font-weight: bold;" title="AI Generated">{s}</span> '
            pdf_data.append({"text": s + " ", "type": "ai"})
        elif s in spun_flags:
            highlighted_html += f'<span class="highlight-spun" style="color: #3b82f6; font-weight: bold; text-decoration: underline;" title="Paraphrased/Spinbot">{s}</span> '
            pdf_data.append({"text": s + " ", "type": "spun"})
        elif s in plag_flags:
            source, similarity = plag_flags[s]
            highlighted_html += f'<span class="highlight-plag" style="color: #f59e0b; font-weight: bold;" title="Found in: {source} ({round(similarity * 100)}% Match)">{s}</span> '
            pdf_data.append({"text": s + " ", "type": "plag"})
        else:
            highlighted_html += s + " "
            pdf_data.append({"text": s + " ", "type": "clean"})

    total = max(1, len(valid_sentences))
    ai_score = int(((len(ai_flags) + len(spun_flags)) / total) * 100)
    
    if ai_score > 60: ai_label = "Highly Likely AI"
    elif ai_score > 30: ai_label = "Suspected AI"
    else: ai_label = "Human Driven"

    return text, sorted(list(matched_sources), key=lambda x: x[1], reverse=True), ai_label, ai_score, highlighted_html, pdf_data