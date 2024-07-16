from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class ClassCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_code = db.Column(db.String(50), unique=True, nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    given_name = db.Column(db.String(50), nullable=False)
    family_name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    country = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.String(10), nullable=False)

class ClassList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_code = db.Column(db.String(50), db.ForeignKey('class_code.class_code'), nullable=False)
    student_id = db.Column(db.String(50), db.ForeignKey('student.student_id'), nullable=False)

class ClassSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_code = db.Column(db.String(50), db.ForeignKey('class_code.class_code'), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    start_time = db.Column(db.String(5), nullable=False)
    end_time = db.Column(db.String(5), nullable=False)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_schedule_id = db.Column(db.Integer, db.ForeignKey('class_schedule.id'), nullable=False)
    student_id = db.Column(db.String(50), db.ForeignKey('student.student_id'), nullable=False)
    attendance = db.Column(db.Boolean, nullable=False)
    time_of_registration = db.Column(db.String(5), nullable=False)
