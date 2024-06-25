from flask import Flask, render_template, url_for, jsonify, redirect, request
import qrcode
import io
from datetime import datetime, timedelta
import hashlib
from flask import send_file
import threading

app = Flask(__name__)

# List to store hash values and their expiration times
hash_list = []
attendance_count = 0

def generate_qr_data():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    hash_object = hashlib.md5(timestamp.encode())
    hash_value = hash_object.hexdigest()
    qr_url = url_for('qr_code_test', timestamp=timestamp, hash=hash_value, _external=True)
    
    # Add hash value to the list with expiration time
    expiration_time = datetime.now() + timedelta(minutes=3)
    hash_list.append((hash_value, expiration_time))
    
    return qr_url

def remove_expired_hashes():
    while True:
        now = datetime.now()
        hash_list[:] = [(h, t) for h, t in hash_list if t > now]
        threading.Event().wait(60)  # Check every minute

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/qr_code_test')
def qr_code_test():
    hash_value = request.args.get('hash')
    now = datetime.now()
    
    # Check if the hash value is in the list
    if any(h == hash_value for h, t in hash_list):
        return redirect(url_for('attendance', timestamp=now.strftime("%a %d %Y -- %H:%M:%S")))
    else:
        return redirect(url_for('expired'))

@app.route('/attendance')
def attendance():
    timestamp = request.args.get('timestamp')
    return render_template('attendance.html', timestamp=timestamp)

@app.route('/submit_attendance', methods=['POST'])
def submit_attendance():
    global attendance_count
    student_id = request.form.get('student_id')
    timestamp = request.form.get('timestamp')
    # Here you would typically save this information to a database
    attendance_count += 1
    return f"Attendance recorded for Student ID: {student_id} at {timestamp}"

@app.route('/get_attendance_count')
def get_attendance_count():
    return jsonify({'count': attendance_count})

@app.route('/expired')
def expired():
    return render_template('expired.html')

@app.route('/qr_code_image')
def qr_code_image():
    qr_url = generate_qr_data()
    qr = qrcode.make(qr_url)
    img_io = io.BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/get_qr_url')
def get_qr_url():
    return jsonify({'url': url_for('qr_code_image')})

if __name__ == '__main__':
    # Start a background thread to remove expired hashes
    threading.Thread(target=remove_expired_hashes, daemon=True).start()
    app.run(debug=True)


