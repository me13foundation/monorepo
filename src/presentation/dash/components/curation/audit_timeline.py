"""
Enhanced Audit Timeline Component for MED13 Curation Dashboard.

Provides sophisticated visualization of curation history and decision trails.
"""

from typing import Any, Dict, List, Optional, Tuple

from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from datetime import datetime, timedelta


def create_enhanced_audit_timeline(
    variant_id: str, audit_events: Optional[List[Dict[str, Any]]] = None
) -> dbc.Card:
    """
    Create an enhanced audit timeline showing detailed curation history.

    Args:
        variant_id: The variant identifier
        audit_events: List of audit events (optional, uses mock data if not provided)

    Returns:
        Bootstrap Card with enhanced audit timeline
    """
    if audit_events is None:
        audit_events = _get_mock_audit_events(variant_id)

    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H5("Audit Timeline", className="mb-0"),
                    html.Small(f"Variant: {variant_id}", className="text-muted ms-2"),
                ]
            ),
            dbc.CardBody(
                [
                    # Timeline controls
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button(
                                                "Timeline",
                                                active=True,
                                                size="sm",
                                                id="view-timeline",
                                            ),
                                            dbc.Button(
                                                "Graph", size="sm", id="view-graph"
                                            ),
                                            dbc.Button(
                                                "Table", size="sm", id="view-table"
                                            ),
                                        ]
                                    )
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    dcc.Dropdown(
                                        options=[  # type: ignore
                                            {"label": "All Events", "value": "all"},
                                            {
                                                "label": "Decisions Only",
                                                "value": "decisions",
                                            },
                                            {
                                                "label": "Annotations Only",
                                                "value": "annotations",
                                            },
                                            {
                                                "label": "Conflicts Only",
                                                "value": "conflicts",
                                            },
                                        ],
                                        value="all",
                                        id="timeline-filter",
                                        clearable=False,
                                        className="mb-0",
                                    )
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.Small(
                                                f"{len(audit_events)} total events",
                                                className="text-muted",
                                            )
                                        ],
                                        className="text-end",
                                    )
                                ],
                                width=4,
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Timeline visualization
                    html.Div(
                        id="timeline-content",
                        children=create_timeline_view(audit_events),
                    ),
                    # Summary statistics
                    dbc.Row(
                        [dbc.Col(create_timeline_stats(audit_events), width=12)],
                        className="mt-4",
                    ),
                ]
            ),
        ]
    )


def create_timeline_view(audit_events: List[Dict[str, Any]]) -> html.Div:
    """Create the main timeline view with enhanced visualization."""
    if not audit_events:
        return html.Div(
            [dbc.Alert("No audit events available for this variant.", color="info")]
        )

    # Sort events by timestamp (most recent first for timeline)
    sorted_events = sorted(audit_events, key=lambda x: x["timestamp"], reverse=True)

    timeline_items = []
    for i, event in enumerate(sorted_events):
        event_type = _classify_event_type(event)
        timeline_items.append(_create_timeline_item(event, event_type, i))

    return html.Div(
        [html.Div(timeline_items, className="timeline-container")],
        className="audit-timeline",
    )


def _create_timeline_item(
    event: Dict[str, Any], event_type: str, index: int
) -> html.Div:
    """Create a single timeline item with enhanced styling."""
    icon_class, color_class = _get_event_styling(event_type)

    # Decision impact indicator
    impact_indicator = _get_decision_impact(event)

    return html.Div(
        [
            # Timeline connector
            html.Div(className="timeline-connector"),
            # Timeline content
            html.Div(
                [
                    # Event header
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.I(
                                                className=f"{icon_class} timeline-icon {color_class}"
                                            ),
                                            html.Strong(
                                                event["action"], className="ms-2"
                                            ),
                                            impact_indicator,
                                        ],
                                        className="d-flex align-items-center",
                                    )
                                ],
                                width=8,
                            ),
                            dbc.Col(
                                [
                                    html.Small(
                                        _format_timestamp(event["timestamp"]),
                                        className="text-muted text-end d-block",
                                    )
                                ],
                                width=4,
                            ),
                        ],
                        className="mb-2",
                    ),
                    # Event details
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.Small("👤 ", className="text-muted"),
                                            html.Small(
                                                event.get("user", "System"),
                                                className="text-primary fw-bold",
                                            ),
                                        ],
                                        className="mb-1",
                                    ),
                                    html.P(
                                        event.get("details", ""),
                                        className="text-muted small mb-1",
                                    ),
                                    _create_event_metadata(event),
                                ],
                                width=10,
                            ),
                            dbc.Col(
                                [_create_event_actions(event, index)],
                                width=2,
                                className="text-end",
                            ),
                        ]
                    ),
                ],
                className="timeline-content",
            ),
        ],
        className="timeline-item",
    )


