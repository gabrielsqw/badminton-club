from dash import html, register_page

register_page(__name__, path="/faq")

layout = html.Div([html.H2("FAQ Page"), html.P("Frequently Asked Questions go here.")])
