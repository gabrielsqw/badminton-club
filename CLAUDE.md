# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
- **Development mode**: `python badminton_club/app.py` (runs on port 8051 with authentication)
- **Production (Docker)**: `docker build -t badminton-club . && docker run -p 8000:8000 badminton-club`

### Authentication
- Default credentials: `admin` / `password123`
- Override with environment variables:
  - `ADMIN_USERNAME`: Set custom username
  - `ADMIN_PASSWORD_HASH`: Set SHA256 hash of password
  - `SECRET_KEY`: Set Flask session secret key (auto-generated if not set)

### Dependencies
- Install: `pip install -r requirements.txt` or `uv pip install -r requirements.txt`
- Core dependencies: Dash, dash-bootstrap-components

## Architecture Overview

This is a Dash-based web application for a badminton club with secure authentication:

### Application Structure
- **app.py**: Main application with integrated authentication system
- **pages/**: Directory containing individual page modules that auto-register with Dash
  - `home.py`: Landing page (path: "/")
  - `faq.py`: FAQ page (path: "/faq")

### Key Architectural Patterns
- **Multi-page architecture**: Uses Dash's `page_registry` and `page_container` for automatic page discovery
- **Bootstrap styling**: Uses `dash-bootstrap-components` with DARKLY theme
- **Page registration**: Pages automatically register themselves using `register_page(__name__, path='...')`
- **Session management**: Flask sessions for authentication state with secure secret key
- **Containerization**: Docker setup using Python 3.12-slim with gunicorn for production

### Authentication System
- **Secure password hashing**: Uses SHA256 for password verification
- **Environment-based configuration**: Credentials and secrets configurable via environment variables
- **Session-based authentication**: Flask sessions with auto-generated secret keys
- **Conditional layout rendering**: Login screen vs main application based on authentication state
- **Responsive UI**: Bootstrap-styled login form with proper validation feedback

### Navigation
Navigation is automatically generated from registered pages using `page_registry.values()`, creating a responsive navbar with logout functionality when authenticated.