def _classify_event_type(event: Dict[str, Any]) -> str:
    """Classify event type for styling and filtering."""
    action = event.get("action", "").lower()

    if "conflict" in action or "resolve" in action:
        return "conflict"
    elif "annotat" in action or "comment" in action:
        return "annotation"
    elif "approve" in action or "reject" in action or "decis" in action:
        return "decision"
    elif "review" in action or "flag" in action:
        return "review"
    elif "update" in action or "change" in action:
        return "update"
    else:
        return "system"


def _get_event_styling(event_type: str) -> Tuple[str, str]:
    """Get icon and color styling for event type."""
    styling_map = {
        "conflict": ("fas fa-exclamation-triangle", "text-warning"),
        "annotation": ("fas fa-comment-medical", "text-info"),
        "decision": ("fas fa-gavel", "text-success"),
        "review": ("fas fa-flag", "text-danger"),
        "update": ("fas fa-edit", "text-primary"),
        "system": ("fas fa-cog", "text-muted"),
    }

    return styling_map.get(event_type, ("fas fa-circle", "text-muted"))


def _get_decision_impact(event: Dict[str, Any]) -> Optional[html.Span]:
    """Create impact indicator for significant decisions."""
    action = event.get("action", "").lower()
    impact_level = None

    if "approve" in action and "pathogenic" in event.get("details", "").lower():
        impact_level = "high"
    elif "reject" in action or "conflict" in action:
        impact_level = "medium"
    elif "flag" in action or "review" in action:
        impact_level = "low"

    if impact_level:
        color_map = {"high": "danger", "medium": "warning", "low": "info"}
        return html.Span(
            "●",
            className=f"text-{color_map[impact_level]} ms-2",
            title=f"{impact_level.title()} impact decision",
        )

    return None


def _create_event_metadata(event: Dict[str, Any]) -> html.Div:
    """Create metadata display for event details."""
    metadata_items = []

    # Add confidence change if present
    if "confidence_change" in event:
        metadata_items.append(
            html.Small(
                f"🎯 Confidence: {event['confidence_change']}", className="d-block"
            )
        )

    # Add evidence strength if present
    if "evidence_level" in event:
        metadata_items.append(
            html.Small(f"📊 Evidence: {event['evidence_level']}", className="d-block")
        )

    # Add related conflicts if present
    if "related_conflicts" in event:
        metadata_items.append(
            html.Small(
                f"⚠️ Conflicts: {event['related_conflicts']}", className="d-block"
            )
        )

    return html.Div(metadata_items) if metadata_items else html.Div()


def _create_event_actions(event: Dict[str, Any], index: int) -> html.Div:
    """Create action buttons for timeline events."""
    actions = []

    # Undo action for recent decisions
    if _is_recent_event(event) and _is_reversible_action(event):
        actions.append(
            dbc.Button(
                html.I(className="fas fa-undo"),
                size="sm",
                color="outline-secondary",
                id=f"undo-event-{index}",
                title="Undo this action",
            )
        )

    # View details action
    actions.append(
        dbc.Button(
            html.I(className="fas fa-eye"),
            size="sm",
            color="outline-info",
            id=f"view-event-{index}",
            title="View full details",
        )
    )

    return html.Div(actions, className="btn-group-vertical btn-group-sm")


