import os
import re
import pickle
import numpy as np
import shutil
import math
import json
import concurrent.futures # <-- IMPORTED FOR SPEED (Parallel Processing)
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from googlesearch import search
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

VECTOR_DB_FILE = "vector_db.pkl"
REFERENCE_DIR = "reference_docs"
LEARNED_LEXICON_FILE = "learned_lexicon.json"

_vectorizer = None
_matrix = None
_metadata = None

STOPWORDS = {
    'is', 'am', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 
    'will', 'would', 'shall', 'should', 'can', 'could', 'may', 'might', 'must', 'the', 'a', 'an', 'and', 
    'or', 'but', 'if', 'because', 'as', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 
    'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 
    'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 
    'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 
    'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'now', 'it', 'they', 
    'he', 'she', 'we', 'i', 'you', 'me', 'him', 'her', 'us', 'them', 'this', 'that', 'these', 'those'
}

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
                        try:
                            import pytesseract
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

    biblio_match = re.search(r'\n(?:\d+\.\s*)?(?:References|Bibliography|REFERENCES|BIBLIOGRAPHY)\s*\n', text)
    if biblio_match:
        text = text[:biblio_match.start()]

    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    text = text.replace('\n\n', ' <br><br> ')
    return text.strip()

def calculate_shannon_entropy(words):
    meaningful_words = [w for w in words if w not in STOPWORDS and len(w) > 2]
    if not meaningful_words: return 10.0 
    
    word_counts = Counter(meaningful_words)
    total_words = len(meaningful_words)
    entropy = 0
    for count in word_counts.values():
        p = count / total_words
        entropy -= p * math.log2(p)
    return entropy

