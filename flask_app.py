from flask import Flask, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import pandas as pd
from models import db, ClassCode, Student, ClassList, ClassSchedule, Attendance
from flask_migrate import Migrate
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx'}
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///classes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    class_counts = db.session.query(ClassList.class_code, db.func.count(ClassList.student_id)).group_by(ClassList.class_code).all()
    class_codes = ClassCode.query.all()
    class_schedules = ClassSchedule.query.all()
    return render_template('index.html', class_counts=class_counts, class_codes=class_codes, class_schedules=class_schedules)

@app.route('/admin/upload.html', methods=['GET', 'POST'])
def admin_upload():
    class_codes = []
    class_schedules = []
    if request.method == 'POST':
        if 'config_file' in request.files:
            file = request.files['config_file']
            if file.filename == '' or not allowed_file(file.filename):
                return redirect(request.url)
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            process_config_file(filepath)
            class_codes = ClassCode.query.all()
            class_schedules = ClassSchedule.query.all()
        elif 'class_file' in request.files:
            file = request.files['class_file']
            if file.filename == '' or not allowed_file(file.filename):
                return redirect(request.url)
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            process_class_file(filepath, filename)
        return render_template('upload.html', class_codes=class_codes, class_schedules=class_schedules)
    return render_template('upload.html', class_codes=class_codes, class_schedules=class_schedules)


def process_config_file(filepath):
    class_codes_df = pd.read_excel(filepath, sheet_name='ClassCodes')
    class_schedule_df = pd.read_excel(filepath, sheet_name='ClassSchedule')
    
    for _, row in class_codes_df.iterrows():
        class_code = ClassCode.query.filter_by(class_code=row['class_code']).first()
        if class_code is None:
            class_code = ClassCode(class_code=row['class_code'])
            db.session.add(class_code)
    
    for _, row in class_schedule_df.iterrows():
        # Convert date, start_time, and end_time to strings
        date_str = row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], pd.Timestamp) else str(row['date'])
        start_time_str = row['start_time'].strftime('%H:%M:%S') if isinstance(row['start_time'], pd.Timestamp) else str(row['start_time'])
        end_time_str = row['end_time'].strftime('%H:%M:%S') if isinstance(row['end_time'], pd.Timestamp) else str(row['end_time'])

        class_schedule = ClassSchedule.query.filter_by(
            class_code=row['class_code'], 
            date=date_str, 
            start_time=start_time_str, 
            end_time=end_time_str
        ).first()
        if class_schedule is None:
            class_schedule = ClassSchedule(
                class_code=row['class_code'], 
                date=date_str, 
                start_time=start_time_str, 
                end_time=end_time_str
            )
            db.session.add(class_schedule)
    
    db.session.commit()


def process_class_file(filepath, filename):
    df = pd.read_excel(filepath)
    for _, row in df.iterrows():
        student = Student.query.filter_by(student_id=row['student_id']).first()
        if student is None:
            student = Student(
                student_id=row['student_id'],
                given_name=row['given_name'],
                family_name=row['family_name'],
                gender=row['gender'],
                country=row['country'],
                email=row['email'],
                dob=row['dob']
            )
            db.session.add(student)
        class_list = ClassList.query.filter_by(class_code=row['class_code'], student_id=row['student_id']).first()
        if class_list is None:
            class_list = ClassList(class_code=row['class_code'], student_id=row['student_id'])
            db.session.add(class_list)
    db.session.commit()

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True, port=8080)
