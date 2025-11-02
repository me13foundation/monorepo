from typing import List

from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dcc import Checklist, Dropdown

from src.presentation.dash.components.sidebar import create_sidebar


DropdownOption = Dropdown.Options
ChecklistOption = Checklist.Options

IMPORT_TYPE_OPTIONS: List[DropdownOption] = [
    {"label": "ClinVar Data", "value": "clinvar"},
    {"label": "HPO Data", "value": "hpo"},
    {"label": "PubMed Data", "value": "pubmed"},
    {"label": "UniProt Data", "value": "uniprot"},
]

EXPORT_ENTITY_OPTIONS: List[ChecklistOption] = [
    {"label": "Genes", "value": "genes"},
    {"label": "Variants", "value": "variants"},
    {"label": "Phenotypes", "value": "phenotypes"},
    {"label": "Publications", "value": "publications"},
]

EXPORT_FORMAT_OPTIONS: List[DropdownOption] = [
    {"label": "JSON", "value": "json"},
    {"label": "CSV", "value": "csv"},
    {"label": "TSV", "value": "tsv"},
]

BATCH_OPERATION_OPTIONS: List[DropdownOption] = [
    {"label": "Validate All", "value": "validate"},
    {"label": "Normalize IDs", "value": "normalize"},
    {"label": "Cross-reference", "value": "cross_ref"},
    {"label": "Quality Check", "value": "quality"},
]


def create_bulk_page() -> dbc.Container:
    """Create the bulk operations page."""
    return dbc.Container(
        [
            dbc.Row(
                [
                    create_sidebar("/bulk"),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Bulk Operations"),
                                    dbc.CardBody(
                                        [
                                            dbc.Tabs(
                                                [
                                                    dbc.Tab(
                                                        [
                                                            html.H5(
                                                                "Import Data",
                                                                className="mb-3",
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        [
                                                                            dcc.Upload(
                                                                                id="upload-data",
                                                                                children=html.Div(
                                                                                    [
                                                                                        "Drag and drop or click to select files"
                                                                                    ]
                                                                                ),
                                                                                style={
                                                                                    "width": "100%",
                                                                                    "height": "60px",
                                                                                    "lineHeight": "60px",
                                                                                    "borderWidth": "1px",
                                                                                    "borderStyle": "dashed",
                                                                                    "borderRadius": "5px",
                                                                                    "textAlign": "center",
                                                                                    "margin": "10px",
                                                                                },
                                                                                multiple=True,
                                                                            )
                                                                        ],
                                                                        width=6,
                                                                    ),
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Label(
                                                                                "Import Type"
                                                                            ),
                                                                            dcc.Dropdown(
                                                                                id="import-type",
                                                                                options=IMPORT_TYPE_OPTIONS,
                                                                                placeholder="Select data type",
                                                                            ),
                                                                            dbc.Button(
                                                                                "Start Import",
                                                                                id="start-import-btn",
                                                                                color="primary",
                                                                                className="mt-3",
                                                                            ),
                                                                        ],
                                                                        width=6,
                                                                    ),
                                                                ]
                                                            ),
                                                        ],
                                                        label="Import",
                                                        tab_id="import",
                                                    ),
                                                    dbc.Tab(
                                                        [
                                                            html.H5(
                                                                "Export Data",
                                                                className="mb-3",
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Label(
                                                                                "Entity Types"
                                                                            ),
                                                                            dcc.Checklist(
                                                                                id="export-types",
                                                                                options=EXPORT_ENTITY_OPTIONS,
                                                                                value=[
                                                                                    "genes"
                                                                                ],
                                                                            ),
                                                                        ],
                                                                        width=4,
                                                                    ),
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Label(
                                                                                "Format"
                                                                            ),
                                                                            dcc.Dropdown(
                                                                                id="export-format",
                                                                                options=EXPORT_FORMAT_OPTIONS,
                                                                                value="json",
                                                                            ),
                                                                        ],
                                                                        width=4,
                                                                    ),
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Button(
                                                                                "Export Data",
                                                                                id="export-data-btn",
                                                                                color="success",
                                                                                className="mt-4",
                                                                            )
                                                                        ],
                                                                        width=4,
                                                                    ),
                                                                ]
                                                            ),
                                                        ],
                                                        label="Export",
                                                        tab_id="export",
                                                    ),
                                                    dbc.Tab(
                                                        [
                                                            html.H5(
                                                                "Batch Processing",
                                                                className="mb-3",
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Label(
                                                                                "Operation"
                                                                            ),
                                                                            dcc.Dropdown(
                                                                                id="batch-operation",
                                                                                options=BATCH_OPERATION_OPTIONS,
                                                                                placeholder="Select operation",
                                                                            ),
                                                                        ],
                                                                        width=6,
                                                                    ),
                                                                    dbc.Col(
                                                                        [
                                                                            dbc.Button(
                                                                                "Start Batch",
                                                                                id="start-batch-btn",
                                                                                color="warning",
                                                                                className="mt-4",
                                                                            )
                                                                        ],
                                                                        width=6,
                                                                    ),
                                                                ]
                                                            ),
                                                            html.Div(
                                                                id="batch-progress-container",
                                                                className="mt-4",
                                                            ),
                                                        ],
                                                        label="Batch",
                                                        tab_id="batch",
                                                    ),
                                                ],
                                                id="bulk-tabs",
                                                active_tab="import",
                                            )
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=9,
                    ),
                ]
            )
        ],
        fluid=True,
    )


__all__ = ["create_bulk_page"]