def analyze_linguistics(sentences):
    ai_flags, spun_flags = set(), set()
    
    ai_buzzwords = {
        'delve', 'multifaceted', 'testament', 'crucial', 'vital', 'underscore', 
        'seamless', 'robust', 'foster', 'aligns', 'comprehensive', 'pivotal', 
        'intricate', 'meticulous', 'leverage', 'paradigm', 'dynamic', 'tapestry', 
        'nuanced', 'landscape', 'navigating', 'realm', 'beacon', 'embark', 
        'catalyst', 'intertwined', 'symphony', 'myriad', 'demystify', 'unveil',
        'holistic', 'iterative', 'bespoke', 'overarching', 'encapsulate', 
        'illuminating', 'inherent', 'profound', 'compelling', 'intrinsic', 
        'resonance', 'synergy', 'ubiquitous', 'unprecedented', 'burgeoning', 
        'intersection', 'nexus', 'indispensable', 'quintessential', 'transformative',
        'cornerstone', 'framework', 'intricacies', 'paramount', 'culmination',
        'imperative', 'elevate', 'curated', 'hallmark', 'vanguard', 'ecosystem',
        'trajectory', 'fabric', 'unwavering', 'harmonious', 'empower'
    }
    
    ai_transitions = {
        'furthermore', 'moreover', 'consequently', 'therefore', 'additionally', 
        'ultimately', 'notably', 'in conclusion', 'in summary', 'important to note',
        'worth noting', 'to summarize', 'by and large', 'in essence', 'it is crucial',
        'it is imperative', 'delving deeper', 'moving forward', 'as we navigate', 
        'inevitably', 'to that end', 'in this context', 'all in all', 'largely', 
        'it is worth mentioning', 'broadly speaking', 'with this in mind', 
        'it goes without saying', 'at its core', 'first and foremost', 'as a result',
        'to put it simply', 'in the realm of', 'from a broader perspective',
        'as previously stated', 'to reiterate'
    }
    
    spinbot_buzzwords = {
        'subsequently', 'henceforth', 'utilize', 'optimal', 'paramount', 
        'pertaining', 'ameliorate', 'facilitate', 'endeavor', 'procure', 
        'cognizant', 'ascertain', 'elucidate', 'plethora', 'albeit', 
        'heretofore', 'thusly', 'commence', 'terminate', 'peruse', 
        'instantiate', 'methodology', 'aforementioned', 'thereby', 
        'wherein', 'notwithstanding', 'veritable', 'proficient', 
        'apprehend', 'concoct', 'fabricate', 'substantiate', 'apprise',
        'behoove', 'wherewithal', 'insofar', 'purview'
    }

    learned_words = set()
    if os.path.exists(LEARNED_LEXICON_FILE):
        try:
            with open(LEARNED_LEXICON_FILE, 'r') as f:
                learned_words = set(json.load(f))
                ai_buzzwords.update(learned_words)
        except: pass
        
    new_words_learned = False

    all_words = []
    lengths = []
    for s in sentences:
        clean = re.sub(r'<[^>]+>', '', s).strip().lower()
        if not (clean.startswith('"') and clean.endswith('"')):
            w = [x.strip('.,!?"\'') for x in clean.split()]
            all_words.extend(w)
            if len(w) > 3:
                lengths.append(len(w))
    
    burstiness = np.var(lengths) / (np.mean(lengths) + 1) if len(lengths) > 2 else 100
    is_robotic_doc = burstiness < 7.0 

    for original_s in sentences:
        clean_s = re.sub(r'<[^>]+>', '', original_s).strip().lower()
        if clean_s.startswith('"') and clean_s.endswith('"'): continue
            
        words = [w.strip('.,!?"\'') for w in clean_s.split()]
        if len(words) < 5: continue

        ai_count = sum(1 for w in words if w in ai_buzzwords)
        trans_count = sum(1 for t in ai_transitions if t in clean_s)
        spun_count = sum(1 for w in words if w in spinbot_buzzwords)
        avg_len = sum(len(w) for w in words) / len(words)
        
        sent_entropy = calculate_shannon_entropy(words)
        is_ai = False
        
        if ai_count >= 3: 
            is_ai = True
        elif trans_count >= 1 and sent_entropy < 2.5 and is_robotic_doc:
            is_ai = True
        elif sent_entropy < 2.2 and avg_len > 5.5:
            is_ai = True
        elif len(words) > 18 and sent_entropy < 3.0 and burstiness < 7.0:
             is_ai = True

        if is_ai:
            ai_flags.add(original_s)
            
            for w in words:
                if len(w) > 9 and w not in ai_buzzwords and w not in spinbot_buzzwords and w not in STOPWORDS:
                    learned_words.add(w)
                    ai_buzzwords.add(w)
                    new_words_learned = True
                    
        elif spun_count >= 2 or (spun_count >= 1 and avg_len > 6.0):
            spun_flags.add(original_s)

    if new_words_learned:
        try:
            with open(LEARNED_LEXICON_FILE, 'w') as f:
                json.dump(list(learned_words), f)
        except: pass

    return ai_flags, spun_flags

# --- SPEED FIX: Helper function for parallel internet searching ---
def fetch_web_match(target_data, plag_flags):
    original_s, score = target_data
    if original_s in plag_flags: return None
    
    clean_s = re.sub(r'<[^>]+>', '', original_s).strip()
    try:
        # Reduced 'pause' from 2.0 to 0.5 to stop artificial blocking
        results = list(search(f'"{clean_s}"', num_results=1, stop=1, pause=0.5))
        if results:
            display_url = results[0].split("://")[-1][:40] + "..."
            return (original_s, display_url, clean_s)
    except: pass
    return None

