import sys
import os
import time
import sqlite3
import uuid
import shutil
from flask import Flask, render_template, request, redirect, url_for, session, make_response
from authlib.integrations.flask_client import OAuth
from xhtml2pdf import pisa
from io import BytesIO

print("\n" + "="*50)
print("PLAGIARISM GUARD: CORE SERVER STARTING")
print("="*50)

app = Flask(__name__)
app.secret_key = 'piet_final_project_2026_safe'

# --- GOOGLE OAUTH CONFIG ---
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='424588205949-ruahf80h5rshqeggrucbnik699n4e60v.apps.googleusercontent.com', 
    client_secret='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', 
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

REPORT_CACHE = {}
UPLOAD_FOLDER = 'uploads'
DB_PATH = 'plag_guard.db'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        filename TEXT, 
        plag_score INTEGER, 
        ai_score INTEGER, 
        ai_label TEXT, 
        word_count INTEGER, 
        process_time REAL, 
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
        user_email TEXT)''')
    conn.close()

# --- MAIN ROUTES ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename:
            print(f" [*] Processing: {file.filename}")
            start = time.time()
            path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(path)
            
            # --- THE SELF-LEARNING UPGRADE ---
            os.makedirs('reference_docs', exist_ok=True)
            reference_path = os.path.join('reference_docs', file.filename)
            shutil.copy(path, reference_path)
            # ---------------------------------
            
            try:
                import logic 
                txt, matches, label, ai_s, h_html, pdf_d = logic.check_plagiarism(path)
                
                # Tell the database to learn the new file in the background
                logic.rebuild_database()
            except Exception as e:
                print(f" [!] AI Processing Error: {e}")
                return f"Internal AI Error: {e}", 500
            
            p_score = matches[0][1] if matches else 0
            rid = str(uuid.uuid4())
            REPORT_CACHE[rid] = {
                "filename": file.filename, "plag_score": p_score, 
                "ai_score": ai_s, "ai_label": label, 
                "word_count": len(txt.split()), 
                "process_time": round(time.time()-start,2), 
                "web_matches": matches, "highlighted_text": h_html, "pdf_data": pdf_d
            }
            session['report_id'] = rid
            
            conn = sqlite3.connect(DB_PATH)
            conn.execute("INSERT INTO scans (filename, plag_score, ai_score, ai_label, word_count, process_time, user_email) VALUES (?,?,?,?,?,?,?)", 
                         (file.filename, p_score, ai_s, label, len(txt.split()), round(time.time()-start,2), session.get('email', 'Guest')))
            conn.commit()
            conn.close()
            return redirect(url_for('report'))
    return render_template('index.html')

# --- AUTH ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['email'] = request.form.get('email')
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/google_login')
def google_login():
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/google_callback')
def google_callback():
    try:
        token = google.authorize_access_token()
        resp = google.get('https://www.googleapis.com/oauth2/v3/userinfo')
        user_info = resp.json()
        session['email'] = user_info['email']
        session['name'] = user_info.get('name', 'User')
        return redirect(url_for('index'))
    except Exception as e:
        print(f" [!] Auth Error: {e}")
        return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        session['email'] = request.form.get('email')
        return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- VIEWS ---
@app.route('/report')
def report():
    rid = session.get('report_id')
    if rid in REPORT_CACHE: return render_template('report.html', scan_result=REPORT_CACHE[rid])
    return redirect(url_for('index'))

@app.route('/history')
def history():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row 
    cursor = conn.execute("SELECT filename, plag_score, ai_score, date FROM scans ORDER BY date DESC")
    scans = cursor.fetchall()
    conn.close()
    return render_template('history.html', scans=scans)

@app.route('/download')
def download():
    rid = session.get('report_id')
    if rid not in REPORT_CACHE: return redirect(url_for('index'))
    html = render_template('pdf_export.html', scan_result=REPORT_CACHE[rid], time=time)
    pdf_out = BytesIO()
    pisa.CreatePDF(html, dest=pdf_out)
    resp = make_response(pdf_out.getvalue())
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = f'attachment; filename=Report_{int(time.time())}.pdf'
    return resp

# --- ADMIN DASHBOARD ---
@app.route('/admin')
def admin_dashboard():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row 
    cursor = conn.execute("SELECT * FROM scans ORDER BY date DESC")
    all_scans = cursor.fetchall()
    conn.close()
    
    total_submissions = len(all_scans)
    flagged_plag = sum(1 for s in all_scans if s['plag_score'] > 20)
    flagged_ai = sum(1 for s in all_scans if s['ai_score'] > 40)
    
    return render_template('admin_dashboard.html', 
                           scans=all_scans, 
                           total=total_submissions, 
                           f_plag=flagged_plag, 
                           f_ai=flagged_ai)

if __name__ == '__main__':
    init_db()
    print(" [i] Server is LIVE at http://127.0.0.1:5000")
    print("="*50 + "\n")
    app.run(debug=True, use_reloader=False)