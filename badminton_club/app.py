from dash import Dash, dcc, html, page_container, page_registry, Input, Output, State, callback
import dash_bootstrap_components as dbc
from badminton_club.auth import auth_manager
from badminton_club.database import db_session

# Initialize the Dash app with a Bootstrap theme
app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        dbc.themes.DARKLY
    ],  # You can replace FLATLY with other themes
)
app.title = "Gab's badminton group"  # Set browser title

# Flask server configuration
server = app.server
server.secret_key = auth_manager.get_secret_key()


@server.teardown_appcontext
def shutdown_session(exception=None):
    """Clean up database session after each request."""
    db_session.remove()

# Define the main layout with all components present
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),

    # Login container
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H3("Login", className="text-center")),
                    dbc.CardBody([
                        dbc.Form([
                            dbc.Row([
                                dbc.Label("Username", html_for="username", width=2),
                                dbc.Col([
                                    dbc.Input(
                                        type="text",
                                        id="username",
                                        placeholder="Enter username",
                                        required=True
                                    )
                                ], width=10)
                            ], className="mb-3"),
                            dbc.Row([
                                dbc.Label("Password", html_for="password", width=2),
                                dbc.Col([
                                    dbc.Input(
                                        type="password",
                                        id="password",
                                        placeholder="Enter password",
                                        required=True
                                    )
                                ], width=10)
                            ], className="mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button(
                                        "Login",
                                        id="login-btn",
                                        color="primary",
                                        size="lg",
                                        className="w-100"
                                    )
                                ], width={"size": 6, "offset": 3})
                            ])
                        ])
                    ])
                ], className="shadow")
            ], width={"size": 6, "offset": 3})
        ], className="min-vh-100 d-flex align-items-center"),

        # Alert for login messages (positioned at top)
        dbc.Alert(
            id="login-alert",
            is_open=False,
            dismissable=True,
            style={"position": "fixed", "top": "20px", "left": "50%", "transform": "translateX(-50%)", "z-index": "9999", "width": "400px"}
        )
    ], fluid=True, id="login-container"),

    # Main app container
    dbc.Container([
        # Navigation with user info and logout button
        dbc.Navbar([
            dbc.Nav([
                dbc.NavItem(
                    dcc.Link(page["name"], href=page["path"], className="nav-link")
                )
                for page in page_registry.values()
            ], pills=True, className="me-auto"),
            dbc.Nav([
                dbc.NavItem([
                    html.Span(
                        id="username-display",
                        className="navbar-text me-3",
                        style={"color": "white"}
                    )
                ]),
                dbc.NavItem(
                    dbc.Button(
                        "Logout",
                        id="logout-btn",
                        color="outline-light",
                        size="sm"
                    )
                )
            ])
        ], color="dark", dark=True, className="mb-4"),

        # Page content
        dbc.Card(
            dbc.CardBody(
                page_container,
                style={"padding": "20px"},
            ),
            className="shadow-sm",
        ),

        # Alert for messages (positioned at top)
        dbc.Alert(
            id="alert-message",
            is_open=False,
            dismissable=True,
            style={"position": "fixed", "top": "20px", "left": "50%", "transform": "translateX(-50%)", "z-index": "9999", "width": "400px"}
        )
    ], fluid=True, style={"padding": "20px"}, id="main-container")
])

@callback(
    [Output("login-container", "style"),
     Output("main-container", "style"),
     Output("username-display", "children")],
    [Input("url", "pathname")]
)
def display_page(pathname):
    if auth_manager.is_authenticated():
        # Show main app, hide login
        username = auth_manager.get_current_username()
        username_text = f"Welcome, {username}" if username else "Welcome"
        return {"display": "none"}, {"padding": "20px"}, username_text
    else:
        # Show login, hide main app
        return {}, {"display": "none"}, ""

@callback(
    [Output("url", "pathname", allow_duplicate=True),
     Output("login-alert", "children", allow_duplicate=True),
     Output("login-alert", "color", allow_duplicate=True),
     Output("login-alert", "is_open", allow_duplicate=True),
     Output("alert-message", "children", allow_duplicate=True),
     Output("alert-message", "color", allow_duplicate=True),
     Output("alert-message", "is_open", allow_duplicate=True)],
    [Input("login-btn", "n_clicks")],
    [State("username", "value"),
     State("password", "value")],
    prevent_initial_call=True
)
def handle_login(n_clicks, username, password):
    if n_clicks and username and password:
        if auth_manager.verify_credentials(username, password):
            auth_manager.login_user(username)
            return "/", "", "info", False, "Login successful!", "success", True
        else:
            return "/", "Invalid username or password", "danger", True, "", "info", False
    return "/", "", "info", False, "", "info", False

@callback(
    [Output("url", "pathname", allow_duplicate=True),
     Output("alert-message", "children", allow_duplicate=True),
     Output("alert-message", "color", allow_duplicate=True),
     Output("alert-message", "is_open", allow_duplicate=True),
     Output("login-alert", "children", allow_duplicate=True),
     Output("login-alert", "color", allow_duplicate=True),
     Output("login-alert", "is_open", allow_duplicate=True)],
    [Input("logout-btn", "n_clicks")],
    prevent_initial_call=True
)
def handle_logout(n_clicks):
    if n_clicks:
        auth_manager.logout_user()
        return "/", "", "info", False, "Logged out successfully", "info", True
    return "/", "", "info", False, "", "info", False

# Run the app
if __name__ == "__main__":
    app.run(debug=True, port=8051)