"""
Curation Dashboard Components.

Clinical-focused UI components for the MED13 curation workflow.
"""

from .clinical_card import (
    create_clinical_review_card,
    create_clinical_card_grid,
    create_enhanced_filters,
    get_clinical_significance_color,
    get_evidence_level_color,
)
from .clinical_viewer import (
    create_clinical_viewer,
    create_confidence_gauge,
    create_summary_tab,
    create_genomic_tab,
    create_evidence_tab,
    create_phenotypes_tab,
    create_literature_tab,
)
from .evidence_comparison import (
    create_evidence_comparison_panel,
)
from .conflict_resolver import (
    create_conflict_resolution_panel,
    create_quick_conflict_resolver,
)
from .annotation_panel import (
    create_annotation_panel,
    create_quick_decision_rationale,
    create_annotation_templates,
)
from .progress_analytics import (
    create_progress_analytics_dashboard,
    create_completion_gauge,
    create_conflict_resolution_stats,
    create_team_productivity_metrics,
    create_quality_trends,
    create_progress_timeline_chart,
    create_conflict_heatmap,
    create_curator_performance_table,
    create_variant_category_breakdown,
    create_recent_activity_feed,
    create_bulk_resolution_tools,
)
from .audit_timeline import (
    create_enhanced_audit_timeline,
    create_timeline_view,
    create_graph_view,
    create_table_view,
    create_timeline_stats,
)
from .bulk_resolution import (
    create_bulk_resolution_panel,
    create_quick_actions,
    create_batch_processing,
    create_bulk_selection,
    create_bulk_preview,
    create_action_summary,
    create_bulk_workflow_templates,
)

__all__ = [
    # Clinical Cards
    "create_clinical_review_card",
    "create_clinical_card_grid",
    "create_enhanced_filters",
    "get_clinical_significance_color",
    "get_evidence_level_color",
    # Clinical Viewer
    "create_clinical_viewer",
    "create_confidence_gauge",
    "create_summary_tab",
    "create_genomic_tab",
    "create_evidence_tab",
    "create_phenotypes_tab",
    "create_literature_tab",
    # Evidence Comparison
    "create_evidence_comparison_panel",
    # Conflict Resolution
    "create_conflict_resolution_panel",
    "create_quick_conflict_resolver",
    # Annotation Panel
    "create_annotation_panel",
    "create_quick_decision_rationale",
    "create_annotation_templates",
    # Progress Analytics
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
    # Audit Timeline
    "create_enhanced_audit_timeline",
    "create_timeline_view",
    "create_graph_view",
    "create_table_view",
    "create_timeline_stats",
    # Bulk Resolution
    "create_bulk_resolution_panel",
    "create_quick_actions",
    "create_batch_processing",
    "create_bulk_selection",
    "create_bulk_preview",
    "create_action_summary",
    "create_bulk_workflow_templates",
]