def check_plagiarism(filepath):
    load_engines()
    text = extract_text(filepath)
    if not text: return "No text extracted", [], 0, "Error", 0, "", []
    
    total_words_in_doc = max(1, len(text.split()))
    
    sentences = re.split(r'(?<=[.!?]) +', text.strip())
    valid_sentences = [s for s in sentences if len(re.sub(r'<[^>]+>', '', s).split()) > 5]
    
    plag_flags = {}
    source_word_counts = {} 

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

    sentence_rarity = []

    if _vectorizer and _matrix is not None and clean_valid_sentences:
        try:
            query_vectors = _vectorizer.transform(clean_valid_sentences)
            for i, vector in enumerate(query_vectors.toarray()):
                sentence_rarity.append((sentence_map[i], np.sum(vector)))

            similarities = cosine_similarity(query_vectors, _matrix)
            for idx, sentence_scores in enumerate(similarities):
                best_match_idx = np.argmax(sentence_scores)
                best_score = sentence_scores[best_match_idx]
                
                original_s = sentence_map[idx]
                
                if best_score > 0.60:
                    src = _metadata[best_match_idx]['filename']
                    plag_flags[original_s] = (src, best_score)
                    
                    word_count = len(re.sub(r'<[^>]+>', '', original_s).strip().split())
                    source_word_counts[src] = source_word_counts.get(src, 0) + word_count
        except Exception as e: print(f" [!] Local Plagiarism Error: {e}")
    else:
        sentence_rarity = [(s, len(s)) for s in sentence_map]

    print(" [i] Running Smart Internet Scan (Parallel Targeted)...")
    top_targets = sorted(sentence_rarity, key=lambda x: x[1], reverse=True)[:4]
    
    # --- SPEED FIX: Execute 4 Google searches concurrently instead of 1 by 1 ---
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(fetch_web_match, target, plag_flags) for target in top_targets]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                original_s, display_url, clean_s = res
                plag_flags[original_s] = (display_url, 0.99)
                word_count = len(clean_s.split())
                source_word_counts[display_url] = source_word_counts.get(display_url, 0) + word_count
                print(f"      -> Web Match (High Rarity): {display_url}")

    ai_flags = {s for s in ai_flags if s not in plag_flags}
    spun_flags = {s for s in spun_flags if s not in plag_flags}

    aggregated_sources = []
    total_plagiarized_words = sum(source_word_counts.values())
    
    for src, count in source_word_counts.items():
        src_percentage = int((count / total_words_in_doc) * 100)
        if src_percentage == 0 and count > 0: src_percentage = 1 
        aggregated_sources.append((src, src_percentage))
    
    aggregated_sources = sorted(aggregated_sources, key=lambda x: x[1], reverse=True)
    overall_plag_score = int((total_plagiarized_words / total_words_in_doc) * 100)

    highlighted_html = ""
    pdf_data = []
    
    for s in sentences:
        clean_s = re.sub(r'<[^>]+>', '', s).strip()
        if len(clean_s.split()) <= 5:
            highlighted_html += s + " "
            pdf_data.append({"text": s + " ", "type": "clean"})
            continue

        if s in plag_flags:
            source, similarity = plag_flags[s]
            highlighted_html += f'<span class="highlight-plag" style="color: #f59e0b; font-weight: bold;" title="Found in: {source} ({round(similarity * 100)}% Match)">{s}</span> '
            pdf_data.append({"text": s + " ", "type": "plag"})
        elif s in ai_flags:
            highlighted_html += f'<span class="highlight-ai" style="color: #a855f7; font-weight: bold;" title="AI Generated">{s}</span> '
            pdf_data.append({"text": s + " ", "type": "ai"})
        elif s in spun_flags:
            highlighted_html += f'<span class="highlight-spun" style="color: #3b82f6; font-weight: bold; text-decoration: underline;" title="Paraphrased/Spinbot">{s}</span> '
            pdf_data.append({"text": s + " ", "type": "spun"})
        else:
            highlighted_html += s + " "
            pdf_data.append({"text": s + " ", "type": "clean"})

    total = max(1, len(valid_sentences))
    ai_score = int(((len(ai_flags) + len(spun_flags)) / total) * 100)
    
    if ai_score > 60: ai_label = "Highly Likely AI"
    elif ai_score > 30: ai_label = "Suspected AI"
    else: ai_label = "Human Driven"

    return text, aggregated_sources, overall_plag_score, ai_label, ai_score, highlighted_html, pdf_data