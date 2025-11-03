"""
Evidence Comparison Component for MED13 Curation Dashboard.

Provides side-by-side comparison of evidence from multiple sources with conflict detection.
"""

from typing import Any, Dict, List

from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from src.presentation.dash.components.curation.clinical_card import (
    get_clinical_significance_color,
    get_evidence_level_color,
)


def create_evidence_comparison_panel(variant_data: Dict[str, Any]) -> dbc.Card:
    """
    Create an evidence comparison panel showing side-by-side analysis of evidence sources.

    Args:
        variant_data: Dictionary containing variant information with evidence records

    Returns:
        Bootstrap Card containing evidence comparison interface
    """
    evidence_records = variant_data.get("evidence_records", [])

    if not evidence_records:
        return dbc.Card(
            [
                dbc.CardHeader("Evidence Comparison"),
                dbc.CardBody(
                    [
                        dbc.Alert(
                            "No evidence records available for comparison.",
                            color="info",
                        )
                    ]
                ),
            ]
        )

    # Group evidence by source (simplified - would need source tracking)
    source_groups = _group_evidence_by_source(evidence_records)

    # Detect conflicts
    conflicts: List[Dict[str, Any]] = _detect_evidence_conflicts(evidence_records)

    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H5("Evidence Comparison", className="mb-0"),
                    _create_conflict_summary_badge(conflicts),
                ]
            ),
            dbc.CardBody(
                [
                    # Conflict alerts
                    _create_conflict_alerts(conflicts),
                    # Source comparison matrix
                    _create_source_comparison_matrix(source_groups),
                    # Evidence strength visualization
                    _create_evidence_strength_chart(evidence_records),
                    # Detailed evidence table
                    _create_evidence_details_table(evidence_records),
                ]
            ),
        ]
    )


