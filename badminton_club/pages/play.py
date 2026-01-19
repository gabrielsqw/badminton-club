"""Play recommendations page - biweekly calendar for scheduling badminton sessions."""

from datetime import date, timedelta
from dash import html, dcc, callback, register_page, callback_context, no_update, ALL
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from badminton_club.database import db_session
from badminton_club.database.models import (
    User,
    Location,
    PlayRecommendation,
    TIME_SLOTS,
)
from badminton_club.auth import auth_manager

register_page(__name__, path="/play", name="Play")


def get_period_start(reference_date: date) -> date:
    """Get the Monday that starts the 2-week period containing the reference date."""
    # Find the Monday of the current week
    days_since_monday = reference_date.weekday()
    monday = reference_date - timedelta(days=days_since_monday)
    return monday


def get_calendar_summary(start_date: date, end_date: date) -> dict:
    """Get interest counts for each date in the range."""
    try:
        results = (
            db_session.query(
                PlayRecommendation.date,
                func.count(PlayRecommendation.id).label("recommendation_count"),
                func.coalesce(func.sum(PlayRecommendation.num_guests), 0).label(
                    "guest_count"
                ),
            )
            .filter(
                PlayRecommendation.date >= start_date,
                PlayRecommendation.date <= end_date,
            )
            .group_by(PlayRecommendation.date)
            .all()
        )
        # Total interest = recommendations + guests (each recommendation = 1 person)
        return {r.date: r.recommendation_count + r.guest_count for r in results}
    except Exception:
        return {}


def get_user_id_by_username(username: str) -> int | None:
    """Get user ID from username."""
    try:
        user = db_session.query(User).filter(User.username == username).first()
        return user.id if user else None
    except Exception:
        return None


def get_user_recommendations(user_id: int) -> list:
    """Get all recommendations for a specific user."""
    try:
        return (
            db_session.query(PlayRecommendation)
            .filter(PlayRecommendation.user_id == user_id)
            .options(joinedload(PlayRecommendation.location))
            .order_by(PlayRecommendation.date, PlayRecommendation.time_slot)
            .all()
        )
    except Exception:
        return []


def get_locations() -> list:
    """Get all active locations."""
    try:
        return (
            db_session.query(Location)
            .filter(Location.is_active == True)
            .order_by(Location.name)
            .all()
        )
    except Exception:
        return []


def create_day_card(day_date: date, interest_count: int, is_today: bool = False):
    """Create a card component for a single day."""
    border_class = " border-primary border-2" if is_today else ""
    badge_color = "primary" if interest_count > 0 else "secondary"

    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.Small(day_date.strftime("%a"), className="text-muted d-block"),
                    html.Strong(day_date.strftime("%d"), style={"fontSize": "1.2rem"}),
                ],
                className="text-center p-2",
            ),
            dbc.CardBody(
                dbc.Badge(
                    f"{interest_count}",
                    color=badge_color,
                    className="rounded-pill",
                    title=f"{interest_count} people interested",
                ),
                className="text-center p-2",
            ),
        ],
        id={"type": "day-card", "date": day_date.isoformat()},
        style={"cursor": "pointer", "minWidth": "70px"},
        className=f"mb-2 shadow-sm h-100{border_class}",
    )


def create_calendar_grid(start_date: date, summaries: dict):
    """Create the 2-week calendar grid."""
    today = date.today()
    rows = []

    for week in range(2):
        week_cards = []
        for day in range(7):
            day_date = start_date + timedelta(days=week * 7 + day)
            interest_count = summaries.get(day_date, 0)
            is_today = day_date == today
            week_cards.append(
                dbc.Col(
                    create_day_card(day_date, interest_count, is_today),
                    className="px-1",
                )
            )
        rows.append(dbc.Row(week_cards, className="g-2 mb-2"))

    return rows


