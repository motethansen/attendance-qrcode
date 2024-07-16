from flask import Flask, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import pandas as pd
import sqlite3
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx'}

# Database initialization
def init_db():
    conn = sqlite3.connect('classes.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            class_id TEXT PRIMARY KEY,
            date TEXT,
            time TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            class_id TEXT
        )
    ''')
    conn.commit()
    conn.close()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

init_db()

@app.route('/')
def index():
    conn = sqlite3.connect('classes.db')
    c = conn.cursor()
    c.execute('SELECT class_id, COUNT(student_id) FROM students GROUP BY class_id')
    class_counts = c.fetchall()
    conn.close()
    return render_template('index.html', class_counts=class_counts)

@app.route('/admin/upload.html', methods=['GET', 'POST'])
def admin_upload():
    if request.method == 'POST':
        if 'config_file' in request.files:
            file = request.files['config_file']
            if file.filename == '' or not allowed_file(file.filename):
                return redirect(request.url)
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            process_config_file(filepath)
        elif 'class_file' in request.files:
            file = request.files['class_file']
            if file.filename == '' or not allowed_file(file.filename):
                return redirect(request.url)
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            process_class_file(filepath, filename)
        return redirect(url_for('index'))
    return render_template('upload.html')

def process_config_file(filepath):
    df = pd.read_excel(filepath)
    conn = sqlite3.connect('classes.db')
    c = conn.cursor()
    for _, row in df.iterrows():
        c.execute('INSERT OR REPLACE INTO classes (class_id, date, time) VALUES (?, ?, ?)',
                  (row['class_id'], row['date'], row['time']))
    conn.commit()
    conn.close()

def process_class_file(filepath, filename):
    class_id = filename.split('_')[0]
    df = pd.read_excel(filepath)
    conn = sqlite3.connect('classes.db')
    c = conn.cursor()
    for _, row in df.iterrows():
        c.execute('INSERT OR IGNORE INTO students (student_id, class_id) VALUES (?, ?)', (row['student_id'], class_id))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)

