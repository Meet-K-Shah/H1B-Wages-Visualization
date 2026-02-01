"""
Dash Layout and UI Components for H1B Wage Dashboard

Phase 2: Interactive dashboard using Phase 1 database/query layer
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

from queries import queries


def serve_layout():
    """
    Build the main app layout.

    Uses Phase 1 query layer for initial dropdown options.
    """

    # Initial data for dropdowns
    all_states = list(queries.get_all_states())
    occupations = list(queries.get_all_occupations())

    return dbc.Container(
        fluid=True,
        children=[
            # Title
            dbc.Row(
                dbc.Col(
                    html.H2("H1B Wage Intelligence Dashboard"),
                    width=12,
                ),
                className="mt-3 mb-2",
            ),

            # Top controls: state, county, occupation, salary
            dbc.Row(
                [
                    # State
                    dbc.Col(
                        [
                            html.Label("State"),
                            dcc.Dropdown(
                                id="state-dropdown",
                                options=[
                                    {"label": s, "value": s} for s in all_states
                                ],
                                placeholder="Select a state",
                                value=None,
                                clearable=True,
                            ),
                        ],
                        md=3,
                    ),

                    # County (depends on state)
                    dbc.Col(
                        [
                            html.Label("County"),
                            dcc.Dropdown(
                                id="county-dropdown",
                                options=[],
                                placeholder="Select a county",
                                value=None,
                                clearable=True,
                            ),
                        ],
                        md=3,
                    ),

                    # Occupation autocomplete
                    dbc.Col(
                        [
                            html.Label("Occupation (SOC)"),
                            dcc.Dropdown(
                                id="occupation-dropdown",
                                options=[
                                    {
                                        "label": f"{o['job_title']} ({o['soc_code']})",
                                        "value": o["soc_code"],
                                    }
                                    for o in occupations
                                ],
                                placeholder="Search or select an occupation",
                                value=None,
                                clearable=True,
                                searchable=True,
                            ),
                            html.Small(
                                "Tip: Start typing job title or SOC code to search",
                                className="text-muted",
                            ),
                        ],
                        md=3,
                    ),

                    # Salary input
                    dbc.Col(
                        [
                            html.Label("Salary"),
                            dcc.Input(
                                id="salary-input",
                                type="number",
                                placeholder="Enter salary",
                                min=0,
                                step=1000,  # adjust as needed
                                value=None,
                                className="form-control",  # Bootstrap styling
                            ),
                            html.Small(
                                "Enter annual salary (USD)",
                                className="text-muted",
                            ),
                        ],
                        md=3,
                    ),
                ],
                className="mb-4",
            ),

            # Wage summary + bar chart row
            dbc.Row(
                [
                    # Wage summary card (location + wage table)
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Selected Location & Occupation"),
                                dbc.CardBody(
                                    [
                                        html.Div(
                                            id="selection-summary",
                                            children=(
                                                "Select state, county, and occupation "
                                                "to view wage levels."
                                            ),
                                        ),
                                        html.Hr(),
                                        # New wage details table container
                                        html.Div(
                                            id="wage-details-table",
                                            children="",
                                        ),
                                    ]
                                ),
                            ],
                            className="h-100",
                        ),
                        md=4,
                    ),

                    # Wage bar chart
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    "Prevailing Wage Levels (L1-L4)"
                                ),
                                dbc.CardBody(
                                    dcc.Graph(
                                        id="wage-bar-chart",
                                        figure={},
                                        config={"displayModeBar": False},
                                    )
                                ),
                            ],
                            className="h-100",
                        ),
                        md=8,
                    ),
                ],
                className="mb-4",
            ),

            # Map / multi-county distribution row
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    "Wage Distribution Across Counties "
                                    "(selected occupation)"
                                ),
                                dbc.CardBody(
                                    [
                                        html.Div(
                                            "Shows how your salary compares to local prevailing wages "
                                            "for the selected occupation across all counties."
                                        ),
                                        dcc.Graph(
                                            id="wage-map",
                                            figure={},
                                            config={"displayModeBar": False},
                                        ),
                                    ]
                                ),
                            ]
                        ),
                        md=12,
                    ),
                ]
            ),

            # Hidden store for client-side state if needed later
            dcc.Store(id="occupation-search-cache"),
        ],
    )
