"""Home page with upcoming play sessions summary."""

from datetime import date, timedelta
from dash import html, register_page
import dash_bootstrap_components as dbc
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from badminton_club.database import db_session
from badminton_club.database.models import User, PlayRecommendation

register_page(__name__, path="/")


def get_upcoming_potential_sessions():
    """Get upcoming potential play sessions grouped by date with member info.

    Returns list of (date, [(username, num_guests), ...]) sorted by date.
    """
    try:
        today = date.today()
        end_date = today + timedelta(days=14)  # Next 2 weeks

        # Get unique (date, user_id, num_guests) combinations
        results = (
            db_session.query(
                PlayRecommendation.date,
                User.username,
                func.max(PlayRecommendation.num_guests).label("guests"),
            )
            .join(User, PlayRecommendation.user_id == User.id)
            .filter(
                PlayRecommendation.date >= today,
                PlayRecommendation.date <= end_date,
            )
            .group_by(PlayRecommendation.date, User.username)
            .order_by(PlayRecommendation.date, User.username)
            .all()
        )

        # Group by date
        by_date = {}
        for rec_date, username, guests in results:
            if rec_date not in by_date:
                by_date[rec_date] = []
            by_date[rec_date].append((username, guests))

        return sorted(by_date.items())
    except Exception:
        return []


def format_members(members):
    """Format list of (username, guests) into readable string."""
    parts = []
    for username, guests in members:
        if guests and guests > 0:
            parts.append(f"{username} (+{guests})")
        else:
            parts.append(username)
    return ", ".join(parts)


def build_upcoming_section():
    """Build the upcoming sessions section."""
    sessions = get_upcoming_potential_sessions()

    if not sessions:
        return dbc.Alert(
            "No upcoming potential sessions (because there's no votes!). Visit the Play page to add your availability!",
            color="info",
        )

    cards = []
    for session_date, members in sessions:
        cards.append(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Strong(
                            session_date.strftime("%a, %b %d"),
                            className="d-block mb-1",
                        ),
                        html.Span(
                            format_members(members),
                            className="text-muted",
                        ),
                    ]
                ),
                className="mb-2",
            )
        )

    return html.Div(cards)


layout = html.Div(
    [
        html.H2("Gab's badminton group"),
        html.P("Welcome!!!"),
        html.Hr(className="my-4"),
        html.H4("Upcoming Potential Sessions", className="mb-3"),
        build_upcoming_section(),
    ]
)
