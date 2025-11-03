"""
Progress Analytics Component for MED13 Curation Dashboard.

Provides comprehensive analytics and progress tracking for curation workflows.
"""

from typing import Any, Dict, List

from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from datetime import datetime, timedelta


def create_progress_analytics_dashboard() -> dbc.Container:
    """
    Create a comprehensive progress analytics dashboard for curation workflows.

    Returns:
        Bootstrap Container with analytics dashboard
    """
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H3("Curation Progress Analytics", className="mb-4"),
                            html.P(
                                "Real-time insights into curation workflow performance and team progress",
                                className="text-muted mb-4",
                            ),
                        ]
                    )
                ]
            ),
            # Key Metrics Row
            dbc.Row(
                [
                    dbc.Col(create_completion_gauge(), width=3),
                    dbc.Col(create_conflict_resolution_stats(), width=3),
                    dbc.Col(create_team_productivity_metrics(), width=3),
                    dbc.Col(create_quality_trends(), width=3),
                ],
                className="mb-4",
            ),
            # Charts Row
            dbc.Row(
                [
                    dbc.Col(create_progress_timeline_chart(), width=8),
                    dbc.Col(create_conflict_heatmap(), width=4),
                ],
                className="mb-4",
            ),
            # Detailed Analytics
            dbc.Row(
                [
                    dbc.Col(create_curator_performance_table(), width=6),
                    dbc.Col(create_variant_category_breakdown(), width=6),
                ],
                className="mb-4",
            ),
            # Recent Activity Feed
            dbc.Row([dbc.Col(create_recent_activity_feed(), width=12)]),
        ],
        fluid=True,
    )


def create_completion_gauge() -> dbc.Card:
    """Create a completion gauge showing overall curation progress."""
    # Mock data - would come from database in production
    completed = 2340
    total = 3600
    percentage = int((completed / total) * 100)

    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H6("Overall Completion", className="card-title text-center"),
                    dbc.Progress(
                        value=percentage,
                        color="success",
                        className="mb-2",
                        style={"height": "20px"},
                    ),
                    html.Div(
                        [
                            html.H4(f"{percentage}%", className="text-center mb-1"),
                            html.Small(
                                f"{completed:,} of {total:,} variants",
                                className="text-muted text-center d-block",
                            ),
                        ]
                    ),
                ]
            )
        ],
        className="h-100",
    )


def create_conflict_resolution_stats() -> dbc.Card:
    """Create conflict resolution statistics card."""
    resolved = 487
    pending = 123
    escalated = 34

    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H6("Conflict Resolution", className="card-title"),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Span("✅ ", className="text-success"),
                                    f"Resolved: {resolved}",
                                ],
                                className="mb-1",
                            ),
                            html.Div(
                                [
                                    html.Span("⏳ ", className="text-warning"),
                                    f"Pending: {pending}",
                                ],
                                className="mb-1",
                            ),
                            html.Div(
                                [
                                    html.Span("🚩 ", className="text-danger"),
                                    f"Escalated: {escalated}",
                                ]
                            ),
                        ]
                    ),
                    html.Hr(),
                    html.Small(
                        f"Resolution Rate: {resolved/(resolved+pending+escalated)*100:.1f}%",
                        className="text-muted",
                    ),
                ]
            )
        ],
        className="h-100",
    )


def create_team_productivity_metrics() -> dbc.Card:
    """Create team productivity metrics card."""
    today_reviews = 47
    weekly_avg = 312
    top_performer = "Dr. Smith"

    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H6("Team Productivity", className="card-title"),
                    html.Div(
                        [
                            html.Div(
                                [html.Strong("Today:"), f" {today_reviews} reviews"],
                                className="mb-1",
                            ),
                            html.Div(
                                [html.Strong("Weekly Avg:"), f" {weekly_avg} reviews"],
                                className="mb-1",
                            ),
                            html.Div(
                                [html.Strong("Top Performer:"), f" {top_performer}"]
                            ),
                        ]
                    ),
                    html.Hr(),
                    html.Small(
                        "📈 12% increase from last week", className="text-success"
                    ),
                ]
            )
        ],
        className="h-100",
    )


