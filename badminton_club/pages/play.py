"""Play recommendations page - biweekly calendar for scheduling badminton sessions."""

import json
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
    days_since_monday = reference_date.weekday()
    monday = reference_date - timedelta(days=days_since_monday)
    return monday


def get_calendar_summary(start_date: date, end_date: date) -> dict:
    """Get interest counts for each date in the range.

    Interest = unique users + their guests (counted once per user per date).
    """
    try:
        # Subquery to get unique (date, user_id, num_guests) - guests are same for all user's entries on a date
        from sqlalchemy import distinct
        from sqlalchemy.orm import aliased

        # Get distinct users per date with their guest count
        # Since num_guests is the same for all of a user's entries on a date, we use max()
        subquery = (
            db_session.query(
                PlayRecommendation.date,
                PlayRecommendation.user_id,
                func.max(PlayRecommendation.num_guests).label("guests"),
            )
            .filter(
                PlayRecommendation.date >= start_date,
                PlayRecommendation.date <= end_date,
            )
            .group_by(PlayRecommendation.date, PlayRecommendation.user_id)
            .subquery()
        )

        # Now count users and sum guests per date
        results = (
            db_session.query(
                subquery.c.date,
                func.count(subquery.c.user_id).label("user_count"),
                func.coalesce(func.sum(subquery.c.guests), 0).label("guest_count"),
            )
            .group_by(subquery.c.date)
            .all()
        )

        # Total interest = unique users + their guests
        return {r.date: r.user_count + r.guest_count for r in results}
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


def create_day_card(
    day_date: date,
    interest_count: int,
    is_today: bool = False,
    is_selected: bool = False,
):
    """Create a card component for a single day."""
    badge_color = "primary" if interest_count > 0 else "secondary"

    # Determine border styling
    if is_selected:
        border_class = " border-warning border-3"
    elif is_today:
        border_class = " border-primary border-2"
    else:
        border_class = ""

    return html.Div(
        dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Small(
                            day_date.strftime("%a"), className="text-muted d-block"
                        ),
                        html.Strong(
                            day_date.strftime("%d"), style={"fontSize": "1.2rem"}
                        ),
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
            style={"cursor": "pointer", "minWidth": "70px"},
            className=f"shadow-sm h-100{border_class}",
        ),
        id={"type": "day-card", "date": day_date.isoformat()},
        n_clicks=0,
        className="mb-2 h-100",
    )


