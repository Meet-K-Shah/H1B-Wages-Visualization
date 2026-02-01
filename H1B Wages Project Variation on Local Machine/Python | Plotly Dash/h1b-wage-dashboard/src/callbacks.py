"""
Dash Callbacks for H1B Wage Dashboard

Phase 2: Connect UI components to Phase 1 query layer
"""

from collections import defaultdict

from dash import Input, Output, callback, html
import plotly.graph_objs as go

from queries import queries


BUCKETS = ["Below L1", "Level I", "Level II", "Level III", "Level IV"]
COLOR_MAP = {
    "Below L1": "#bbbbbb",
    "Level I": "#1f77b4",
    "Level II": "#2ca02c",
    "Level III": "#ff7f0e",
    "Level IV": "#d62728",
}


@callback(
    Output("county-dropdown", "options"),
    Output("county-dropdown", "value"),
    Input("state-dropdown", "value"),
)
def update_counties_for_state(selected_state):
    """
    When state changes, update county dropdown.
    """
    if not selected_state:
        return [], None

    counties = list(queries.get_counties_for_state(selected_state))
    options = [{"label": c, "value": c} for c in counties]
    return options, None


@callback(
    Output("wage-bar-chart", "figure"),
    Output("selection-summary", "children"),
    Output("wage-details-table", "children"),
    Input("state-dropdown", "value"),
    Input("county-dropdown", "value"),
    Input("occupation-dropdown", "value"),
    Input("salary-input", "value"),
)
def update_wage_card_and_chart(state, county, soc_code, salary):
    """
    Update wage bar chart and wage details table when user selects
    state, county, and occupation. Optionally uses salary to compute
    PW Ratio and Status.
    """
    if not state or not county or not soc_code:
        return {}, "Select state, county, and occupation to view wage levels.", ""

    # Get occupation details
    occ = queries.get_occupation_by_code(soc_code)
    if not occ:
        summary = f"{state} / {county} | SOC {soc_code}"
    else:
        summary = f"{state} / {county} | {occ['job_title']} ({occ['soc_code']})"

    # Get wages
    wages = queries.get_wage_levels(state, county, soc_code)
    if not wages:
        return (
            {},
            summary,
            html.Div(
                "No wage records found for this state, county, and occupation combination."
            ),
        )

    levels = ["L1", "L2", "L3", "L4"]
    values = [wages[l] for l in levels]

    # Bar chart with optional horizontal salary line
    fig = go.Figure(
        data=[
            go.Bar(
                x=levels,
                y=values,
                marker_color=["#17a2b8", "#28a745", "#ffc107", "#dc3545"],
                name="Prevailing wage",
            )
        ]
    )

    shapes = []
    annotations = []
    if salary and salary > 0:
        shapes.append(
            dict(
                type="line",
                xref="paper",
                yref="y",
                x0=0,
                x1=1,
                y0=salary,
                y1=salary,
                line=dict(color="black", width=2, dash="dash"),
            )
        )
        annotations.append(
            dict(
                x=1.01,
                y=salary,
                xref="paper",
                yref="y",
                text=f"Your salary: ${salary:,.0f}",
                showarrow=False,
                font=dict(size=10, color="black"),
                xanchor="left",
            )
        )

    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=30),
        yaxis_title="Annual Wage (USD)",
        xaxis_title="Wage Level",
        template="plotly_white",
        shapes=shapes,
        annotations=annotations,
    )

    # Wage details table
    rows = []
    for level in levels:
        annual = wages[level]
        hourly = annual / 2080.0  # 40h/week * 52 weeks

        if salary and salary > 0:
            ratio = salary / annual * 100
            if ratio >= 100:
                status = "🟢"
            elif ratio >= 95:
                status = "🟡"
            else:
                status = "🔴"
            ratio_text = f"{ratio:.1f}%"
        else:
            status = "–"
            ratio_text = "N/A"

        rows.append(
            html.Tr(
                [
                    html.Td(level),
                    html.Td(f"${hourly:,.2f}"),
                    html.Td(f"${annual:,.0f}"),
                    html.Td(ratio_text),
                    html.Td(status),
                ]
            )
        )

    table = html.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Level"),
                        html.Th("Hourly"),
                        html.Th("Annual"),
                        html.Th("PW Ratio"),
                        html.Th("Status"),
                    ]
                )
            ),
            html.Tbody(rows),
        ],
        className="table table-sm table-striped mb-0",
    )

    return fig, summary, table

@callback(
    Output("wage-map", "figure"),
    Input("occupation-dropdown", "value"),
    Input("salary-input", "value"),
)
def update_wage_map(soc_code, salary):
    """
    Show salary-relative wage category across all counties for selected occupation.
    Each county is bucketed as Below L1, Level I–IV based on the user salary,
    using that county's own L1–L4 wages.
    """
    if not soc_code or not salary or salary <= 0:
        return {}

    # This already returns L1–L4 per (state, county)
    all_wages = queries.get_all_wages_for_occupation(soc_code)
    if not all_wages:
        return {}
    
    bucket_points = defaultdict(lambda: {"states": [], "counties": []})

    for (state, county), w in all_wages.items():
        w1, w2, w3, w4 = w["L1"], w["L2"], w["L3"], w["L4"]

        if salary < w1:
            bucket = "Below L1"
        elif salary < w2:
            bucket = "Level I"
        elif salary < w3:
            bucket = "Level II"
        elif salary < w4:
            bucket = "Level III"
        else:
            bucket = "Level IV"

        bucket_points[bucket]["states"].append(state)
        bucket_points[bucket]["counties"].append(county)


    # Build one trace per bucket so legend shows the five buckets
    data = []
    for bucket in BUCKETS:
        pts = bucket_points.get(bucket)
        if not pts or not pts["states"]:
            continue

        hover_texts = [
            f"{c}, {s}<br>{bucket}"
            for s, c in zip(pts["states"], pts["counties"])
        ]

        data.append(
            go.Scattergeo(
                locationmode="USA-states",
                text=hover_texts,
                mode="markers",
                marker=dict(
                    size=0.5,
                    color=COLOR_MAP[bucket],
                    opacity=1.0,
                ),
                name=bucket,
            )
        )

    fig = go.Figure(data=data)
    fig.update_layout(
        geo=dict(
            scope="usa",
            showland=True,
            landcolor="rgb(240, 240, 240)",
            showcountries=True,
        ),
        margin=dict(l=5, r=5, t=20, b=10),
        template="plotly_white",
    )

    return fig