def create_quality_trends() -> dbc.Card:
    """Create quality trends card."""
    avg_quality = 87.3
    trend_direction = "up"
    change_percent = 3.2

    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H6("Quality Trends", className="card-title"),
                    html.Div(
                        [
                            html.H4(f"{avg_quality}%", className="mb-1"),
                            html.Small(
                                "Average curation quality", className="text-muted"
                            ),
                        ]
                    ),
                    html.Hr(),
                    html.Small(
                        [
                            "📊 " if trend_direction == "up" else "📉 ",
                            f"{change_percent}% vs last month",
                        ],
                        className=(
                            "text-success" if trend_direction == "up" else "text-danger"
                        ),
                    ),
                ]
            )
        ],
        className="h-100",
    )


def create_progress_timeline_chart() -> dbc.Card:
    """Create a timeline chart showing curation progress over time."""
    # Mock timeline data
    dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]
    completed = [2200 + i * 5 for i in range(30)]  # Cumulative completion

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=completed,
            mode="lines+markers",
            name="Completed Variants",
            line=dict(color="#28a745", width=3),
            marker=dict(size=6),
        )
    )

    # Add target line
    target = [3600] * 30
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=target,
            mode="lines",
            name="Target",
            line=dict(color="#6c757d", width=2, dash="dash"),
        )
    )

    fig.update_layout(
        title="Curation Progress Timeline",
        xaxis_title="Date",
        yaxis_title="Variants Completed",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=True,
    )

    return dbc.Card(
        [dbc.CardBody([dcc.Graph(figure=fig, config={"displayModeBar": False})])]
    )


def create_conflict_heatmap() -> dbc.Card:
    """Create a heatmap showing conflict types by curator."""
    # Mock conflict data by curator and type
    curators = ["Dr. Smith", "Dr. Johnson", "Dr. Williams", "Dr. Brown"]
    conflict_types = ["Clinical Sig.", "Evidence Level", "Confidence"]

    # Mock data - conflicts resolved by each curator per type
    data = [
        [12, 8, 5],  # Dr. Smith
        [15, 6, 3],  # Dr. Johnson
        [9, 12, 7],  # Dr. Williams
        [6, 9, 8],  # Dr. Brown
    ]

    fig = go.Figure(
        data=go.Heatmap(
            z=data,
            x=conflict_types,
            y=curators,
            colorscale="RdYlGn_r",  # Red for high conflicts, green for low
            text=[[f"{val}" for val in row] for row in data],
            texttemplate="%{text}",
            textfont={"size": 12},
            hoverongaps=False,
        )
    )

    fig.update_layout(
        title="Conflict Resolution by Curator",
        xaxis_title="Conflict Type",
        yaxis_title="Curator",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
    )

    return dbc.Card(
        [dbc.CardBody([dcc.Graph(figure=fig, config={"displayModeBar": False})])]
    )


