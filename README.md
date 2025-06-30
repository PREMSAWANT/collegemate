# CollegeMate - BMIT Solapur AI Assistant

CollegeMate is an AI-powered assistant for Brahmdevdada Mane Institute of Technology, Solapur. It helps students with admissions inquiries, course information, and campus facilities.

## Features

- AI-powered chat interface
- Voice interaction support
- Course information and admission details
- Campus facilities information
- Admin dashboard for monitoring interactions
- User registration and authentication
- Document management system

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- OpenAI API key
- SMTP server credentials (for email notifications)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/collegemate.git
cd collegemate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Update the following variables in `.env`:
     - `SECRET_KEY`: Your Flask secret key
     - `OPENAI_API_KEY`: Your OpenAI API key (recommended: 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)
     - `SMTP_USERNAME`: Your email address
     - `