from dash import Dash, dcc, html, page_container, page_registry
import dash_bootstrap_components as dbc

# Initialize the Dash app with a Bootstrap theme
app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        dbc.themes.DARKLY
    ],  # You can replace FLATLY with other themes
)
app.title = "Gab's badminton group"  # Set browser title

# Define the main layout
app.layout = html.Div([dbc.Container(  # Use Bootstrap's responsive container
    [
        # Dynamic navigation links based on registered pages
        dbc.Nav(
            [
                dbc.NavItem(
                    dcc.Link(page["name"], href=page["path"], className="nav-link")
                )
                for page in page_registry.values()
                # if page["path"] != "/"
            ],
            pills=True,  # Style the navigation as pills
            className="mb-4",  # Adds spacing below the nav
        ),
        # Page container to hold the content of the active page
        dbc.Card(
            dbc.CardBody(
                page_container,
                style={"padding": "20px"},
            ),
            className="shadow-sm",  # Add a light shadow for better aesthetics
        ),
    ],
    fluid=True,  # Makes the container full width
    style={"padding": "20px", "display": "block"},  # Adds padding around the container
)])

server = app.server

# Run the app
if __name__ == "__main__":
    app.run(debug=True, port=8051)