def create_calendar_grid(
    start_date: date, summaries: dict, selected_date_str: str = None
):
    """Create the 2-week calendar grid."""
    today = date.today()
    selected_date = date.fromisoformat(selected_date_str) if selected_date_str else None
    rows = []

    for week in range(2):
        week_cards = []
        for day in range(7):
            day_date = start_date + timedelta(days=week * 7 + day)
            interest_count = summaries.get(day_date, 0)
            is_today = day_date == today
            is_selected = day_date == selected_date
            week_cards.append(
                dbc.Col(
                    create_day_card(day_date, interest_count, is_today, is_selected),
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
                        # Time slots - multi-select checklist
                        html.Label("Time Slots", className="fw-bold mb-2"),
                        html.Div(
                            dbc.Checklist(
                                id="time-slot-checklist",
                                options=[
                                    {"label": ts, "value": ts} for ts in TIME_SLOTS
                                ],
                                value=[],
                                inline=True,
                                className="mb-3",
                            ),
                            style={"maxHeight": "150px", "overflowY": "auto"},
                        ),
                        html.Hr(),
                        # Locations - multi-select checklist
                        html.Label("Locations", className="fw-bold mb-2"),
                        html.Div(
                            dbc.Checklist(
                                id="location-checklist",
                                options=[],
                                value=[],
                                className="mb-3",
                            ),
                            style={"maxHeight": "150px", "overflowY": "auto"},
                        ),
                        html.Hr(),
                        # Number of guests
                        dbc.Row(
                            [
                                dbc.Label("Number of Guests", width=6),
                                dbc.Col(
                                    dbc.Input(
                                        id="num-guests-input",
                                        type="number",
                                        min=0,
                                        max=10,
                                        value=0,
                                        placeholder="0",
                                    ),
                                    width=6,
                                ),
                            ],
                            className="mb-3 align-items-center",
                        ),
                    ]
                ),
                dbc.ModalFooter(
                    [
                        dbc.Button(
                            "Delete All",
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
            size="lg",
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
        Input("selected-date", "data"),
    ],
    [State("calendar-start-date", "data")],
    prevent_initial_call=False,
)
def update_calendar(
    prev_clicks, next_clicks, save_clicks, delete_clicks, selected_date, start_date_str
):
    """Update the calendar grid based on navigation or data changes."""
    ctx = callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

    if start_date_str:
        start_date = date.fromisoformat(start_date_str)
    else:
        start_date = get_period_start(date.today())

    if triggered_id == "prev-period-btn":
        start_date = start_date - timedelta(days=14)
    elif triggered_id == "next-period-btn":
        start_date = start_date + timedelta(days=14)

    end_date = start_date + timedelta(days=13)
    summaries = get_calendar_summary(start_date, end_date)
    grid = create_calendar_grid(start_date, summaries, selected_date)
    period_label = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"

    return grid, period_label, start_date.isoformat()


@callback(
    [
        Output("recommendation-modal", "is_open"),
        Output("modal-date-header", "children"),
        Output("selected-date", "data"),
        Output("editing-recommendation-id", "data"),
        Output("time-slot-checklist", "value"),
        Output("location-checklist", "options"),
        Output("location-checklist", "value"),
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
        State("selected-date", "data"),
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
    current_selected_date,
):
    """Open/close the modal and populate with data."""
    ctx = callback_context
    if not ctx.triggered:
        return (no_update,) * 9

    triggered = ctx.triggered[0]
    triggered_id = triggered["prop_id"]
    triggered_value = triggered["value"]

    # Close modal on cancel, save, or delete - but keep selected date
    if any(
        btn in triggered_id
        for btn in [
            "cancel-modal-btn",
            "save-recommendation-btn",
            "delete-recommendation-btn",
        ]
    ):
        return False, "", no_update, None, [], [], [], 0, {"display": "none"}

    # For day-card clicks, check if an actual click occurred (value > 0)
    if "day-card" in triggered_id:
        # Check if this is a real click (not initial render)
        if triggered_value is None or triggered_value == 0:
            return (no_update,) * 9

        try:
            id_json = triggered_id.split(".")[0]
            id_dict = json.loads(id_json)
            clicked_date = id_dict["date"]
            selected_date = date.fromisoformat(clicked_date)

            # Get locations for dropdown
            locations = get_locations()
            location_options = [
                {"label": loc.name, "value": loc.id} for loc in locations
            ]

            # Get user's existing entries for this date to pre-select
            username = auth_manager.get_current_username()
            existing_time_slots = []
            existing_locations = []
            existing_guests = 0

            if username:
                user_id = get_user_id_by_username(username)
                if user_id:
                    existing = (
                        db_session.query(PlayRecommendation)
                        .filter(
                            PlayRecommendation.user_id == user_id,
                            PlayRecommendation.date == selected_date,
                        )
                        .all()
                    )
                    existing_time_slots = list(set(r.time_slot for r in existing))
                    existing_locations = list(set(r.location_id for r in existing))
                    if existing:
                        existing_guests = existing[0].num_guests

            show_delete = (
                {"display": "block"} if existing_time_slots else {"display": "none"}
            )

            return (
                True,
                f"Add Entry - {selected_date.strftime('%A, %B %d, %Y')}",
                clicked_date,
                None,
                existing_time_slots,
                location_options,
                existing_locations,
                existing_guests,
                show_delete,
            )
        except (json.JSONDecodeError, KeyError):
            pass

    # Handle edit button click
    if "edit-btn" in triggered_id:
        if triggered_value is None or triggered_value == 0:
            return (no_update,) * 9

        try:
            id_json = triggered_id.split(".")[0]
            id_dict = json.loads(id_json)
            rec_id = id_dict["id"]
            rec = (
                db_session.query(PlayRecommendation)
                .options(joinedload(PlayRecommendation.location))
                .filter(PlayRecommendation.id == rec_id)
                .first()
            )
            if rec:
                locations = get_locations()
                location_options = [
                    {"label": loc.name, "value": loc.id} for loc in locations
                ]

                # Get all entries for this user on this date
                username = auth_manager.get_current_username()
                user_id = get_user_id_by_username(username) if username else None

                existing_time_slots = [rec.time_slot]
                existing_locations = [rec.location_id]

                if user_id:
                    all_recs = (
                        db_session.query(PlayRecommendation)
                        .filter(
                            PlayRecommendation.user_id == user_id,
                            PlayRecommendation.date == rec.date,
                        )
                        .all()
                    )
                    existing_time_slots = list(set(r.time_slot for r in all_recs))
                    existing_locations = list(set(r.location_id for r in all_recs))

                return (
                    True,
                    f"Edit Entry - {rec.date.strftime('%A, %B %d, %Y')}",
                    rec.date.isoformat(),
                    rec_id,
                    existing_time_slots,
                    location_options,
                    existing_locations,
                    rec.num_guests,
                    {"display": "block"},
                )
        except (json.JSONDecodeError, KeyError, Exception):
            pass

    return (no_update,) * 9


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
        State("time-slot-checklist", "value"),
        State("location-checklist", "value"),
        State("num-guests-input", "value"),
    ],
    prevent_initial_call=True,
)
def save_recommendation(
    n_clicks, selected_date, rec_id, time_slots, location_ids, num_guests
):
    """Save or update recommendations - creates entries for all combinations."""
    if not n_clicks or not selected_date:
        return no_update, no_update, no_update

    if not time_slots or not location_ids:
        return "Please select at least one time slot and one location.", True, "warning"

    username = auth_manager.get_current_username()
    if not username:
        return "Please log in to save recommendations.", True, "danger"

    user_id = get_user_id_by_username(username)
    if not user_id:
        return "User not found.", True, "danger"

    try:
        rec_date = date.fromisoformat(selected_date)
        num_guests = int(num_guests) if num_guests else 0

        # Delete existing entries for this user/date first
        db_session.query(PlayRecommendation).filter(
            PlayRecommendation.user_id == user_id,
            PlayRecommendation.date == rec_date,
        ).delete()

        # Create new entries for all time_slot x location combinations
        count = 0
        for time_slot in time_slots:
            for location_id in location_ids:
                rec = PlayRecommendation(
                    user_id=user_id,
                    location_id=location_id,
                    date=rec_date,
                    time_slot=time_slot,
                    num_guests=num_guests,
                )
                db_session.add(rec)
                count += 1

        db_session.commit()
        return f"Saved {count} entries successfully!", True, "success"
    except Exception as e:
        db_session.rollback()
        return f"Error saving entries: {str(e)}", True, "danger"


