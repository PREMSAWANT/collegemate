from flask import Flask, request, jsonify, render_template, send_file, redirect, make_response, url_for, session, flash
import json
import random
from functools import wraps
import hashlib
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

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

# File upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
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
    "website": "https://bmitsolapur.com",
    "courses": {
        "cse": {"name": "Computer Science & Engineering", "seats": 60, "fee": 110000, "duration": 4},
        "entc": {"name": "Electronics & Telecommunication", "seats": 60, "fee": 100000, "duration": 4},
        "mech": {"name": "Mechanical Engineering", "seats": 60, "fee": 100000, "duration": 4},
        "civil": {"name": "Civil Engineering", "seats": 60, "fee": 100000, "duration": 4},
        "mba": {"name": "Master of Business Administration", "seats": 60, "fee": 80000, "duration": 2}
    },
    "departments": ["Computer Science", "Electronics", "Mechanical", "Civil", "MBA", "General Science"],
    "facilities": [
        {"name": "Central Library", "description": "Well-stocked library with digital resources"},
        {"name": "Hostel", "description": "Separate hostels for boys and girls with mess facilities"},
        {"name": "Sports Complex", "description": "Indoor and outdoor sports facilities"},
        {"name": "Transportation", "description": "Bus service from all major parts of Solapur city"},
        {"name": "Cafeteria", "description": "Hygienic food court serving nutritious meals"}
    ]
}

# --- Helper Functions ---

def get_gemini_model():
    """Get Gemini model instance"""
    return genai.GenerativeModel('gemini-1.5-flash')

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

def process_admission(info_dict, phone_number):
    """Process admission information and save to database"""
    try:
        # Get course details
        course_name = info_dict.get('course', '').lower()
        
        # Simple mapping if exact match not found
        found_course = None
        for key, val in COLLEGE_INFO['courses'].items():
            if key in course_name or val['name'].lower() in course_name:
                found_course = key
                break
        
        if not found_course:
            return {
                "success": False, 
                "message": f"We don't offer a course named {course_name}. Available courses are: {', '.join([c['name'] for c in COLLEGE_INFO['courses'].values()])}"
            }
            
        course_details = COLLEGE_INFO['courses'][found_course]
        
        # Get batch year (current or next year)
        current_year = datetime.now().year
        batch_year = info_dict.get('batch_year', str(current_year))
            
        # Check if student already has an application
        existing = Admission.query.filter_by(phone_number=phone_number, course_name=found_course, batch_year=batch_year).first()
        
        if existing:
            return {
                "success": False, 
                "message": f"You already have an application for {course_details['name']} for batch {batch_year}. Your application ID is {existing.id}."
            }
        
        # Get student name
        student = StudentDetails.query.filter_by(phone_number=phone_number).first()
        student_name = student.student_name if student else "Unknown"
        
        # Insert admission record
        admission = Admission(
            student_name=student_name,
            phone_number=phone_number,
            course_name=found_course,
            batch_year=batch_year,
            total_amount=course_details['fee'],
            admission_status='applied',
            application_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        db.session.add(admission)
        db.session.commit()
        
        return {
            "success": True,
            "message": f"Application for {course_details['name']} has been submitted successfully. Your application ID is {admission.id}.",
            "admission_id": admission.id,
            "course": course_details['name'],
            "fee": course_details['fee'],
            "batch_year": batch_year
        }
        
    except Exception as e:
        print(f"Error processing admission: {str(e)}")
        db.session.rollback()
        return {"success": False, "message": "An error occurred while processing your admission application."}

def get_ai_response(message, conversation_history):
    """Get response from Gemini API"""
    try:
        if not message:
            return "I didn't receive any message. Could you please try again?"
            
        # Prepare system message
        course_lines = []
        for key, course in COLLEGE_INFO['courses'].items():
            course_lines.append(f"- {course['name']}: {course['seats']} seats, ₹{course['fee']} per year, {course['duration']} years")
            
        system_instruction = f"""You are Mia, a friendly and helpful AI college assistant at {COLLEGE_INFO['name']} (also known as {COLLEGE_INFO['short_name']}).

Your personality: You are warm, friendly, and conversational. You speak like a helpful human assistant would.

College Information:
- Full Name: {COLLEGE_INFO['name']}
- Short Name: {COLLEGE_INFO['short_name']}
- Address: {COLLEGE_INFO['address']}
- Phone: {COLLEGE_INFO['phone']}

Available Courses:
""" + "\n".join(course_lines) + f"""

Departments:
- {', '.join(COLLEGE_INFO['departments'])}

Campus Facilities:
- {', '.join([facility['name'] for facility in COLLEGE_INFO['facilities']])}

For admission inquiries, collect the student's name, phone number, course of interest, and any specific questions they have.
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
        
        chat = model.start_chat(history=chat_history)
        response = chat.send_message(message)
        
        return response.text
    except Exception as e:
        print(f"Gemini API Error: {str(e)}")
        return f"I'm sorry, I'm having trouble connecting to my brain right now. Please try again later. (Error: {str(e)})"

def extract_info_from_message(user_message, ai_response):
    """Extract structured information from the conversation using Gemini"""
    try:
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
    return render_template('index.html', college_info=COLLEGE_INFO)

@app.route('/about')
def about():
    return render_template('about.html', college_info=COLLEGE_INFO)

@app.route('/courses')
def courses():
    return render_template('courses.html', college_info=COLLEGE_INFO)

@app.route('/facilities')
def facilities():
    return render_template('facilities.html', college_info=COLLEGE_INFO)

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
        
    return render_template('contact.html', college_info=COLLEGE_INFO)

@app.route('/chat')
def chat_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat_api():
    try:
        data = request.json
        user_message = data.get('message', '')
        conversation_history = data.get('conversation_history', [])
        phone_number = data.get('phone_number') or session.get('phone')
        
        # Get AI response
        ai_response = get_ai_response(user_message, conversation_history)
        
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
            'audio_url': None # TTS disabled for Vercel compatibility for now
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
        
        if username == ADMIN_USERNAME:
            return render_template('register.html', error="Username reserved.")
        
        if password != confirm_password:
            return render_template('register.html', error="Passwords do not match")
        
        try:
            password_hash = generate_password_hash(password)
            user = User(
                username=username,
                password_hash=password_hash,
                fullname=fullname,
                email=email,
                phone=phone,
                user_type=user_type
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
            return render_template('register.html', error="Username or email already exists")
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
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
        
        return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin.html', college_info=COLLEGE_INFO)

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
@app.route('/facilities')
def facilities():
    return render_template('facilities.html', college_info=COLLEGE_INFO)

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
        
    return render_template('contact.html', college_info=COLLEGE_INFO)

@app.route('/chat')
def chat_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat_api():
    try:
        data = request.json
        user_message = data.get('message', '')
        conversation_history = data.get('conversation_history', [])
        phone_number = data.get('phone_number') or session.get('phone')
        
        # Get AI response
        ai_response = get_ai_response(user_message, conversation_history)
        
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
            'audio_url': None # TTS disabled for Vercel compatibility for now
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
        
        if username == ADMIN_USERNAME:
            return render_template('register.html', error="Username reserved.")
        
        if password != confirm_password:
            return render_template('register.html', error="Passwords do not match")
        
        try:
            password_hash = generate_password_hash(password)
            user = User(
                username=username,
                password_hash=password_hash,
                fullname=fullname,
                email=email,
                phone=phone,
                user_type=user_type
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
            return render_template('register.html', error="Username or email already exists")
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
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
        
        return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin.html', college_info=COLLEGE_INFO)

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