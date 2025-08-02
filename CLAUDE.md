# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
- **Development mode**: `python badminton_club/app.py` (runs on port 8051)
- **Alternative app with auth**: `python badminton_club/app2.py` (includes login functionality)
- **Production (Docker)**: `docker build -t badminton-club . && docker run -p 8000:8000 badminton-club`

### Dependencies
- Install: `pip install -r requirements.txt` or `uv pip install -r requirements.txt`
- Core dependencies: Dash, dash-bootstrap-components

## Architecture Overview

This is a Dash-based web application for a badminton club with two main application variants:

### Application Structure
- **app.py**: Main application without authentication - simple multi-page Dash app
- **app2.py**: Extended version with session-based login authentication (admin/password123)
- **pages/**: Directory containing individual page modules that auto-register with Dash
  - `home.py`: Landing page (path: "/")
  - `faq.py`: FAQ page (path: "/faq")

### Key Architectural Patterns
- **Multi-page architecture**: Uses Dash's `page_registry` and `page_container` for automatic page discovery
- **Bootstrap styling**: Uses `dash-bootstrap-components` with DARKLY theme
- **Page registration**: Pages automatically register themselves using `register_page(__name__, path='...')`
- **Session management** (app2.py only): Flask sessions for authentication state
- **Containerization**: Docker setup using Python 3.12-slim with gunicorn for production

### Navigation
Navigation is automatically generated from registered pages using `page_registry.values()`, creating a responsive nav bar with Bootstrap pills styling.

### Authentication (app2.py)
- Hardcoded credentials for demo purposes
- Session-based login with Flask sessions
- Conditional layout rendering based on authentication state
- Login/logout functionality with state management via Dash callbacks