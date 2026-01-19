from dash import (
    Dash,
    dcc,
    html,
    page_container,
    page_registry,
    Input,
    Output,
    State,
    callback,
)
import dash_bootstrap_components as dbc
from badminton_club.auth import auth_manager
from badminton_club.database import db_session

# Initialize the Dash app with a Bootstrap theme
app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.DARKLY],
)
app.title = "Gab's badminton group"

# Flask server configuration
server = app.server
server.secret_key = auth_manager.get_secret_key()


@server.teardown_appcontext
def shutdown_session(exception=None):
    """Clean up database session after each request."""
    db_session.remove()


# --- Layout Components ---

ALERT_STYLE = {
    "position": "fixed",
    "top": "20px",
    "left": "50%",
    "transform": "translateX(-50%)",
    "z-index": "9999",
    "width": "400px",
}

login_form = html.Div(
    dbc.Form(
        [
            dbc.Row(
                [
                    dbc.Label("Username", html_for="username", width=3),
                    dbc.Col(
                        dbc.Input(
                            type="text",
                            id="username",
                            placeholder="Enter username",
                            required=True,
                        ),
                        width=9,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Label("Password", html_for="password", width=3),
                    dbc.Col(
                        dbc.Input(
                            type="password",
                            id="password",
                            placeholder="Enter password",
                            required=True,
                        ),
                        width=9,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                dbc.Col(
                    dbc.Button(
                        "Login",
                        id="login-btn",
                        color="primary",
                        size="lg",
                        className="w-100",
                    ),
                    width={"size": 6, "offset": 3},
                )
            ),
        ]
    ),
    id="login-form",
)

register_form = html.Div(
    dbc.Form(
        [
            dbc.Row(
                [
                    dbc.Label("Username", html_for="reg-username", width=3),
                    dbc.Col(
                        dbc.Input(
                            type="text",
                            id="reg-username",
                            placeholder="Choose a username",
                            required=True,
                        ),
                        width=9,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Label("Email", html_for="reg-email", width=3),
                    dbc.Col(
                        dbc.Input(
                            type="email",
                            id="reg-email",
                            placeholder="Enter email (optional)",
                        ),
                        width=9,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Label("Password", html_for="reg-password", width=3),
                    dbc.Col(
                        dbc.Input(
                            type="password",
                            id="reg-password",
                            placeholder="Choose a password",
                            required=True,
                        ),
                        width=9,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Label("Confirm", html_for="reg-password-confirm", width=3),
                    dbc.Col(
                        dbc.Input(
                            type="password",
                            id="reg-password-confirm",
                            placeholder="Confirm password",
                            required=True,
                        ),
                        width=9,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                dbc.Col(
                    dbc.Button(
                        "Register",
                        id="register-btn",
                        color="success",
                        size="lg",
                        className="w-100",
                    ),
                    width={"size": 6, "offset": 3},
                )
            ),
        ]
    ),
    id="register-form",
    style={"display": "none"},
)

auth_tabs = dbc.Tabs(
    [
        dbc.Tab(label="Login", tab_id="login-tab"),
        dbc.Tab(label="Register", tab_id="register-tab"),
    ],
    id="auth-tabs",
    active_tab="login-tab",
)

auth_card = dbc.Card(
    [
        dbc.CardHeader(auth_tabs),
        dbc.CardBody([login_form, register_form]),
    ],
    className="shadow",
)

login_container = dbc.Container(
    [
        dbc.Row(
            dbc.Col(auth_card, width={"size": 6, "offset": 3}),
            className="min-vh-100 d-flex align-items-center",
        ),
        dbc.Alert(id="login-alert", is_open=False, dismissable=True, style=ALERT_STYLE),
    ],
    fluid=True,
    id="login-container",
)

navbar = dbc.Navbar(
    [
        dbc.Nav(
            [
                dbc.NavItem(
                    dcc.Link(page["name"], href=page["path"], className="nav-link")
                )
                for page in page_registry.values()
            ],
            pills=True,
            className="me-auto",
        ),
        dbc.Nav(
            [
                dbc.NavItem(
                    html.Span(
                        id="username-display",
                        className="navbar-text me-3",
                        style={"color": "white"},
                    )
                ),
                dbc.NavItem(
                    dbc.Button(
                        "Logout", id="logout-btn", color="outline-light", size="sm"
                    )
                ),
            ]
        ),
    ],
    color="dark",
    dark=True,
    className="mb-4",
)

main_container = dbc.Container(
    [
        navbar,
        dbc.Card(
            dbc.CardBody(page_container, style={"padding": "20px"}),
            className="shadow-sm",
        ),
        dbc.Alert(
            id="alert-message", is_open=False, dismissable=True, style=ALERT_STYLE
        ),
    ],
    fluid=True,
    style={"padding": "20px"},
    id="main-container",
)

# --- App Layout ---

app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        login_container,
        main_container,
    ]
)


# --- Callbacks ---


@callback(
    [
        Output("login-container", "style"),
        Output("main-container", "style"),
        Output("username-display", "children"),
    ],
    [Input("url", "pathname")],
)
def display_page(pathname):
    if auth_manager.is_authenticated():
        username = auth_manager.get_current_username()
        username_text = f"Welcome, {username}" if username else "Welcome"
        return {"display": "none"}, {"padding": "20px"}, username_text
    return {}, {"display": "none"}, ""


@callback(
    [
        Output("url", "pathname", allow_duplicate=True),
        Output("login-alert", "children", allow_duplicate=True),
        Output("login-alert", "color", allow_duplicate=True),
        Output("login-alert", "is_open", allow_duplicate=True),
        Output("alert-message", "children", allow_duplicate=True),
        Output("alert-message", "color", allow_duplicate=True),
        Output("alert-message", "is_open", allow_duplicate=True),
    ],
    [Input("login-btn", "n_clicks")],
    [State("username", "value"), State("password", "value")],
    prevent_initial_call=True,
)
def handle_login(n_clicks, username, password):
    if n_clicks and username and password:
        if auth_manager.verify_credentials(username, password):
            auth_manager.login_user(username)
            return "/", "", "info", False, "Login successful!", "success", True
        return "/", "Invalid username or password", "danger", True, "", "info", False
    return "/", "", "info", False, "", "info", False


@callback(
    [
        Output("url", "pathname", allow_duplicate=True),
        Output("alert-message", "children", allow_duplicate=True),
        Output("alert-message", "color", allow_duplicate=True),
        Output("alert-message", "is_open", allow_duplicate=True),
        Output("login-alert", "children", allow_duplicate=True),
        Output("login-alert", "color", allow_duplicate=True),
        Output("login-alert", "is_open", allow_duplicate=True),
    ],
    [Input("logout-btn", "n_clicks")],
    prevent_initial_call=True,
)
def handle_logout(n_clicks):
    if n_clicks:
        auth_manager.logout_user()
        return "/", "", "info", False, "Logged out successfully", "info", True
    return "/", "", "info", False, "", "info", False


@callback(
    [Output("login-form", "style"), Output("register-form", "style")],
    [Input("auth-tabs", "active_tab")],
)
def toggle_auth_forms(active_tab):
    if active_tab == "register-tab":
        return {"display": "none"}, {"display": "block"}
    return {"display": "block"}, {"display": "none"}


@callback(
    [
        Output("login-alert", "children", allow_duplicate=True),
        Output("login-alert", "color", allow_duplicate=True),
        Output("login-alert", "is_open", allow_duplicate=True),
        Output("auth-tabs", "active_tab", allow_duplicate=True),
    ],
    [Input("register-btn", "n_clicks")],
    [
        State("reg-username", "value"),
        State("reg-email", "value"),
        State("reg-password", "value"),
        State("reg-password-confirm", "value"),
    ],
    prevent_initial_call=True,
)
def handle_registration(n_clicks, username, email, password, password_confirm):
    if not n_clicks:
        return "", "info", False, "register-tab"

    if not username or not password:
        return "Username and password are required", "danger", True, "register-tab"

    if len(username) < 3:
        return "Username must be at least 3 characters", "danger", True, "register-tab"

    if len(password) < 6:
        return "Password must be at least 6 characters", "danger", True, "register-tab"

    if password != password_confirm:
        return "Passwords do not match", "danger", True, "register-tab"

    existing_user = auth_manager.get_user_by_username(username)
    if existing_user:
        return "Username already taken", "danger", True, "register-tab"

    user = auth_manager.create_user(username, password, email or None)
    if user:
        return "Registration successful! Please login.", "success", True, "login-tab"
    return "Registration failed. Please try again.", "danger", True, "register-tab"


if __name__ == "__main__":
    app.run(debug=True, port=8051)