@callback(
    [
        Output("play-alert", "children", allow_duplicate=True),
        Output("play-alert", "is_open", allow_duplicate=True),
        Output("play-alert", "color", allow_duplicate=True),
    ],
    [Input("delete-recommendation-btn", "n_clicks")],
    [State("selected-date", "data")],
    prevent_initial_call=True,
)
def delete_recommendation(n_clicks, selected_date):
    """Delete all recommendations for the selected date."""
    if not n_clicks or not selected_date:
        return no_update, no_update, no_update

    username = auth_manager.get_current_username()
    if not username:
        return "Please log in to delete recommendations.", True, "danger"

    user_id = get_user_id_by_username(username)
    if not user_id:
        return "User not found.", True, "danger"

    try:
        rec_date = date.fromisoformat(selected_date)
        count = (
            db_session.query(PlayRecommendation)
            .filter(
                PlayRecommendation.user_id == user_id,
                PlayRecommendation.date == rec_date,
            )
            .delete()
        )
        db_session.commit()
        return f"Deleted {count} entries for this date.", True, "success"
    except Exception as e:
        db_session.rollback()
        return f"Error deleting entries: {str(e)}", True, "danger"


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
    """Load the current user's entries grouped by date."""
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

    # Group by date
    by_date = {}
    for rec in recommendations:
        if rec.date not in by_date:
            by_date[rec.date] = []
        by_date[rec.date].append(rec)

    entries = []
    for rec_date in sorted(by_date.keys()):
        recs = by_date[rec_date]
        time_slots = sorted(set(r.time_slot for r in recs))
        locations = sorted(set(r.location.name for r in recs if r.location))
        guests = recs[0].num_guests if recs else 0

        entries.append(
            dbc.Card(
                dbc.CardBody(
                    dbc.Row(
                        [
                            dbc.Col(
                                html.Strong(rec_date.strftime("%a, %b %d")),
                                width=2,
                            ),
                            dbc.Col(
                                ", ".join(time_slots),
                                width=4,
                                className="text-muted small",
                            ),
                            dbc.Col(
                                ", ".join(locations),
                                width=3,
                                className="small",
                            ),
                            dbc.Col(
                                f"+{guests}" if guests else "",
                                width=1,
                                className="text-muted",
                            ),
                            dbc.Col(
                                dbc.Button(
                                    "Edit",
                                    id={"type": "edit-btn", "id": recs[0].id},
                                    color="outline-primary",
                                    size="sm",
                                ),
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
