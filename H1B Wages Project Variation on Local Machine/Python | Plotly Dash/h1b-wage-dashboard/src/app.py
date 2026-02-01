"""
Dash Application Entry Point
Phase 2: Wire Phase 1 data layer to Dash UI
Run:
    python -m app.app
or:
    python app/app.py
"""

import os
from pathlib import Path

from dash import Dash
import dash_bootstrap_components as dbc
from flask import Flask

from layout import serve_layout
from queries import queries  # noqa: F401  # ensures db/queries are imported
import callbacks  # noqa: F401  # registers callbacks


def create_flask_server():
    """
    Create underlying Flask server for Dash.
    Useful for deploying with gunicorn: gunicorn app.app:server
    """
    server = Flask(__name__)
    return server


def create_dash_app(server=None):
    """
    Initialize Dash app and attach to Flask server.
    """
    if server is None:
        server = create_flask_server()

    external_stylesheets = [dbc.themes.BOOTSTRAP]

    app = Dash(
        __name__,
        server=server,
        external_stylesheets=external_stylesheets,
        suppress_callback_exceptions=True,
        title="H1B Wage Dashboard",
    )

    app.layout = serve_layout

    return app, server


# For gunicorn: `server` variable must be at module level
app, server = create_dash_app()


if __name__ == "__main__":
    # Allow port override for deployment / debugging
    port = int(os.environ.get("PORT", 8050))
    debug = os.environ.get("DEBUG", "1") == "1"

    app.run(host='127.0.0.1', port=port, debug=debug)
