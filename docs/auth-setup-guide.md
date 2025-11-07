# Authentication Setup Guide

## Overview

The authentication system has been fully implemented and is ready for use. This guide explains how to set up and use authentication in the MED13 Resource Library.

## What Was Fixed

### ✅ Login Endpoint Implementation
- **Before**: Placeholder that returned fake tokens
- **After**: Fully functional authentication using `AuthenticationService`
- **Location**: `src/routes/auth.py` (lines 209-255)

### ✅ Admin User Seed Script
- **Created**: `scripts/seed_admin_user.py`
- **Purpose**: Creates default admin user for initial system access
- **Makefile Target**: `make db-seed-admin`

## Quick Start

### Step 1: Ensure Database is Set Up

```bash
# Run migrations if not already done
make db-migrate

# Or create fresh database
alembic upgrade head
```

### Step 2: Create Admin User

```bash
# Using Makefile (recommended)
make db-seed-admin

# Or directly with Python
python scripts/seed_admin_user.py

# With custom credentials
python scripts/seed_admin_user.py \
  --email admin@example.com \
  --username admin \
  --password YourSecurePassword123! \
  --full-name "Your Name"
```

**Default Admin Credentials:**
- **Email**: `admin@med13.org`
- **Username**: `admin`
- **Password**: `admin123`
- **Role**: `ADMIN`
- **Status**: `ACTIVE`

⚠️ **Security Warning**: Change the default password immediately after first login!

### Step 3: Start the Backend

```bash
# Start FastAPI backend
make run-local

# Or directly
uvicorn src.main:app --reload --port 8080
```

### Step 4: Start Next.js Frontend

```bash
# Start Next.js admin interface
cd src/web
npm run dev

# Or using Makefile
make run-web
```

### Step 5: Login

1. Navigate to: `http://localhost:3000/auth/login`
2. Enter credentials:
   - Email: `admin@med13.org`
   - Password: `admin123`
3. Click "Sign In"
4. You'll be redirected to `/dashboard`

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Authenticate user and get tokens |
| POST | `/auth/register` | Register new user account |
| POST | `/auth/logout` | Logout and revoke session |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Get current user profile |
| PUT | `/auth/me` | Update current user profile |
| POST | `/auth/me/change-password` | Change password |
| POST | `/auth/forgot-password` | Request password reset |
| POST | `/auth/reset-password` | Reset password with token |
| POST | `/auth/verify-email/{token}` | Verify email address |

### Example: Login Request

```bash
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@med13.org",
    "password": "admin123"
  }'
```

**Response:**
```json
{
  "user": {
    "id": "uuid",
    "email": "admin@med13.org",
    "username": "admin",
    "full_name": "MED13 Administrator",
    "role": "admin",
    "status": "active",
    "email_verified": true
  },
  "access_token": "jwt_token_here",
  "refresh_token": "refresh_token_here",
  "expires_in": 900,
  "token_type": "bearer"
}
```

## User Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| `ADMIN` | System administrator | Full system access |
| `CURATOR` | Data curator | Can review and approve data |
| `RESEARCHER` | Researcher | Can view and search data |
| `VIEWER` | Read-only user | Can view public data only |

## Security Features

### ✅ Implemented
- **Password Hashing**: Bcrypt with proper salt rounds
- **JWT Tokens**: Secure access and refresh tokens
- **Session Management**: Tracks user sessions
- **Account Lockout**: Prevents brute force attacks
- **Email Verification**: Required for new accounts (can be bypassed for admin-created users)
- **Password Reset**: Secure token-based password reset
- **Audit Logging**: Tracks authentication events

### 🔄 In Progress
- Email sending (SMTP configuration needed for production)
- Multi-factor authentication (architecture ready)

## Troubleshooting

### Login Fails with "Invalid email or password"

1. **Check if user exists:**
   ```bash
   # Check database directly
   sqlite3 med13.db "SELECT email, username, role, status FROM users;"
   ```

2. **Verify password:**
   - Default password is `admin123`
   - Passwords are case-sensitive
   - Check for extra spaces

3. **Check account status:**
   - User must have `status = 'ACTIVE'`
   - User must have `email_verified = True` (or be admin-created)

### "Account is locked" Error

- Account is locked after multiple failed login attempts
- Wait 30 minutes or manually unlock in database:
  ```sql
  UPDATE users SET login_attempts = 0, locked_until = NULL WHERE email = 'admin@med13.org';
  ```

### Token Validation Fails

- Check if `NEXTAUTH_SECRET` is set in environment
- Verify JWT secret matches between backend and frontend
- Check token expiration (access tokens expire in 15 minutes)

### Database Connection Issues

- Ensure database migrations are up to date: `alembic upgrade head`
- Check database file exists: `ls -la med13.db`
- Verify database connection string in configuration

## Next Steps

After authentication is working:

1. **Change Default Password**: Use `/auth/me/change-password` endpoint
2. **Create Additional Users**: Use `/auth/register` or admin user management
3. **Configure Email**: Set up SMTP for email verification and password reset
4. **Set Up Production Secrets**: Configure `NEXTAUTH_SECRET` and JWT secrets

## Related Documentation

- `docs/Auth_PRD_FSD.md` - Complete authentication system specification
- `src/routes/auth.py` - Authentication API endpoints
- `src/application/services/authentication_service.py` - Authentication service implementation
- `src/web/lib/auth.ts` - NextAuth.js configuration