def create_curator_performance_table() -> dbc.Card:
    """Create a table showing curator performance metrics."""
    # Mock curator performance data
    performance_data: List[Dict[str, Any]] = [
        {
            "name": "Dr. Smith",
            "reviews": 1247,
            "avg_quality": 92.3,
            "conflicts_resolved": 156,
            "avg_time": "4.2 min",
        },
        {
            "name": "Dr. Johnson",
            "reviews": 1189,
            "avg_quality": 89.7,
            "conflicts_resolved": 142,
            "avg_time": "4.8 min",
        },
        {
            "name": "Dr. Williams",
            "reviews": 1156,
            "avg_quality": 91.1,
            "conflicts_resolved": 138,
            "avg_time": "4.5 min",
        },
        {
            "name": "Dr. Brown",
            "reviews": 987,
            "avg_quality": 88.9,
            "conflicts_resolved": 98,
            "avg_time": "5.1 min",
        },
    ]

    table_rows = []
    for curator in performance_data:
        row = html.Tr(
            [
                html.Td(curator["name"]),
                html.Td(f"{curator['reviews']:,}"),
                html.Td(
                    [
                        f"{curator['avg_quality']}%",
                        " ",
                        (
                            "🟢"
                            if curator["avg_quality"] >= 90
                            else "🟡"
                            if curator["avg_quality"] >= 85
                            else "🔴"
                        ),
                    ]
                ),
                html.Td(curator["conflicts_resolved"]),
                html.Td(curator["avg_time"]),
            ]
        )
        table_rows.append(row)

    return dbc.Card(
        [
            dbc.CardHeader("Curator Performance"),
            dbc.CardBody(
                [
                    dbc.Table(
                        [
                            html.Thead(
                                html.Tr(
                                    [
                                        html.Th("Curator"),
                                        html.Th("Reviews"),
                                        html.Th("Avg Quality"),
                                        html.Th("Conflicts Resolved"),
                                        html.Th("Avg Time"),
                                    ]
                                )
                            ),
                            html.Tbody(table_rows),
                        ],
                        bordered=True,
                        hover=True,
                        responsive=True,
                        size="sm",
                    )
                ]
            ),
        ]
    )


def create_variant_category_breakdown() -> dbc.Card:
    """Create a breakdown of variants by clinical category."""
    # Mock category data
    categories = [
        {"name": "Pathogenic", "count": 1456, "percentage": 40.4, "color": "#C0392B"},
        {
            "name": "Uncertain Significance",
            "count": 1089,
            "percentage": 30.3,
            "color": "#F1C40F",
        },
        {
            "name": "Likely Pathogenic",
            "count": 567,
            "percentage": 15.8,
            "color": "#E74C3C",
        },
        {"name": "Benign", "count": 321, "percentage": 8.9, "color": "#1ABC9C"},
        {"name": "Likely Benign", "count": 167, "percentage": 4.6, "color": "#27AE60"},
    ]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=[cat["name"] for cat in categories],
                values=[cat["count"] for cat in categories],
                marker_colors=[cat["color"] for cat in categories],
                textinfo="label+percent",
                textposition="inside",
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        title="Variants by Clinical Significance",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
    )

    return dbc.Card(
        [dbc.CardBody([dcc.Graph(figure=fig, config={"displayModeBar": False})])]
    )


def create_recent_activity_feed() -> dbc.Card:
    """Create a feed of recent curation activities."""
    # Mock recent activities
    activities = [
        {
            "timestamp": "2024-01-15 14:32:00",
            "user": "Dr. Smith",
            "action": "Resolved clinical significance conflict",
            "variant": "MED13:c.123A>G",
            "details": "Accepted ClinVar pathogenic classification over internal assessment",
        },
        {
            "timestamp": "2024-01-15 14:28:00",
            "user": "Dr. Johnson",
            "action": "Added expert annotation",
            "variant": "MED13:c.456T>C",
            "details": "Noted functional studies support benign classification",
        },
        {
            "timestamp": "2024-01-15 14:25:00",
            "user": "Dr. Williams",
            "action": "Approved variant curation",
            "variant": "MED13:c.789G>A",
            "details": "Strong evidence from multiple sources",
        },
        {
            "timestamp": "2024-01-15 14:22:00",
            "user": "Dr. Brown",
            "action": "Flagged for expert review",
            "variant": "MED13:c.101C>T",
            "details": "Conflicting evidence levels between sources",
        },
        {
            "timestamp": "2024-01-15 14:18:00",
            "user": "Dr. Smith",
            "action": "Updated confidence score",
            "variant": "MED13:c.202G>C",
            "details": "Increased confidence based on new literature evidence",
        },
    ]

    activity_items = []
    for activity in activities:
        activity_item = dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.Strong(activity["action"]),
                                html.Small(
                                    f" • {activity['variant']}",
                                    className="text-muted ms-2",
                                ),
                            ],
                            className="mb-1",
                        ),
                        html.P(activity["details"], className="text-muted mb-1 small"),
                        html.Div(
                            [
                                html.Small(
                                    f"by {activity['user']}",
                                    className="text-primary me-3",
                                ),
                                html.Small(
                                    activity["timestamp"], className="text-muted"
                                ),
                            ]
                        ),
                    ],
                    width=10,
                ),
                dbc.Col(
                    [
                        # Activity type icon
                        html.I(
                            className=f"{get_activity_icon(activity['action'])} fa-lg text-info",
                        )
                    ],
                    width=2,
                    className="text-end",
                ),
            ],
            className="mb-3 pb-3 border-bottom",
        )

        activity_items.append(activity_item)

    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H6("Recent Activity Feed", className="mb-0"),
                    dbc.Badge("Live", color="success", className="ms-2"),
                ]
            ),
            dbc.CardBody(
                [
                    html.Div(
                        activity_items,
                        style={"maxHeight": "400px", "overflowY": "auto"},
                    )
                ]
            ),
        ]
    )


