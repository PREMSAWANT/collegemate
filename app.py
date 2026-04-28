from flask import Flask, request, jsonify, render_template, send_file, redirect, make_response, url_for, session, flash
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from models import db, User, StudentDetails, Admission, Conversation, Query, TimeSlot, Meeting, CollegeInfo, Document, UserInteraction, Setting, Faculty, Event, Grievance, Alumni
# Try to import Gemini, but make it optional
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

import os
import tempfile
import re
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import json
import random
from functools import wraps
import hashlib
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import PIL.Image
import io

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-here")

# Database Configuration
# Use SQLite for local development, can be easily switched to PostgreSQL via DATABASE_URL env var
# Database Configuration
# Use SQLite for local development, can be easily switched to PostgreSQL via DATABASE_URL env var
database_url = os.getenv('DATABASE_URL', 'sqlite:///college.db')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# File upload configuration (use /tmp for Vercel)
UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists (only writable in /tmp on Vercel)
try:
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
except OSError:
    pass  # Read-only filesystem, skip folder creation

# Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_AVAILABLE and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Admin Authentication
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Bmit@24"  # In production, use hashed password

# College Information (In-memory fallback, ideally should be in DB)
COLLEGE_INFO = {
    "name": "Brahmdevdada Mane Institute of Technology, Solapur",
    "short_name": "BMIT Solapur",
    "address": "Belati, Solapur - 413002, Maharashtra, India",
    "phone": "+91 98765 43210",
    "email": "info@bmitsolapur.com",
    "google_maps": "https://maps.app.goo.gl/NFZd1Rb8xFb1R3966",
    "logo": "/static/images/logo.png",
    "courses": {
        "cse": {"name": "Computer Science & Engineering", "seats": 60, "fee": 110000, "duration": 4, "image": "/static/images/cse.png", "department": "Computer Science", "description": "Learn cutting-edge technologies like AI, ML, and Cloud Computing."},
        "entc": {"name": "Electronics & Telecommunication", "seats": 60, "fee": 100000, "duration": 4, "image": "/static/images/entc.png", "department": "Electronics", "description": "Master the world of electronics, communication systems, and IoT."},
        "mech": {"name": "Mechanical Engineering", "seats": 60, "fee": 100000, "duration": 4, "image": "/static/images/mech.png", "department": "Mechanical", "description": "Design and build the future with core mechanical engineering principles."},
        "civil": {"name": "Civil Engineering", "seats": 60, "fee": 100000, "duration": 4, "image": "/static/images/civil.png", "department": "Civil", "description": "Shape the world with sustainable infrastructure and construction."},
        "mba": {"name": "Master of Business Administration", "seats": 60, "fee": 80000, "duration": 2, "image": "/static/images/mba.png", "department": "Management", "description": "Develop leadership skills and business acumen for the corporate world."}
    },
    "departments": ["Computer Science", "Electronics", "Mechanical", "Civil", "MBA", "General Science"],
    "facilities": [
        {"name": "Central Library", "description": "Well-stocked library with digital resources", "image": "/static/images/library.png", "icon": "fas fa-book"},
        {"name": "Hostel", "description": "Separate hostels for boys and girls with mess facilities", "image": "/static/images/hostel.jpg", "icon": "fas fa-bed"},
        {"name": "Sports Complex", "description": "Indoor and outdoor sports facilities", "image": "/static/images/sports.jpg", "icon": "fas fa-basketball-ball"},
        {"name": "Transportation", "description": "Bus service from all major parts of Solapur city", "image": "/static/images/transport.jpg", "icon": "fas fa-bus"},
        {"name": "Cafeteria", "description": "Hygienic food court serving nutritious meals", "image": "/static/images/cafeteria.jpg", "icon": "fas fa-utensils"}
    ],
    "announcements": [
        {"title": "Admissions Open 2025-26", "date": "2024-05-01", "content": "Admissions are now open for all undergraduate and postgraduate programs. Apply now!"},
        {"title": "Annual Tech Fest 'TechnoVision'", "date": "2024-04-15", "content": "Join us for the biggest technical festival of the year. exciting competitions and prizes to be won."},
        {"title": "Campus Recruitment Drive", "date": "2024-03-20", "content": "Major MNCs visiting campus for recruitment. Final year students, get ready!"}
    ]
}

