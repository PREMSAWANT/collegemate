from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StudentDetails(db.Model):
    __tablename__ = 'student_details'
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120))
    preferred_contact = db.Column(db.String(50))
    notes = db.Column(db.Text)
    first_interaction = db.Column(db.String(50), nullable=False)
    last_interaction = db.Column(db.String(50), nullable=False)
    
    admissions = db.relationship('Admission', backref='student', lazy=True)
    meetings = db.relationship('Meeting', backref='student', lazy=True)

class Admission(db.Model):
    __tablename__ = 'admissions'
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), db.ForeignKey('student_details.phone_number'), nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    batch_year = db.Column(db.String(20), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    admission_status = db.Column(db.String(20), default='applied')
    application_date = db.Column(db.String(50), nullable=False)

class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20))
    message_type = db.Column(db.String(20), nullable=False)
    message_content = db.Column(db.Text, nullable=False)
    context_data = db.Column(db.Text)
    timestamp = db.Column(db.String(50), nullable=False)

class Query(db.Model):
    __tablename__ = 'queries'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TimeSlot(db.Model):
    __tablename__ = 'time_slots'
    id = db.Column(db.Integer, primary_key=True)
    date_str = db.Column(db.String(20), nullable=False)
    time_str = db.Column(db.String(20), nullable=False)
    is_available = db.Column(db.Integer, default=1, nullable=False)
    __table_args__ = (db.UniqueConstraint('date_str', 'time_str', name='unique_slot'),)

class Meeting(db.Model):
    __tablename__ = 'meetings'
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), db.ForeignKey('student_details.phone_number'), nullable=False)
    email = db.Column(db.String(120))
    purpose = db.Column(db.String(200), nullable=False)
    date_str = db.Column(db.String(20), nullable=False)
    time_str = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='scheduled')

class CollegeInfo(db.Model):
    __tablename__ = 'college_info'
    id = db.Column(db.Integer, primary_key=True)
    section = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))

class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))

class UserInteraction(db.Model):
    __tablename__ = 'user_interactions'
    id = db.Column(db.Integer, primary_key=True)
    interaction_time = db.Column(db.String(50))
    user_message = db.Column(db.Text)
    ai_response = db.Column(db.Text)
    extracted_info = db.Column(db.Text)
    interaction_type = db.Column(db.String(50))
