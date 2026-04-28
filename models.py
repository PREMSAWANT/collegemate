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
    department = db.Column(db.String(50))
    year = db.Column(db.String(20))
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
    email = db.Column(db.String(120))
    gender = db.Column(db.String(20))
    dob = db.Column(db.String(20))
    address = db.Column(db.Text)
    
    course_name = db.Column(db.String(100), nullable=False)
    batch_year = db.Column(db.String(20), nullable=False)
    
    tenth_percent = db.Column(db.Float)
    twelfth_percent = db.Column(db.Float)
    entrance_score = db.Column(db.Float)
    
    document_url = db.Column(db.String(200)) # Path to uploaded marksheet/ID
    total_amount = db.Column(db.Float, nullable=False)
    admission_status = db.Column(db.String(20), default='applied') # applied, pending_docs, under_review, approved, rejected
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

class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50)) # e.g., 'college_info', 'ui_settings'
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Faculty(db.Model):
    __tablename__ = 'faculty'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    expertise = db.Column(db.String(200))
    email = db.Column(db.String(120), unique=True)
    image_url = db.Column(db.String(200))
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(100))
    category = db.Column(db.String(50)) # workshop, seminar, sports, culture
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Grievance(db.Model):
    __tablename__ = 'grievances'
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    category = db.Column(db.String(50), nullable=False) # academic, hostel, transport, fees, other
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, in_progress, resolved, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Alumni(db.Model):
    __tablename__ = 'alumni'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    batch = db.Column(db.String(20), nullable=False)
    company = db.Column(db.String(100))
    position = db.Column(db.String(100))
    testimonial = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    linkedin_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Resource(db.Model):
    __tablename__ = 'resources'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False) # e-book, syllabus, question_paper, note
    department = db.Column(db.String(100), nullable=False)
    file_url = db.Column(db.String(200))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FeeStatus(db.Model):
    __tablename__ = 'fee_status'
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), db.ForeignKey('student_details.phone_number'), nullable=False)
    total_fee = db.Column(db.Float, nullable=False)
    paid_fee = db.Column(db.Float, default=0.0)
    due_date = db.Column(db.String(20))
    status = db.Column(db.String(20), default='pending') # pending, partially_paid, paid
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