def create_graph_view(audit_events: List[Dict[str, Any]]) -> dcc.Graph:
    """Create a graph view of audit events over time."""
    if not audit_events:
        return dcc.Graph()

    # Group events by date and type
    events_by_date: Dict[str, Dict[str, int]] = {}
    for event in audit_events:
        if isinstance(event["timestamp"], str):
            try:
                dt = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
                date_str = dt.date().isoformat()
            except (ValueError, TypeError):
                date_str = "unknown"
        elif isinstance(event["timestamp"], datetime):
            date_str = event["timestamp"].date().isoformat()
        else:
            date_str = "unknown"
        event_type = _classify_event_type(event)

        if date_str not in events_by_date:
            events_by_date[date_str] = {}
        if event_type not in events_by_date[date_str]:
            events_by_date[date_str][event_type] = 0
        events_by_date[date_str][event_type] += 1

    # Create traces for each event type
    dates = sorted(events_by_date.keys())
    traces = []

    event_types = ["decision", "conflict", "annotation", "review", "update", "system"]
    colors = ["#28a745", "#ffc107", "#17a2b8", "#dc3545", "#007bff", "#6c757d"]

    for event_type, color in zip(event_types, colors):
        counts = [events_by_date.get(date, {}).get(event_type, 0) for date in dates]
        if any(counts):  # Only add trace if there are events
            traces.append(
                go.Bar(name=event_type.title(), x=dates, y=counts, marker_color=color)
            )

    fig = go.Figure(data=traces)

    fig.update_layout(
        title="Audit Events Over Time",
        xaxis_title="Date",
        yaxis_title="Number of Events",
        barmode="stack",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
    )

    return dcc.Graph(figure=fig)


def create_table_view(audit_events: List[Dict[str, Any]]) -> dbc.Table:
    """Create a tabular view of audit events."""
    if not audit_events:
        return dbc.Table()

    headers = [
        html.Th("Timestamp"),
        html.Th("Action"),
        html.Th("User"),
        html.Th("Details"),
        html.Th("Type"),
    ]

    rows = []
    for event in audit_events:
        event_type = _classify_event_type(event)
        _, color_class = _get_event_styling(event_type)

        row = html.Tr(
            [
                html.Td(_format_timestamp(event["timestamp"])),
                html.Td(event["action"]),
                html.Td(event.get("user", "System")),
                html.Td(html.Small(event.get("details", ""), className="text-muted")),
                html.Td(
                    dbc.Badge(
                        event_type.title(),
                        className=color_class.replace("text-", "badge-"),
                    )
                ),
            ]
        )
        rows.append(row)

    return dbc.Table(
        [html.Thead(html.Tr(headers)), html.Tbody(rows)],
        bordered=True,
        hover=True,
        responsive=True,
        size="sm",
    )


def create_timeline_stats(audit_events: List[Dict[str, Any]]) -> dbc.Card:
    """Create statistics summary for the audit timeline."""
    if not audit_events:
        return dbc.Card()

    # Calculate statistics
    total_events = len(audit_events)
    event_types: Dict[str, int] = {}

    for event in audit_events:
        event_type = _classify_event_type(event)
        event_types[event_type] = event_types.get(event_type, 0) + 1

    # Calculate time span
    if audit_events:
        timestamps = [
            (
                datetime.fromisoformat(event["timestamp"])
                if isinstance(event["timestamp"], str)
                else event["timestamp"]
            )
            for event in audit_events
        ]
        time_span = max(timestamps) - min(timestamps)
        days_span = time_span.days if hasattr(time_span, "days") else 1
    else:
        days_span = 0

    # Most active user
    user_counts: Dict[str, int] = {}
    for event in audit_events:
        user = event.get("user", "System")
        user_counts[user] = user_counts.get(user, 0) + 1

    most_active_user = (
        max(user_counts.items(), key=lambda x: x[1]) if user_counts else ("None", 0)
    )

    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H6("Timeline Statistics", className="card-title"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.Strong(f"{total_events}"),
                                            html.Br(),
                                            html.Small(
                                                "Total Events", className="text-muted"
                                            ),
                                        ]
                                    )
                                ],
                                width=3,
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.Strong(f"{len(event_types)}"),
                                            html.Br(),
                                            html.Small(
                                                "Event Types", className="text-muted"
                                            ),
                                        ]
                                    )
                                ],
                                width=3,
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.Strong(f"{days_span}"),
                                            html.Br(),
                                            html.Small(
                                                "Days Span", className="text-muted"
                                            ),
                                        ]
                                    )
                                ],
                                width=3,
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.Strong(most_active_user[0]),
                                            html.Br(),
                                            html.Small(
                                                f"{most_active_user[1]} events",
                                                className="text-muted",
                                            ),
                                        ]
                                    )
                                ],
                                width=3,
                            ),
                        ],
                        className="text-center",
                    ),
                ]
            )
        ]
    )