def get_activity_icon(action: str) -> str:
    """Get appropriate icon class for activity type."""
    icon_map = {
        "Resolved clinical significance conflict": "fas fa-check-circle text-success",
        "Added expert annotation": "fas fa-comment-medical text-info",
        "Approved variant curation": "fas fa-thumbs-up text-success",
        "Flagged for expert review": "fas fa-flag text-warning",
        "Updated confidence score": "fas fa-chart-line text-primary",
    }
    return icon_map.get(action, "fas fa-circle text-muted")


def create_bulk_resolution_tools() -> dbc.Card:
    """Create bulk resolution tools for handling multiple conflicts."""
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H6("Bulk Resolution Tools", className="mb-0"),
                    dbc.Badge("Advanced", color="info", className="ms-2"),
                ]
            ),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H6("Quick Actions", className="mb-3"),
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button(
                                                [
                                                    html.I(
                                                        className="fas fa-check-double me-2"
                                                    ),
                                                    "Accept All Highest Evidence",
                                                ],
                                                color="success",
                                                size="sm",
                                                id="bulk-accept-highest",
                                            ),
                                            dbc.Button(
                                                [
                                                    html.I(
                                                        className="fas fa-flag me-2"
                                                    ),
                                                    "Flag All Conflicts",
                                                ],
                                                color="warning",
                                                size="sm",
                                                id="bulk-flag-conflicts",
                                            ),
                                        ],
                                        vertical=True,
                                        className="w-100 mb-3",
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.H6("Batch Processing", className="mb-3"),
                                    html.Div(
                                        [
                                            html.Label("Apply to conflicts with:"),
                                            dcc.Checklist(
                                                options=[  # type: ignore
                                                    {
                                                        "label": " Low severity",
                                                        "value": "low",
                                                    },
                                                    {
                                                        "label": " Medium severity",
                                                        "value": "medium",
                                                    },
                                                    {
                                                        "label": " High severity",
                                                        "value": "high",
                                                    },
                                                ],
                                                value=[],
                                                id="bulk-severity-filter",
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-cogs me-2"),
                                            "Process Batch",
                                        ],
                                        color="primary",
                                        id="process-batch-btn",
                                    ),
                                ],
                                width=6,
                            ),
                        ]
                    )
                ]
            ),
        ]
    )


__all__ = [
    "create_progress_analytics_dashboard",
    "create_completion_gauge",
    "create_conflict_resolution_stats",
    "create_team_productivity_metrics",
    "create_quality_trends",
    "create_progress_timeline_chart",
    "create_conflict_heatmap",
    "create_curator_performance_table",
    "create_variant_category_breakdown",
    "create_recent_activity_feed",
    "create_bulk_resolution_tools",
]
