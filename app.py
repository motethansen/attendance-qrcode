from flask import Flask, render_template, url_for, jsonify, redirect, request
import qrcode
import io
import os
import re
from datetime import datetime, timedelta
import hashlib
from flask import send_file
import threading
import pandas as pd

app = Flask(__name__)

# List to store hash values and their expiration times
hash_list = []
attendance_count = 0

# Path to the Excel file
#EXCEL_FILE = 'classes/BU2001-TF-1000.xlsx'

# Example usage
directory = 'classes'
classcode = 'BU2001'
student_id = '12345'
date_str = '26-06-2024'  # The column name for the date

# the format for filename shoudl be CLASSCODE_DDMMYYYY_HHMM (e.g. BU2001_26062024_1000.xlsx)
def get_latest_excel_file(directory, classcode):
    # Get the current date and time
    now = datetime.now()

    # Define the file name pattern
    file_pattern = re.compile(r'([\w-]+)_\d{8}_\d{4}\.xlsx')

    # List all files in the directory
    files = os.listdir(directory)

    # Filter files that match the pattern
    matched_files = [f for f in files if file_pattern.match(f)]

    # Filter files based on the current date
    date_today = now.strftime('%d%m%Y')
    date_filtered_files = [f for f in matched_files if f.split('_')[1][:8] == date_today]

    # If no files are found for today, return None
    if not date_filtered_files:
        return None

    # Further filter files based on the time constraint (within 2 hours window)
    valid_files = []
    for file in date_filtered_files:
        time_str = file.split('_')[2][:4]
        file_datetime = datetime.strptime(date_today + time_str, "%d%m%Y%H%M")
        if now-timedelta(hours=1, minutes=30) <= file_datetime <= now:
            valid_files.append(file)

    # If no valid files are found within the time window, return None
    if not valid_files:
        return None

    # Prioritize files by classcode
    classcode_files = [f for f in valid_files if f.startswith(classcode)]
    if classcode_files:
        return os.path.join(directory, classcode_files[0])

    # If no files match the classcode exactly, return the latest valid file
    valid_files.sort(key=lambda f: datetime.strptime(f.split('_')[1][:8] + f.split('_')[2][:4], "%d%m%Y%H%M"), reverse=True)
    return os.path.join(directory, valid_files[0]) if valid_files else None

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


def check_location(lat, lon):
    # Calculate distance between two points using Haversine formula
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(ACCEPTED_LAT)
    phi2 = math.radians(lat)
    delta_phi = math.radians(lat - ACCEPTED_LAT)
    delta_lambda = math.radians(lon - ACCEPTED_LON)

    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    distance = R * c

    return distance <= ACCEPTED_RADIUS


@app.route('/')
def index():
    latest_file = get_latest_excel_file(directory, classcode)
    if latest_file != None:
        class_code = latest_file.split('_')[0].replace('classes/', '')
        start_time = datetime.strptime(latest_file.split('_')[1][:8] + latest_file.split('_')[2][:4], "%d%m%Y%H%M")
    else:
        class_code = None
        start_time = None
    if class_code and start_time:
        start_time_str = start_time.strftime(' %H:%M')
    else:
        class_code = "No classcode and student list found"
        start_time_str = "N/A"
    return render_template('index.html', class_code=class_code, start_time=start_time_str)

@app.route('/qr_code_test')
def qr_code_test():
    hash_value = request.args.get('hash')
    now = datetime.now()
    
    # Check if the hash value is in the list
    if any(h == hash_value for h, t in hash_list):    
        return redirect(url_for('attendance', timestamp=now.strftime("%a %d %Y -- %H:%M:%S"), hash = hash_value))
    else:
        return redirect(url_for('expired'))

@app.route('/attendance')
def attendance():
    timestamp = request.args.get('timestamp')
    hash_value = request.args.get('hash')
    return render_template('attendance.html', timestamp=timestamp, hash_value=hash_value)#, accepted_lat=ACCEPTED_LAT, accepted_lon=ACCEPTED_LON, accepted_radius=ACCEPTED_RADIUS)

@app.route('/lookup_student', methods=['POST'])
def lookup_student():
    student_id = request.form.get('student_id')
    lastestfile = get_latest_excel_file(directory, classcode)
    df = pd.read_excel(lastestfile)

    student = df[df['STUDENTID'] == student_id]
    if not student.empty:
        student_name = student.iloc[0]['Name']
        return jsonify({'name': student_name})
    else:
        return jsonify({'name': None})
    
@app.route('/submit_attendance', methods=['POST'])
def submit_attendance():
    global attendance_count
    student_id = request.form.get('student_id')
    timestamp = request.form.get('timestamp')
    hash_value = request.form.get('hash')
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    lastestfile = get_latest_excel_file(directory, classcode)

    # Load the Excel file
    df = pd.read_excel(lastestfile)

    print( "Hash :", hash_value)
    # Strip any spaces from STUDENTID if they are string
    if df['STUDENTID'].dtype == 'O':  # Object type often means strings in pandas
        df['STUDENTID'] = df['STUDENTID'].str.strip()

    # Check if the hash value is in the list
    if any(h == hash_value for h, t in hash_list): 
        # Convert student_id to integer
        try:
            student_id = int(student_id.strip())  # Strip spaces and convert to integer
        except ValueError:
            print("Invalid student_id format; must be an integer.")

        # Check if the hash value is in the list
        if (student_id in df['STUDENTID'].values):
            if (df.loc[df['STUDENTID'] == student_id, date_str].values[0] != 1):
                # Here you would typically save this information to a database
                df.loc[df['STUDENTID'] == student_id, date_str] = 1
                df.to_excel(lastestfile, index=False)
                attendance_count += 1
                return f"Attendance recorded for Student ID: {student_id} at {timestamp}"
            else:
                return f"Registration was already recorded for Student ID: {student_id}"
        else:
            return "Student ID not found"
    else:
        return redirect(url_for('expired'))
        
@app.route('/get_attendance_count')
def get_attendance_count():
    return jsonify({'count': attendance_count})

@app.route('/expired')
def expired():
    return render_template('expired.html')

@app.route('/wrong_location')
def wrong_location():
    return render_template('wrong_location.html')

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