def _get_mock_audit_events(variant_id: str) -> List[Dict[str, Any]]:
    """Generate mock audit events for demonstration."""
    base_time = datetime.now()

    return [
        {
            "timestamp": (base_time - timedelta(hours=2)).isoformat(),
            "action": "Variant Created",
            "user": "Data Pipeline",
            "details": f"Initial import of variant {variant_id} from ClinVar database",
            "event_type": "system",
        },
        {
            "timestamp": (base_time - timedelta(hours=1, minutes=45)).isoformat(),
            "action": "Evidence Added",
            "user": "System",
            "details": "ClinVar evidence automatically associated",
            "evidence_level": "supporting",
            "event_type": "system",
        },
        {
            "timestamp": (base_time - timedelta(hours=1, minutes=30)).isoformat(),
            "action": "Clinical Significance Assessed",
            "user": "Dr. Smith",
            "details": "Initial assessment: Uncertain significance based on limited evidence",
            "confidence_change": "0.6 → 0.7",
            "event_type": "decision",
        },
        {
            "timestamp": (base_time - timedelta(hours=1)).isoformat(),
            "action": "Conflict Detected",
            "user": "System",
            "details": "Evidence level disagreement between ClinVar (supporting) and internal assessment (limited)",
            "related_conflicts": 1,
            "event_type": "conflict",
        },
        {
            "timestamp": (base_time - timedelta(minutes=45)).isoformat(),
            "action": "Expert Annotation Added",
            "user": "Dr. Johnson",
            "details": "Noted recent publication suggesting pathogenic classification. Recommends review of additional functional studies.",
            "evidence_level": "supporting",
            "event_type": "annotation",
        },
        {
            "timestamp": (base_time - timedelta(minutes=30)).isoformat(),
            "action": "Flagged for Expert Review",
            "user": "Dr. Smith",
            "details": "Escalated due to conflicting evidence and clinical significance uncertainty",
            "event_type": "review",
        },
        {
            "timestamp": (base_time - timedelta(minutes=15)).isoformat(),
            "action": "Confidence Score Updated",
            "user": "Dr. Williams",
            "details": "Increased confidence to 0.85 based on additional literature review",
            "confidence_change": "0.7 → 0.85",
            "event_type": "update",
        },
        {
            "timestamp": base_time.isoformat(),
            "action": "Final Decision: Approved",
            "user": "Dr. Williams",
            "details": "Approved as Likely Pathogenic based on consensus of evidence and expert review",
            "event_type": "decision",
        },
    ]


def _format_timestamp(timestamp: Any) -> str:
    """Format timestamp for display."""
    if isinstance(timestamp, str):
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return timestamp
    elif isinstance(timestamp, datetime):
        dt = timestamp
    else:
        return str(timestamp)

    return dt.strftime("%Y-%m-%d %H:%M")


def _is_recent_event(event: Dict[str, Any]) -> bool:
    """Check if event is recent (within last 24 hours)."""
    if isinstance(event["timestamp"], str):
        event_time = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
    elif isinstance(event["timestamp"], datetime):
        event_time = event["timestamp"]
    else:
        return False

    return (datetime.now() - event_time).total_seconds() < 86400  # 24 hours


def _is_reversible_action(event: Dict[str, Any]) -> bool:
    """Check if the action can be reversed."""
    reversible_actions = ["Approved", "Rejected", "Flagged", "Updated"]
    return any(action in event.get("action", "") for action in reversible_actions)


__all__ = [
    "create_enhanced_audit_timeline",
    "create_timeline_view",
    "create_graph_view",
    "create_table_view",
    "create_timeline_stats",
]
