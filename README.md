# CollegeMate - BMIT Solapur AI Assistant

CollegeMate is an AI-powered assistant for Brahmdevdada Mane Institute of Technology, Solapur. It helps students with admissions inquiries, course information, and campus facilities through an intelligent chatbot interface.

**Live Demo:** [https://collegemate-bmit.vercel.app/](https://collegemate-bmit.vercel.app/)

> **Note:** The database features (registration, login, chat history) and AI responses in the live demo may be limited or unavailable as it relies on a local database. For full functionality, please run the project locally.

## Features

### Static Features (Available in Live Demo)
- � College Information (About)
- 📚 Course Details & Fees
- 🏫 Campus Facilities Showcase
- 📞 Contact Information

### Local-Only Features (Requires Local Setup)
- 🔐 User Authentication (Login/Register)
- 💬 AI Chatbot with History (Requires Gemini API)
- 📊 Admin Dashboard & Analytics
- 📝 Admission Management System
- � User Profile Management

> **Note:** The live demo runs on Vercel with a read-only filesystem. For full functionality including user accounts and database persistence, please set up the project locally.

## Screenshots

### Chat Interface
Beautiful split-screen layout with chatbot on the left and user details on the right.

![Chat Interface](static/screenshots/new_chat_ui_1765028215355.png)

### Homepage
Modern and responsive landing page.

![Homepage](static/screenshots/homepage_ui_1765028484018.png)

### Courses Page
Detailed course information and fee structure.

![Courses Page](static/screenshots/courses_page_ui_1765028599429.png)

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Google Gemini API key (free tier available)
- PostgreSQL database (or SQLite for local development)

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/PremSawant/collegemate.git
cd collegemate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

> **⚠️ IMPORTANT: API Keys Are Placeholders**
> 
> All API keys and secrets in `.env.example` are **placeholders only**. 
> You **must** replace them with your own valid keys before running the application.

Copy `.env.example` to `.env`:
```bash
cp .env.example .env  # On Unix/Mac
copy .env.example .env  # On Windows
```

Update the following variables in `.env`:

#### Required Configuration

- **SECRET_KEY**: Generate a secure random key for Flask sessions
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

- **GEMINI_API_KEY**: Your Google Gemini API key
  - Get yours at: https://ai.google.dev/
  - Free tier available with generous limits
  - Example: `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXX`

- **DATABASE_URL**: Your PostgreSQL database connection string
  - Format: `postgresql://username:password@host:port/database`
  - For local SQLite (development): `sqlite:///college.db`
  - For production (Neon, Supabase, etc.): Use the provided connection string

### 4. Initialize the database
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized!')"
```

### 5. Run the application

To run locally with SQLite (recommended for testing):

```bash
# Windows PowerShell
$env:DATABASE_URL='sqlite:///college.db'; python app.py

# Unix/Mac
export DATABASE_URL='sqlite:///college.db' && python app.py
```

The application will be available at `http://localhost:5000`

## Admin Access

### Admin Dashboard Credentials

- **Username**: `admin`
- **Password**: `Bmit@24`

> **🔒 Security Note**: Change the admin password in production by updating the `ADMIN_PASSWORD` variable in `app.py` (line 60).

Access the admin dashboard at: `http://localhost:5000/admin/dashboard`

### Admin Features
- View conversation statistics
- Monitor student interactions
- Export data to Excel
- Manage admissions and queries

## Project Structure

```
collegemate/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template (PLACEHOLDERS ONLY)
├── .gitignore            # Git ignore file (protects secrets)
├── templates/            # HTML templates
│   ├── index.html        # Homepage
│   ├── chat.html         # Chat interface (split-screen UI)
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   └── admin.html        # Admin dashboard
└── static/               # Static assets
    ├── images/           # College images and logos
    └── css/              # Stylesheets
```

## Usage

### For Students
1. Visit the website homepage
2. Register for an account or login
3. Access the AI chatbot to ask questions about:
   - Course details and admissions
   - Campus facilities
   - Fee structure
   - Placement information
   - General inquiries

### For Administrators
1. Login with admin credentials
2. Access the admin dashboard
3. Monitor student interactions
4. View analytics and statistics
5. Export data for reports

## Deployment

### Vercel Deployment

Detailed deployment instructions are available in [VERCEL_SETUP.md](VERCEL_SETUP.md)

Quick steps:
1. Push your code to GitHub
2. Import project to Vercel
3. Configure environment variables in Vercel dashboard
4. Deploy!

### Important for Deployment
- ✅ Use PostgreSQL database (not SQLite) in production
- ✅ Set all environment variables in your hosting platform
- ✅ Ensure `.env` file is in `.gitignore` (it is by default)
- ✅ Never commit real API keys to GitHub

## Security Best Practices

1. **Never commit secrets**: `.env` file is gitignored by default
2. **Use strong passwords**: Change default admin password
3. **Secure API keys**: Keep your Gemini API key private
4. **HTTPS in production**: Always use HTTPS for production deployments
5. **Regular updates**: Keep dependencies updated

## API Keys & Credentials

> **⚠️ CRITICAL REMINDER**: All API keys in `.env.example` are **PLACEHOLDERS**.
> Replace them with your own valid keys from:
> - Google Gemini API: https://ai.google.dev/
> - Database: Your PostgreSQL provider (Neon, Supabase, etc.)

**Never share your real API keys publicly!**

## Troubleshooting

### Registration Error / Internal Server Error
- Ensure `google-generativeai` package is installed
- Check that `GEMINI_API_KEY` is valid and has available quota
- Verify database is initialized

### Chat Not Responding
- Verify Gemini API key is correct and active
- Check API quota limits at https://ai.dev/usage
- Ensure internet connection is stable

### Database Errors
- Run database initialization command
- Check `DATABASE_URL` format is correct
- Verify PostgreSQL server is running (if using PostgreSQL)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this project for your college!

## Contact

For questions or support, contact the college administration or create an issue on GitHub.

---

**Developed for Brahmdevdada Mane Institute of Technology, Solapur**