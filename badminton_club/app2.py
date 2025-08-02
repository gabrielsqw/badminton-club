import logging

from dash import Dash, dcc, html, page_container, page_registry
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from flask import session
import dash

logging.basicConfig(level="DEBUG")
logger = logging.getLogger(__name__)
# Initialize the Dash app
app = Dash(
    __name__,
    # use_pages=True,
    external_stylesheets=[dbc.themes.DARKLY],
)
app.title = "Gab's Badminton Group"

server = app.server

# Flask server configuration for a secret key (required for session storage)
server.secret_key = "your-secret-key"  # Replace with a secure key


# Define hardcoded credentials (for simplicity)
VALID_USERNAME = "admin"
VALID_PASSWORD = "password123"


# Login form layout
def login_layout():
    return dbc.Container(
        [
            dbc.Row(dbc.Col(html.H2("Login to Your Account"), className="mb-3")),
            dbc.Row(
                dbc.Col(
                    dbc.Input(id="username", placeholder="Username", type="text"),
                    className="mb-3",
                )
            ),
            dbc.Row(
                dbc.Col(
                    dbc.Input(id="password", placeholder="Password", type="password"),
                    className="mb-3",
                )
            ),
            dbc.Row(
                dbc.Col(
                    dbc.Button(
                        "Login", id="login-button", color="primary", className="mb-3"
                    ),
                )
            ),
            html.Div(id="login-output", className="text-danger"),
        ],
        fluid=True,
        className="mt-5",
        style={"display": "block"},
        id="login-layout",
    )


# Main app layout when logged in
def app_layout():
    return dbc.Container(
        [
            dbc.Nav(
                [
                    dbc.NavItem(
                        dcc.Link(page["name"], href=page["path"], className="nav-link")
                    )
                    for page in page_registry.values()
                ],
                pills=True,
                className="mb-4",
            ),
            dbc.Card(
                dbc.CardBody(
                    page_container,
                    style={"padding": "20px"},
                ),
                className="shadow-sm",
            ),
            dbc.Button("Logout", id="logout-button", className="mt-4", color="danger"),
        ],
        fluid=True,
        style={"padding": "20px", "display": "none"},
        id="app-layout",
    )


# Callback for managing which layout to show
@app.callback(
    [
        Output("app-layout", "style"),
        Output("login-layout", "style"),
        Output("logout-button", "n_clicks"),
        Output("login-button", "n_clicks"),
    ],
    [
        Input("logout-button", "n_clicks"),
        Input("login-button", "n_clicks"),
    ],
    [
        State("username", "value"),
        State("password", "value"),
        State("app-layout", "style"),
        State("login-layout", "style"),
    ],
)
def display_page(
    logout_click, login_click, username, password, app_state, login_state
):
    logger.warning((login_click, logout_click))
    # If user clicked logout
    if logout_click:
        logger.warning("logged out")
        session["logged_in"] = False
        app_state["display"] = "none"
        login_state["display"] = "block"
        logger.warning((app_state, login_state))
        return app_state, login_state, 0, 0

    # If user is logged in, show the app layout
    if session.get("logged_in"):
        logger.warning("logged in")
        del app_state["display"]
        login_state["display"] = "none"
        logger.warning((app_state, login_state))
        return app_state, login_state, 0, 0

    # Handle login attempt
    if login_click:
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            logger.warning("login click valid")
            session["logged_in"] = True
            del app_state["display"]
            login_state["display"] = "none"
            logger.warning((app_state, login_state))
            return app_state, login_state, 0, 0
        else:
            logger.warning("login click invalid")
            logger.warning((app_state, login_state))
            return app_state, login_state, 0, 0
    # Default to login page
    logger.warning("nothing done")
    logger.warning((app_state, login_state))
    return app_state, login_state, 0, 0


# Layout with login and pages
app.layout = html.Div(
    [
        login_layout(),
        app_layout(),
    ]
)

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