def _group_evidence_by_source(
    evidence_records: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Group evidence records by source for comparison."""
    # For now, group by evidence type as proxy for source
    # In a full implementation, this would use actual source metadata
    source_groups: Dict[str, List[Dict[str, Any]]] = {}
    for evidence in evidence_records:
        source = evidence.get("evidence_type", "unknown")
        if source not in source_groups:
            source_groups[source] = []
        source_groups[source].append(evidence)

    return source_groups


def _detect_evidence_conflicts(
    evidence_records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Detect conflicts in evidence records.

    Returns list of conflict descriptions with severity levels.
    """
    conflicts: List[Dict[str, Any]] = []

    if not evidence_records:
        return conflicts

    # Check for clinical significance conflicts
    significances: List[str] = [
        str(ev.get("clinical_significance"))
        for ev in evidence_records
        if ev.get("clinical_significance")
    ]
    if len(set(significances)) > 1 and len(significances) > 1:
        conflicts.append(
            {
                "type": "clinical_significance",
                "severity": "high",
                "title": "Clinical Significance Disagreement",
                "description": f'Multiple significance classifications: {", ".join(significances)}',
                "sources": len(set(significances)),
            }
        )

    # Check for evidence level conflicts
    levels: List[str] = [
        str(ev.get("evidence_level"))
        for ev in evidence_records
        if ev.get("evidence_level")
    ]
    if len(set(levels)) > 1 and len(levels) > 1:
        conflicts.append(
            {
                "type": "evidence_level",
                "severity": "medium",
                "title": "Evidence Strength Disagreement",
                "description": f'Conflicting evidence levels: {", ".join(levels)}',
                "sources": len(set(levels)),
            }
        )

    # Check for confidence score conflicts
    confidences = [
        ev.get("confidence", 0) for ev in evidence_records if ev.get("confidence")
    ]
    if confidences and max(confidences) - min(confidences) > 0.5:
        conflicts.append(
            {
                "type": "confidence",
                "severity": "low",
                "title": "Confidence Score Variation",
                "description": f"Wide range in confidence scores: {min(confidences):.1f} - {max(confidences):.1f}",
                "sources": len(confidences),
            }
        )

    return conflicts


def _create_conflict_summary_badge(conflicts: List[Dict[str, Any]]) -> dbc.Badge:
    """Create a summary badge showing number and severity of conflicts."""
    if not conflicts:
        return dbc.Badge("No Conflicts", color="success")

    high_conflicts = len([c for c in conflicts if c["severity"] == "high"])
    total_conflicts = len(conflicts)

    if high_conflicts > 0:
        return dbc.Badge(
            f"{total_conflicts} Conflicts ({high_conflicts} High)", color="danger"
        )
    elif total_conflicts > 0:
        return dbc.Badge(f"{total_conflicts} Conflicts", color="warning")
    else:
        return dbc.Badge("No Conflicts", color="success")


def _create_conflict_alerts(conflicts: List[Dict[str, Any]]) -> html.Div:
    """Create alert components for detected conflicts."""
    if not conflicts:
        return html.Div()

    alerts = []
    for conflict in conflicts:
        color_map = {"high": "danger", "medium": "warning", "low": "info"}
        color = color_map.get(conflict["severity"], "info")

        alerts.append(
            dbc.Alert(
                [
                    html.H6(
                        [
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            conflict["title"],
                        ]
                    ),
                    html.P(conflict["description"], className="mb-0"),
                ],
                color=color,
                className="mb-3",
            )
        )

    return html.Div(alerts)


def _create_source_comparison_matrix(
    source_groups: Dict[str, List[Dict[str, Any]]],
) -> dbc.Table:
    """Create a comparison matrix showing evidence by source."""
    if not source_groups:
        return dbc.Table()

    # Create table headers
    headers = [html.Th("Aspect")] + [
        html.Th(source.title()) for source in source_groups.keys()
    ]

    # Create table rows for different aspects
    rows = []

    # Clinical significance row
    sig_row = [html.Td("Clinical Significance")]
    for source, evidence_list in source_groups.items():
        significances = [
            ev.get("clinical_significance", "Unknown")
            for ev in evidence_list
            if ev.get("clinical_significance")
        ]
        if significances:
            sig_badge = dbc.Badge(
                significances[0],
                style={
                    "backgroundColor": get_clinical_significance_color(significances[0])
                },
                className="text-white",
            )
            sig_row.append(html.Td(sig_badge))
        else:
            sig_row.append(html.Td("Not specified"))
    rows.append(html.Tr(sig_row))

    # Evidence level row
    level_row = [html.Td("Evidence Level")]
    for source, evidence_list in source_groups.items():
        levels = [
            ev.get("evidence_level", "Unknown")
            for ev in evidence_list
            if ev.get("evidence_level")
        ]
        if levels:
            level_badge = dbc.Badge(
                levels[0].title(),
                style={"backgroundColor": get_evidence_level_color(levels[0])},
                className="text-white",
            )
            level_row.append(html.Td(level_badge))
        else:
            level_row.append(html.Td("Not specified"))
    rows.append(html.Tr(level_row))

    # Confidence row
    conf_row = [html.Td("Confidence")]
    for source, evidence_list in source_groups.items():
        confidences = [
            ev.get("confidence", 0) for ev in evidence_list if ev.get("confidence")
        ]
        if confidences:
            conf_value = confidences[0]
            conf_row.append(html.Td(f"{conf_value:.2f}"))
        else:
            conf_row.append(html.Td("Not specified"))
    rows.append(html.Tr(conf_row))

    # Evidence count row
    count_row = [html.Td("Evidence Count")]
    for source, evidence_list in source_groups.items():
        count_row.append(html.Td(str(len(evidence_list))))
    rows.append(html.Tr(count_row))

    return dbc.Table(
        [html.Thead(html.Tr(headers)), html.Tbody(rows)],
        bordered=True,
        hover=True,
        responsive=True,
        className="mb-3",
    )


def _create_evidence_strength_chart(
    evidence_records: List[Dict[str, Any]],
) -> dcc.Graph:
    """Create a chart visualizing evidence strength distribution."""
    if not evidence_records:
        return dcc.Graph()

    # Count evidence by level
    level_counts: Dict[str, int] = {}
    for evidence in evidence_records:
        level = evidence.get("evidence_level", "unknown")
        level_counts[level] = level_counts.get(level, 0) + 1

    # Create bar chart
    levels = list(level_counts.keys())
    counts = list(level_counts.values())

    # Color mapping for levels
    colors = [get_evidence_level_color(level) for level in levels]

    fig = go.Figure(
        data=[
            go.Bar(
                x=levels,
                y=counts,
                marker_color=colors,
                text=counts,
                textposition="auto",
            )
        ]
    )

    fig.update_layout(
        title="Evidence Strength Distribution",
        xaxis_title="Evidence Level",
        yaxis_title="Count",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
    )

    return dcc.Graph(figure=fig, className="mb-3")


def _create_evidence_details_table(evidence_records: List[Dict[str, Any]]) -> dbc.Table:
    """Create a detailed table of all evidence records."""
    if not evidence_records:
        return dbc.Table()

    headers = [
        html.Th("Type"),
        html.Th("Level"),
        html.Th("Confidence"),
        html.Th("Description"),
        html.Th("Source"),
    ]

    rows = []
    for evidence in evidence_records:
        level_color = get_evidence_level_color(
            evidence.get("evidence_level", "unknown")
        )

        row = html.Tr(
            [
                html.Td(evidence.get("evidence_type", "Unknown").title()),
                html.Td(
                    dbc.Badge(
                        evidence.get("evidence_level", "Unknown").title(),
                        style={"backgroundColor": level_color, "color": "white"},
                    )
                ),
                html.Td(f"{evidence.get('confidence', 0):.2f}"),
                html.Td(
                    evidence.get("description", "No description")[:100] + "..."
                    if len(evidence.get("description", "")) > 100
                    else evidence.get("description", "No description")
                ),
                html.Td(evidence.get("source", "Unknown")),
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


__all__ = [
    "create_evidence_comparison_panel",
    "_detect_evidence_conflicts",
    "_create_source_comparison_matrix",
    "_create_evidence_strength_chart",
]