# Layout
layout = dbc.Container(
    [
        # Stores for state management
        dcc.Store(
            id="calendar-start-date", data=get_period_start(date.today()).isoformat()
        ),
        dcc.Store(id="selected-date", data=None),
        dcc.Store(id="editing-recommendation-id", data=None),
        # Alert for notifications
        dbc.Alert(
            id="play-alert",
            is_open=False,
            duration=4000,
            style={
                "position": "fixed",
                "top": "20px",
                "left": "50%",
                "transform": "translateX(-50%)",
                "zIndex": "9999",
                "width": "400px",
            },
        ),
        # Header
        html.H2("Play Recommendations", className="mb-4"),
        html.P(
            "Click on a date to add your availability. See when others want to play!",
            className="text-muted mb-4",
        ),
        # Navigation
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button(
                        "< Prev",
                        id="prev-period-btn",
                        color="outline-light",
                        size="sm",
                    ),
                    width="auto",
                ),
                dbc.Col(
                    html.H5(id="period-label", className="mb-0 text-center"),
                    className="d-flex align-items-center justify-content-center",
                ),
                dbc.Col(
                    dbc.Button(
                        "Next >",
                        id="next-period-btn",
                        color="outline-light",
                        size="sm",
                    ),
                    width="auto",
                ),
            ],
            className="mb-4 justify-content-between align-items-center",
        ),
        # Calendar grid container
        html.Div(id="calendar-grid"),
        html.Hr(className="my-4"),
        # My Entries section
        html.H4("My Entries", className="mb-3"),
        html.Div(id="my-entries-container"),
        # Add/Edit Modal
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle(id="modal-date-header")),
                dbc.ModalBody(
                    [
                        dbc.Form(
                            [
                                dbc.Row(
                                    [
                                        dbc.Label("Time Slot", width=4),
                                        dbc.Col(
                                            dbc.Select(
                                                id="time-slot-select",
                                                options=[
                                                    {"label": ts, "value": ts}
                                                    for ts in TIME_SLOTS
                                                ],
                                            ),
                                            width=8,
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Label("Location", width=4),
                                        dbc.Col(
                                            dbc.Select(
                                                id="location-select",
                                                options=[],
                                            ),
                                            width=8,
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                                dbc.Row(
                                    [
                                        dbc.Label("Guests", width=4),
                                        dbc.Col(
                                            dbc.Input(
                                                id="num-guests-input",
                                                type="number",
                                                min=0,
                                                max=10,
                                                value=0,
                                                placeholder="Number of guests",
                                            ),
                                            width=8,
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                            ]
                        )
                    ]
                ),
                dbc.ModalFooter(
                    [
                        dbc.Button(
                            "Delete",
                            id="delete-recommendation-btn",
                            color="danger",
                            className="me-auto",
                            style={"display": "none"},
                        ),
                        dbc.Button("Cancel", id="cancel-modal-btn", color="secondary"),
                        dbc.Button(
                            "Save", id="save-recommendation-btn", color="primary"
                        ),
                    ]
                ),
            ],
            id="recommendation-modal",
            is_open=False,
        ),
    ],
    className="py-4",
)


@callback(
    [
        Output("calendar-grid", "children"),
        Output("period-label", "children"),
        Output("calendar-start-date", "data"),
    ],
    [
        Input("prev-period-btn", "n_clicks"),
        Input("next-period-btn", "n_clicks"),
        Input("save-recommendation-btn", "n_clicks"),
        Input("delete-recommendation-btn", "n_clicks"),
    ],
    [State("calendar-start-date", "data")],
    prevent_initial_call=False,
)
def update_calendar(
    prev_clicks, next_clicks, save_clicks, delete_clicks, start_date_str
):
    """Update the calendar grid based on navigation or data changes."""
    ctx = callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

    # Parse the start date
    if start_date_str:
        start_date = date.fromisoformat(start_date_str)
    else:
        start_date = get_period_start(date.today())

    # Handle navigation
    if triggered_id == "prev-period-btn":
        start_date = start_date - timedelta(days=14)
    elif triggered_id == "next-period-btn":
        start_date = start_date + timedelta(days=14)

    end_date = start_date + timedelta(days=13)

    # Get summaries for the period
    summaries = get_calendar_summary(start_date, end_date)

    # Create calendar grid
    grid = create_calendar_grid(start_date, summaries)

    # Format period label
    period_label = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"

    return grid, period_label, start_date.isoformat()


@callback(
    [
        Output("recommendation-modal", "is_open"),
        Output("modal-date-header", "children"),
        Output("selected-date", "data"),
        Output("editing-recommendation-id", "data"),
        Output("time-slot-select", "value"),
        Output("location-select", "options"),
        Output("location-select", "value"),
        Output("num-guests-input", "value"),
        Output("delete-recommendation-btn", "style"),
    ],
    [
        Input({"type": "day-card", "date": ALL}, "n_clicks"),
        Input({"type": "edit-btn", "id": ALL}, "n_clicks"),
        Input("cancel-modal-btn", "n_clicks"),
        Input("save-recommendation-btn", "n_clicks"),
        Input("delete-recommendation-btn", "n_clicks"),
    ],
    [
        State({"type": "day-card", "date": ALL}, "id"),
        State({"type": "edit-btn", "id": ALL}, "id"),
        State("recommendation-modal", "is_open"),
    ],
    prevent_initial_call=True,
)
def toggle_modal(
    day_clicks,
    edit_clicks,
    cancel_clicks,
    save_clicks,
    delete_clicks,
    day_ids,
    edit_ids,
    is_open,
):
    """Open/close the modal and populate with data."""
    ctx = callback_context
    if not ctx.triggered:
        return (
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
        )

    triggered = ctx.triggered[0]
    triggered_id = triggered["prop_id"]

    # Close modal on cancel, save, or delete
    if any(
        btn in triggered_id
        for btn in [
            "cancel-modal-btn",
            "save-recommendation-btn",
            "delete-recommendation-btn",
        ]
    ):
        return False, "", None, None, None, [], None, 0, {"display": "none"}

    # Get locations for dropdown
    locations = get_locations()
    location_options = [{"label": loc.name, "value": loc.id} for loc in locations]
    default_location = locations[0].id if locations else None

    # Handle day card click (new entry)
    if "day-card" in triggered_id:
        # Find which card was clicked
        for i, click in enumerate(day_clicks):
            if click:
                clicked_date = day_ids[i]["date"]
                selected_date = date.fromisoformat(clicked_date)
                return (
                    True,
                    f"Add Entry - {selected_date.strftime('%A, %B %d, %Y')}",
                    clicked_date,
                    None,
                    TIME_SLOTS[0],
                    location_options,
                    default_location,
                    0,
                    {"display": "none"},
                )

    # Handle edit button click
    if "edit-btn" in triggered_id:
        for i, click in enumerate(edit_clicks):
            if click:
                rec_id = edit_ids[i]["id"]
                try:
                    rec = (
                        db_session.query(PlayRecommendation)
                        .options(joinedload(PlayRecommendation.location))
                        .filter(PlayRecommendation.id == rec_id)
                        .first()
                    )
                    if rec:
                        return (
                            True,
                            f"Edit Entry - {rec.date.strftime('%A, %B %d, %Y')}",
                            rec.date.isoformat(),
                            rec_id,
                            rec.time_slot,
                            location_options,
                            rec.location_id,
                            rec.num_guests,
                            {"display": "block"},
                        )
                except Exception:
                    pass

    return (
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
    )


@callback(
    [
        Output("play-alert", "children"),
        Output("play-alert", "is_open"),
        Output("play-alert", "color"),
    ],
    [Input("save-recommendation-btn", "n_clicks")],
    [
        State("selected-date", "data"),
        State("editing-recommendation-id", "data"),
        State("time-slot-select", "value"),
        State("location-select", "value"),
        State("num-guests-input", "value"),
    ],
    prevent_initial_call=True,
)
def save_recommendation(
    n_clicks, selected_date, rec_id, time_slot, location_id, num_guests
):
    """Save or update a recommendation."""
    if not n_clicks or not selected_date or not time_slot or not location_id:
        return no_update, no_update, no_update

    username = auth_manager.get_current_username()
    if not username:
        return "Please log in to save recommendations.", True, "danger"

    user_id = get_user_id_by_username(username)
    if not user_id:
        return "User not found.", True, "danger"

    try:
        rec_date = date.fromisoformat(selected_date)
        num_guests = int(num_guests) if num_guests else 0

        if rec_id:
            # Update existing
            rec = (
                db_session.query(PlayRecommendation)
                .filter(PlayRecommendation.id == rec_id)
                .first()
            )
            if rec and rec.user_id == user_id:
                rec.date = rec_date
                rec.time_slot = time_slot
                rec.location_id = location_id
                rec.num_guests = num_guests
                db_session.commit()
                return "Entry updated successfully!", True, "success"
            return "Entry not found or access denied.", True, "danger"
        else:
            # Create new
            rec = PlayRecommendation(
                user_id=user_id,
                location_id=location_id,
                date=rec_date,
                time_slot=time_slot,
                num_guests=num_guests,
            )
            db_session.add(rec)
            db_session.commit()
            return "Entry added successfully!", True, "success"
    except Exception as e:
        db_session.rollback()
        if "uq_user_date_time_location" in str(e):
            return (
                "You already have an entry for this date, time, and location.",
                True,
                "warning",
            )
        return f"Error saving entry: {str(e)}", True, "danger"


@callback(
    [
        Output("play-alert", "children", allow_duplicate=True),
        Output("play-alert", "is_open", allow_duplicate=True),
        Output("play-alert", "color", allow_duplicate=True),
    ],
    [Input("delete-recommendation-btn", "n_clicks")],
    [State("editing-recommendation-id", "data")],
    prevent_initial_call=True,
)
def delete_recommendation(n_clicks, rec_id):
    """Delete a recommendation."""
    if not n_clicks or not rec_id:
        return no_update, no_update, no_update

    username = auth_manager.get_current_username()
    if not username:
        return "Please log in to delete recommendations.", True, "danger"

    user_id = get_user_id_by_username(username)
    if not user_id:
        return "User not found.", True, "danger"

    try:
        rec = (
            db_session.query(PlayRecommendation)
            .filter(PlayRecommendation.id == rec_id)
            .first()
        )
        if rec and rec.user_id == user_id:
            db_session.delete(rec)
            db_session.commit()
            return "Entry deleted successfully!", True, "success"
        return "Entry not found or access denied.", True, "danger"
    except Exception as e:
        db_session.rollback()
        return f"Error deleting entry: {str(e)}", True, "danger"


@callback(
    Output("my-entries-container", "children"),
    [
        Input("calendar-start-date", "data"),
        Input("save-recommendation-btn", "n_clicks"),
        Input("delete-recommendation-btn", "n_clicks"),
    ],
    prevent_initial_call=False,
)
def load_user_entries(start_date_str, save_clicks, delete_clicks):
    """Load the current user's entries."""
    username = auth_manager.get_current_username()
    if not username:
        return dbc.Alert("Please log in to see your entries.", color="info")

    user_id = get_user_id_by_username(username)
    if not user_id:
        return dbc.Alert("User not found.", color="warning")

    recommendations = get_user_recommendations(user_id)

    if not recommendations:
        return dbc.Alert(
            "You haven't added any entries yet. Click on a date above to add one!",
            color="info",
        )

    entries = []
    for rec in recommendations:
        location_name = rec.location.name if rec.location else "Unknown"
        entries.append(
            dbc.Card(
                dbc.CardBody(
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Strong(rec.date.strftime("%a, %b %d")),
                                    html.Span(
                                        f" | {rec.time_slot}", className="text-muted"
                                    ),
                                ],
                                width=4,
                            ),
                            dbc.Col(location_name, width=3),
                            dbc.Col(
                                (
                                    f"{rec.num_guests} guest(s)"
                                    if rec.num_guests
                                    else "No guests"
                                ),
                                width=3,
                                className="text-muted",
                            ),
                            dbc.Col(
                                [
                                    dbc.Button(
                                        "Edit",
                                        id={"type": "edit-btn", "id": rec.id},
                                        color="outline-primary",
                                        size="sm",
                                        className="me-1",
                                    ),
                                ],
                                width=2,
                                className="text-end",
                            ),
                        ],
                        className="align-items-center",
                    )
                ),
                className="mb-2",
            )
        )

    return entries
