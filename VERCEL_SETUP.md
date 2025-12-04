# Vercel Environment Variables Setup

This document lists all the environment variables you need to configure in your Vercel project dashboard.

## How to Add Environment Variables in Vercel

1. Go to your Vercel project dashboard
2. Navigate to **Settings** → **Environment Variables**
3. Add each variable below with its corresponding value

---

## Required Environment Variables

### 1. GEMINI_API_KEY
**Description:** Google Gemini API key for AI chat functionality  
**Where to get it:** https://aistudio.google.com/app/apikey  
**Example Value:** `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`  
**Environment:** Production, Preview, Development

```
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

---

### 2. DATABASE_URL
**Description:** PostgreSQL database connection string  
**Where to get it:** Create a PostgreSQL database on services like:
- Neon (https://neon.tech) - Recommended
- Supabase (https://supabase.com)
- Railway (https://railway.app)
- Vercel Postgres

**Format:** `postgresql://username:password@host:port/database`  
**Example Value:** `postgresql://user:pass@ep-cool-name-123.us-east-2.aws.neon.tech/collegemate?sslmode=require`  
**Environment:** Production, Preview, Development

```
DATABASE_URL=postgresql://username:password@host:port/database
```

**Important Notes:**
- The connection string should include `?sslmode=require` at the end
- Make sure the database is publicly accessible or whitelisted for Vercel IPs
- After deployment, visit `https://your-app.vercel.app/init-db` to initialize database tables

---

### 3. SECRET_KEY
**Description:** Flask session secret key for secure sessions  
**Where to get it:** Generate a random string (at least 32 characters)  
**Example Value:** `your-super-secret-key-here-make-it-very-long-and-random`  
**Environment:** Production, Preview, Development

**To generate a secure key:**
```python
# Run this in Python
import secrets
print(secrets.token_hex(32))
```

```
SECRET_KEY=your_generated_secret_key_here
```

---

## Optional Environment Variables (Currently Hardcoded)

### ADMIN_USERNAME
**Description:** Admin dashboard username  
**Current Value:** `admin` (hardcoded in app.py)  
**Recommended:** Add as environment variable for better security

```
ADMIN_USERNAME=admin
```

### ADMIN_PASSWORD
**Description:** Admin dashboard password  
**Current Value:** `Bmit@24` (hardcoded in app.py)  
**⚠️ SECURITY WARNING:** This should be changed to a hashed password or environment variable

```
ADMIN_PASSWORD=your_secure_password_here
```

---

## Summary Checklist

Before deploying to Vercel, ensure you have:

- [ ] **GEMINI_API_KEY** - Get from Google AI Studio
- [ ] **DATABASE_URL** - PostgreSQL connection string
- [ ] **SECRET_KEY** - Generate a random secure key
- [ ] Deploy your app to Vercel
- [ ] Visit `/init-db` route to initialize database tables
- [ ] Test login/register functionality
- [ ] Test AI chat functionality

---

## Step-by-Step Deployment Guide

### 1. Get Gemini API Key
1. Go to https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

### 2. Set Up PostgreSQL Database
**Using Neon (Recommended):**
1. Sign up at https://neon.tech
2. Create a new project
3. Copy the connection string from the dashboard
4. Make sure it includes `?sslmode=require`

### 3. Generate Secret Key
Run in Python terminal:
```python
import secrets
print(secrets.token_hex(32))
```

### 4. Add Variables to Vercel
1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Add all three variables:
   - `GEMINI_API_KEY`
   - `DATABASE_URL`
   - `SECRET_KEY`
3. Select "Production, Preview, and Development" for all

### 5. Deploy & Initialize
1. Deploy your app (Vercel auto-deploys from GitHub)
2. Visit `https://your-app.vercel.app/init-db` to create database tables
3. Test by registering a new user!

---

## Troubleshooting

**Error: "No API key provided"**
- Make sure `GEMINI_API_KEY` is set in Vercel
- Redeploy after adding the variable

**Error: "Database connection failed"**
- Check if `DATABASE_URL` is correct
- Ensure the database is publicly accessible
- Test the connection string locally first

**Error: "Internal Server Error"**
- Check Vercel function logs for details
- Make sure all three environment variables are set
- Verify the database tables were created via `/init-db`

---

## Security Best Practices

1. **Never commit `.env` to Git** - Already protected by `.gitignore`
2. **Use strong passwords** - Change the default admin password
3. **Rotate API keys regularly** - Update keys every few months
4. **Use different keys for dev/prod** - Keep development and production separate
5. **Enable database SSL** - Always use `?sslmode=require` in DATABASE_URL

---

**Last Updated:** 2025-12-04
**Project:** CollegeMate - AI College Assistant
