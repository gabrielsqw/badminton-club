# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
- **Development mode**: `python badminton_club/app.py` (runs on port 8051, requires PostgreSQL)
- **Production (Docker Compose)**: `docker compose up --build` (runs on port 8000)

### Database Setup
- **Start database only**: `docker compose up db`
- **Run migrations**: `alembic upgrade head`
- **Create new migration**: `alembic revision --autogenerate -m "description"`
- **Rollback migration**: `alembic downgrade -1`

### Authentication
- Default credentials: `admin` / `password123`
- Environment variables:
  - `DATABASE_URL`: PostgreSQL connection string (default: `postgresql://badminton:badminton_secret@localhost:5432/badminton_club`)
  - `SECRET_KEY`: Set Flask session secret key (auto-generated if not set)
  - `ADMIN_USERNAME` / `ADMIN_PASSWORD_HASH`: Fallback auth when database unavailable

### Dependencies
- Install: `pip install -r requirements.txt` or `uv pip install -r requirements.txt`
- Core dependencies: Dash, dash-bootstrap-components, SQLAlchemy, Alembic, psycopg2-binary

## Architecture Overview

This is a Dash-based web application for a badminton club with database-backed authentication:

### Application Structure
- **app.py**: Main application entry point with UI components and routing
- **auth.py**: Authentication module handling credentials, session management, and security
- **database/**: Database module with SQLAlchemy setup
  - `__init__.py`: Database engine, session, and Base configuration
  - `models.py`: SQLAlchemy models (User)
- **pages/**: Directory containing individual page modules that auto-register with Dash
  - `home.py`: Landing page (path: "/")
  - `faq.py`: FAQ page (path: "/faq")
- **alembic/**: Database migrations
  - `versions/`: Migration scripts

### Key Architectural Patterns
- **Multi-page architecture**: Uses Dash's `page_registry` and `page_container` for automatic page discovery
- **Bootstrap styling**: Uses `dash-bootstrap-components` with DARKLY theme
- **Page registration**: Pages automatically register themselves using `register_page(__name__, path='...')`
- **Separation of concerns**: Authentication logic separated into dedicated `auth.py` module
- **Database-backed auth**: User credentials stored in PostgreSQL with SQLAlchemy ORM
- **Session management**: Flask sessions for authentication state with secure secret key
- **Docker Compose**: PostgreSQL + app containers with health checks and auto-migrations

### Authentication System
- **Database storage**: Users stored in PostgreSQL `users` table
- **Modular design**: Dedicated `AuthManager` class in `auth.py` handling all authentication logic
- **Secure password hashing**: Uses SHA256 for password verification with `hash_password()` utility
- **Fallback auth**: Falls back to environment variables if database unavailable
- **Session-based authentication**: Flask sessions with auto-generated secret keys
- **Clean API**: Methods like `verify_credentials()`, `login_user()`, `logout_user()`, `is_authenticated()`, `create_user()`

### Database Schema
- **users**: User authentication table
  - `id`: Primary key
  - `username`: Unique username (indexed)
  - `password_hash`: SHA256 hashed password
  - `email`: Optional email (unique, indexed)
  - `is_active`: Account active flag
  - `created_at`, `updated_at`: Timestamps

### Navigation
Navigation is automatically generated from registered pages using `page_registry.values()`, creating a responsive navbar with logout functionality when authenticated.