# --- Helper Functions ---

def get_settings():
    """Load settings from database and merge with default COLLEGE_INFO"""
    try:
        db_settings = Setting.query.all()
        settings_dict = {}
        for s in db_settings:
            try:
                # Try to parse JSON if possible (for nested dicts like 'courses')
                settings_dict[s.key] = json.loads(s.value)
            except:
                settings_dict[s.key] = s.value
        
        # Merge with defaults
        merged_info = COLLEGE_INFO.copy()
        merged_info.update(settings_dict)
        return merged_info
    except Exception as e:
        print(f"Error loading settings: {str(e)}")
        return COLLEGE_INFO

def get_gemini_model():
    """Get Gemini model instance"""
    if not GEMINI_AVAILABLE:
        raise ImportError("Google Generative AI package is not installed")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured")
    return genai.GenerativeModel('gemini-2.5-flash')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session or session['user_type'] != 'admin':
            flash('You need admin privileges to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_client_history(phone_number):
    """Retrieve client's complete history including bookings and conversations"""
    # Get client details
    client_info = StudentDetails.query.filter_by(phone_number=phone_number).first()
    
    if not client_info:
        return None
    
    # Get booking history
    admissions = Admission.query.filter_by(phone_number=phone_number).order_by(Admission.application_date.desc()).all()
    
    # Get recent conversations
    conversations = Conversation.query.filter_by(phone_number=phone_number).order_by(Conversation.timestamp.desc()).limit(10).all()
    
    result = {
        'client_info': {c.name: getattr(client_info, c.name) for c in client_info.__table__.columns},
        'admissions': [{c.name: getattr(a, c.name) for c in a.__table__.columns} for a in admissions],
        'conversations': [{c.name: getattr(c, c.name) for c in c.__table__.columns} for c in conversations]
    }
    
    return result

def save_conversation(phone_number, message_type, content, context_data=None):
    """Save conversation to database"""
    try:
        conv = Conversation(
            phone_number=phone_number,
            message_type=message_type,
            message_content=content,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            context_data=json.dumps(context_data) if context_data else None
        )
        db.session.add(conv)
        db.session.commit()
    except Exception as e:
        print(f"Error saving conversation: {str(e)}")
        db.session.rollback()

def update_client_details(phone_number, info_dict):
    """Update client details in the database"""
    try:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        client = StudentDetails.query.filter_by(phone_number=phone_number).first()
        
        if client:
            # Update existing client
            client.student_name = info_dict.get('student_name', client.student_name)
            if info_dict.get('email'): client.email = info_dict.get('email')
            if info_dict.get('preferred_contact'): client.preferred_contact = info_dict.get('preferred_contact')
            if info_dict.get('notes'): client.notes = info_dict.get('notes')
            client.last_interaction = current_time
        else:
            # Insert new client
            client = StudentDetails(
                student_name=info_dict.get('student_name', 'Unknown'),
                phone_number=phone_number,
                email=info_dict.get('email'),
                preferred_contact=info_dict.get('preferred_contact'),
                notes=info_dict.get('notes'),
                first_interaction=current_time,
                last_interaction=current_time
            )
            db.session.add(client)
        
        db.session.commit()
        return client.id
    except Exception as e:
        print(f"Error updating client details: {str(e)}")
        db.session.rollback()
        return None

def get_eligibility_prediction(info_dict):
    """Use Gemini to predict admission eligibility based on scores"""
    try:
        if not GEMINI_AVAILABLE or not GEMINI_API_KEY:
            return "Unable to predict eligibility at this time."
            
        settings = get_settings()
        course_name = info_dict.get('course_name', 'General')
        
        prompt = f"""
        As an admission counselor at {settings['short_name']}, evaluate this student's eligibility for {course_name}:
        - 10th Score: {info_dict.get('tenth_percent')}%
        - 12th Score: {info_dict.get('twelfth_percent')}%
        - Entrance Exam Score: {info_dict.get('entrance_score')}
        
        Provide a brief (2-3 sentence) encouraging response about their chances and what they should do next.
        """
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error predicting eligibility: {str(e)}")
        return "Your application is being processed. We will contact you soon."

def process_admission(info_dict, phone_number):
    """Process admission information and save to database (Enhanced)"""
    try:
        settings = get_settings()
        course_id = info_dict.get('course_name', '').lower()
        
        found_course = None
        for key, val in settings['courses'].items():
            if key == course_id or val['name'].lower() == course_id.lower():
                found_course = key
                break
        
        if not found_course:
            return {"success": False, "message": "Invalid course selected."}
            
        course_details = settings['courses'][found_course]
        current_year = datetime.now().year
        batch_year = info_dict.get('batch_year', str(current_year))
        
        admission = Admission(
            student_name=info_dict.get('student_name', 'Unknown'),
            phone_number=phone_number,
            email=info_dict.get('email'),
            gender=info_dict.get('gender'),
            dob=info_dict.get('dob'),
            address=info_dict.get('address'),
            course_name=found_course,
            batch_year=batch_year,
            tenth_percent=float(info_dict.get('tenth_percent', 0)),
            twelfth_percent=float(info_dict.get('twelfth_percent', 0)),
            entrance_score=float(info_dict.get('entrance_score', 0)),
            total_amount=course_details['fee'],
            admission_status='under_review',
            application_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        db.session.add(admission)
        db.session.commit()
        
        return {
            "success": True,
            "message": f"Application for {course_details['name']} submitted successfully!",
            "admission_id": admission.id
        }
    except Exception as e:
        print(f"Error processing admission: {str(e)}")
        db.session.rollback()
        return {"success": False, "message": "An error occurred."}

def get_ai_response(message, conversation_history, image_data=None, personality='friendly'):
    """Get response from Gemini API, supporting text, images, and personality profiles"""
    try:
        if not message and not image_data:
            return "I didn't receive any message or image. Could you please try again?"
        
        if not GEMINI_AVAILABLE:
            return "I'm sorry, the AI chat feature is currently unavailable. The required package (google-generativeai) is not installed. Please contact the administrator."
        
        if not GEMINI_API_KEY:
            return "I'm sorry, the AI chat feature is not configured. Please contact the administrator."
            
        settings = get_settings()
        course_lines = []
        for key, course in settings['courses'].items():
            course_lines.append(f"- {course['name']}: {course['seats']} seats, ₹{course['fee']} per year, {course['duration']} years")
            
        personality_prompts = {
            'friendly': "You are Mia, a warm, friendly, and conversational AI assistant. You speak like a helpful human friend. Use emojis occasionally.",
            'formal': "You are Mia, a highly professional and efficient college administrator AI. Use formal language, clear structure, and be very precise.",
            'creative': "You are Mia, an enthusiastic and inspiring student ambassador. You are very energetic, use modern slang occasionally, and focus on the exciting campus life."
        }
        
        system_instruction = f"""{personality_prompts.get(personality, personality_prompts['friendly'])}
 
 You work at {settings['name']} (also known as {settings['short_name']}).
 
 College Information:
 - Full Name: {settings['name']}
 - Short Name: {settings['short_name']}
 - Address: {settings['address']}
 - Phone: {settings['phone']}
 
 Available Courses:
 """ + "\n".join(course_lines) + f"""
 
 Departments:
 - {', '.join(settings['departments'])}
 
 Campus Facilities:
 - {', '.join([facility['name'] for facility in settings['facilities']])}
 
 For admission inquiries, guide them to the online Admission Wizard at /admission/apply.
 Always ask for the student's phone number as it helps us keep track of their inquiries.
 
 IMPORTANT: Format your responses in a conversational way. Use complete sentences and paragraphs. NEVER use numbered lists or bullet points.
 """
        
        model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)
        
        # Convert history to Gemini format
        chat_history = []
        for entry in conversation_history:
            if entry.get('role') == 'user':
                chat_history.append({'role': 'user', 'parts': [entry.get('content')]})
            elif entry.get('role') == 'assistant':
                chat_history.append({'role': 'model', 'parts': [entry.get('content')]})
        
        # Prepare parts
        parts = []
        if message:
            parts.append(message)
        
        if image_data:
            img = PIL.Image.open(io.BytesIO(image_data))
            parts.append(img)
            
        chat = model.start_chat(history=chat_history)
        response = chat.send_message(parts)
        
        return response.text
    except Exception as e:
        print(f"Gemini API Error: {str(e)}")
        return f"I'm sorry, I'm having trouble connecting to my brain right now. Please try again later. (Error: {str(e)})"

def extract_info_from_message(user_message, ai_response):
    """Extract structured information from the conversation using Gemini"""
    try:
        if not GEMINI_AVAILABLE or not GEMINI_API_KEY:
            return "{}"
        
        model = get_gemini_model()
        prompt = f"""
        Analyze the following conversation and extract relevant information into a JSON object.
        User Message: "{user_message}"
        AI Response: "{ai_response}"
        
        Extract the following fields if present:
        - student_name: Name of the student
        - phone_number: Phone number
        - email: Email address
        - course: Course of interest
        - intent: The user's intent (e.g., "inquiry", "admission", "complaint", "general")
        
        Return ONLY the JSON object. Do not include markdown formatting like ```json ... ```.
        """
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean up markdown if present
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
            
        return text.strip()
    except Exception as e:
        print(f"Error extracting info: {str(e)}")
        return "{}"

def generate_speech_sync(text):
    """Generate speech from text using edge-tts (Mock implementation for now as edge-tts is async)"""
    # In a real Vercel deployment, file system is read-only except /tmp
    # For now we'll skip TTS or return a dummy URL
    return ""

def clean_text_for_speech(text):
    """Clean text for speech synthesis"""
    # Remove emojis and special chars
    text = re.sub(r'[^\w\s,.]', '', text)
    return text

# --- Routes ---

@app.route('/')
def home():
    alumni_list = Alumni.query.all()
    return render_template('index.html', college_info=get_settings(), alumni=alumni_list)

@app.route('/about')
def about():
    return render_template('about.html', college_info=get_settings())

@app.route('/courses')
def courses():
    return render_template('courses.html', college_info=get_settings())

@app.route('/facilities')
def facilities():
    return render_template('facilities.html', college_info=get_settings())

@app.route('/faculty')
def faculty():
    faculties = Faculty.query.order_by(Faculty.department).all()
    return render_template('faculty.html', faculties=faculties, college_info=get_settings())

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Save query to DB
        try:
            query = Query(
                name=request.form.get('name'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                subject=request.form.get('subject'),
                message=request.form.get('message')
            )
            db.session.add(query)
            db.session.commit()
            flash('Thank you for your message. We will get back to you soon!', 'success')
        except Exception as e:
            flash('An error occurred. Please try again.', 'error')
            
        return redirect(url_for('contact'))
        
    return render_template('contact.html', college_info=get_settings())

@app.route('/support', methods=['GET', 'POST'])
def support():
    if request.method == 'POST':
        try:
            new_grievance = Grievance(
                student_name=request.form.get('name'),
                phone_number=request.form.get('phone'),
                email=request.form.get('email'),
                category=request.form.get('category'),
                subject=request.form.get('subject'),
                description=request.form.get('description')
            )
            db.session.add(new_grievance)
            db.session.commit()
            flash('Your support request has been submitted. Ticket ID: #' + str(new_grievance.id), 'success')
            return redirect(url_for('support'))
        except Exception as e:
            db.session.rollback()
            flash('Error submitting request: ' + str(e), 'error')
            
    return render_template('support.html', college_info=get_settings())

@app.route('/admission/apply', methods=['GET', 'POST'])
def admission_apply():
    if 'user_id' not in session:
        flash('Please login to apply for admission.', 'info')
        return redirect(url_for('login'))
        
    settings = get_settings()
    
    if request.method == 'POST':
        # Simple implementation for now (can be expanded to handle multi-step)
        info_dict = request.form.to_dict()
        res = process_admission(info_dict, session.get('phone'))
        
        if res['success']:
            prediction = get_eligibility_prediction(info_dict)
            flash(res['message'], 'success')
            return render_template('admission_success.html', 
                                 admission_id=res['admission_id'],
                                 prediction=prediction,
                                 college_info=settings)
        else:
            flash(res['message'], 'error')
            
    return render_template('admission_wizard.html', college_info=settings)

@app.route('/api/chat', methods=['POST'])
def chat_api():
    try:
        # Handle both JSON and Multipart data
        if request.is_json:
            data = request.json
            user_message = data.get('message', '')
            conversation_history = data.get('conversation_history', [])
            phone_number = data.get('phone_number') or session.get('phone')
            personality = data.get('personality', 'friendly')
            image_data = None
        else:
            user_message = request.form.get('message', '')
            conversation_history_str = request.form.get('conversation_history', '[]')
            conversation_history = json.loads(conversation_history_str)
            phone_number = request.form.get('phone_number') or session.get('phone')
            personality = request.form.get('personality', 'friendly')
            
            image_file = request.files.get('image')
            image_data = image_file.read() if image_file else None
        
        # Get AI response
        ai_response = get_ai_response(user_message, conversation_history, image_data, personality)
        
        # Save conversation
        if phone_number:
            save_conversation(phone_number, 'user', user_message)
            save_conversation(phone_number, 'assistant', ai_response)
        
        # Extract info
        extracted_info = extract_info_from_message(user_message, ai_response)
        info_dict = json.loads(extracted_info)
        
        if info_dict and phone_number:
            update_client_details(phone_number, info_dict)
            if 'course' in info_dict and 'admission' in info_dict.get('intent', '').lower():
                process_admission(info_dict, phone_number)
        
        return jsonify({
            'text': ai_response,
            'audio_url': None 
        })
    except Exception as e:
        print(f"Error in chat_api: {str(e)}")
        return jsonify({'text': "I'm sorry, I encountered an error.", 'error': str(e)}), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        fullname = request.form['fullname']
        email = request.form['email']
        phone = request.form['phone']
        user_type = request.form['user_type']
        department = request.form.get('department')
        year = request.form.get('year')
        
        if username == ADMIN_USERNAME:
            return render_template('register.html', error="Username reserved.", college_info=get_settings())
        
        if password != confirm_password:
            return render_template('register.html', error="Passwords do not match", college_info=get_settings())
        
        # Check for existing username, email, or phone
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('register.html', error=f"Username '{username}' is already taken. Please choose another.", college_info=get_settings())
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            return render_template('register.html', error=f"Email '{email}' is already registered. Please use a different email or login.", college_info=get_settings())
        
        existing_phone = User.query.filter_by(phone=phone).first()
        if existing_phone:
            return render_template('register.html', error=f"Phone number '{phone}' is already registered. Please use a different number.", college_info=get_settings())
        
        try:
            password_hash = generate_password_hash(password)
            user = User(
                username=username,
                password_hash=password_hash,
                fullname=fullname,
                email=email,
                phone=phone,
                user_type=user_type,
                department=department,
                year=year
            )
            db.session.add(user)
            db.session.commit()
            
            session['user_id'] = user.id
            session['username'] = username
            session['fullname'] = fullname
            session['email'] = email
            session['phone'] = phone
            session['user_type'] = user_type
            
            return redirect(url_for('chat_page'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {str(e)}")
            return render_template('register.html', error="An error occurred during registration. Please try again.", college_info=get_settings())
    
    return render_template('register.html', college_info=get_settings())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME:
            # Check if admin user exists in DB, otherwise use default
            user = User.query.filter_by(username=username, user_type='admin').first()
            if user:
                if check_password_hash(user.password_hash, password):
                    session['user_id'] = user.id
                    session['username'] = user.username
                    session['user_type'] = 'admin'
                    return redirect(url_for('admin_dashboard'))
            elif password == ADMIN_PASSWORD:
                # Fallback for first-time setup (should be removed after first admin creation)
                session['user_id'] = 0
                session['username'] = username
                session['user_type'] = 'admin'
                return redirect(url_for('admin_dashboard'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['fullname'] = user.fullname
            session['email'] = user.email
            session['phone'] = user.phone
            session['user_type'] = user.user_type
            return redirect(url_for('chat_page'))
        
        return render_template('login.html', error="Invalid credentials", college_info=get_settings())
    
    return render_template('login.html', college_info=get_settings())

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin.html', college_info=get_settings())

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    if request.method == 'POST':
        try:
            # Update basic info
            basic_keys = ['name', 'short_name', 'address', 'phone', 'email']
            for key in basic_keys:
                if key in request.form:
                    setting = Setting.query.filter_by(key=key).first()
                    if setting:
                        setting.value = request.form[key]
                    else:
                        new_setting = Setting(key=key, value=request.form[key], category='college_info')
                        db.session.add(new_setting)
            
            # Update JSON info
            json_keys = ['courses', 'facilities', 'announcements']
            for key in json_keys:
                if key in request.form:
                    # Validate JSON before saving
                    json_val = request.form[key]
                    json.loads(json_val) # Will raise ValueError if invalid
                    
                    setting = Setting.query.filter_by(key=key).first()
                    if setting:
                        setting.value = json_val
                    else:
                        new_setting = Setting(key=key, value=json_val, category='college_info')
                        db.session.add(new_setting)
            
            db.session.commit()
            flash('Settings updated successfully!', 'success')
        except ValueError as e:
            flash(f'Invalid JSON format in settings: {str(e)}', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating settings: {str(e)}', 'error')
        
        return redirect(url_for('admin_settings'))

    # GET request
    settings = get_settings()
    # Add JSON strings for easy editing in textarea
    settings['courses_json'] = json.dumps(settings['courses'], indent=4)
    settings['facilities_json'] = json.dumps(settings['facilities'], indent=4)
    settings['announcements_json'] = json.dumps(settings['announcements'], indent=4)
    
    return render_template('admin_settings.html', settings=settings, college_info=settings)

@app.route('/api/admin/stats')
@admin_required
def admin_stats():
    today = datetime.now().strftime('%Y-%m-%d')
    visitors = db.session.query(Conversation.phone_number).distinct().filter(Conversation.timestamp.like(f'{today}%')).count()
    admissions = Admission.query.filter(Admission.application_date.like(f'{today}%')).count()
    conversations = Conversation.query.filter(Conversation.timestamp.like(f'{today}%')).count()
    
    return jsonify({
        'visitors': visitors,
        'conversations': conversations,
        'admissions': admissions,
        'response_rate': 100 # Placeholder
    })

@app.route('/api/admin/conversations')
@admin_required
def admin_conversations():
    convs = Conversation.query.order_by(Conversation.timestamp.desc()).limit(50).all()
    return jsonify([{
        'phone_number': c.phone_number,
        'message_type': c.message_type,
        'message_content': c.message_content,
        'timestamp': c.timestamp
    } for c in convs])

@app.route('/api/notifications')
def get_notifications():
    # Fetch upcoming events (within next 7 days)
    now = datetime.utcnow()
    next_week = now + timedelta(days=7)
    upcoming_events = Event.query.filter(Event.event_date >= now, Event.event_date <= next_week, Event.is_active == True).all()
    
    notifications = []
    for event in upcoming_events:
        notifications.append({
            'id': event.id,
            'title': event.title,
            'description': event.description[:100] + '...' if event.description else '',
            'type': 'event',
            'date': event.event_date.strftime('%d %b')
        })
    
    return jsonify(notifications)

@app.route('/api/admin/admissions')
@admin_required
def admin_admissions():
    adms = Admission.query.order_by(Admission.application_date.desc()).all()
    return jsonify([{
        'student_name': a.student_name,
        'course_name': a.course_name,
        'admission_status': a.admission_status,
        'application_date': a.application_date
    } for a in adms])

@app.route('/database-view')
@admin_required
def database_view():
    users = User.query.all()
    conversations = Conversation.query.limit(100).all()
    admissions = Admission.query.all()
    queries = Query.query.all()
    return render_template('database_view.html', 
                         users=users,
                         conversations=conversations,
                         admissions=admissions,
                         queries=queries)

@app.route('/api/export')
@admin_required
def export_data():
    try:
        # Create Excel writer object
        excel_path = os.path.join(tempfile.gettempdir(), 'college_data.xlsx')
        
        # Get dataframes
        users_df = pd.read_sql(User.query.statement, db.session.bind)
        admissions_df = pd.read_sql(Admission.query.statement, db.session.bind)
        conversations_df = pd.read_sql(Conversation.query.statement, db.session.bind)
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            users_df.to_excel(writer, sheet_name='Users', index=False)
            admissions_df.to_excel(writer, sheet_name='Admissions', index=False)
            conversations_df.to_excel(writer, sheet_name='Conversations', index=False)
            
        return send_file(excel_path, 
                       mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                       as_attachment=True,
                       download_name='college_data.xlsx')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/analytics')
@admin_required
def admin_analytics():
    # Simplified analytics for now
    return jsonify({
        'traffic': [],
        'topics': []
    })

def init_db():
    with app.app_context():
        db.create_all()

@app.route('/init-db')
def initialize_database():
    try:
        db.create_all()
        return jsonify({'message': 'Database initialized successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
