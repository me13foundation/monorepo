from dash import html
import dash_bootstrap_components as dbc


def create_header() -> dbc.Navbar:
    """Create application header with navigation."""
    return dbc.Navbar(
        dbc.Container(
            [
                dbc.NavbarBrand(
                    [
                        html.I(className="fas fa-dna me-2"),
                        "MED13 Resource Library - Curation Dashboard",
                    ],
                    href="/",
                ),
                dbc.NavbarToggler(id="navbar-toggler"),
                dbc.Collapse(
                    [
                        dbc.Nav(
                            [
                                dbc.NavItem(
                                    dbc.NavLink(
                                        "Dashboard", href="/dashboard", active="exact"
                                    )
                                ),
                                dbc.NavItem(
                                    dbc.NavLink(
                                        "Review Queue", href="/review", active="exact"
                                    )
                                ),
                                dbc.NavItem(
                                    dbc.NavLink(
                                        "Bulk Operations", href="/bulk", active="exact"
                                    )
                                ),
                                dbc.NavItem(
                                    dbc.NavLink(
                                        "Reports", href="/reports", active="exact"
                                    )
                                ),
                                dbc.NavItem(
                                    dbc.NavLink(
                                        "Data Sources",
                                        href="/data-sources",
                                        active="exact",
                                    )
                                ),
                                dbc.NavItem(
                                    dbc.NavLink(
                                        "Settings", href="/settings", active="exact"
                                    )
                                ),
                            ],
                            navbar=True,
                        ),
                        html.Div(
                            dbc.Badge("Live", color="success", className="ms-2"),
                            className="d-flex align-items-center",
                        ),
                    ],
                    id="navbar-collapse",
                    navbar=True,
                ),
            ]
        ),
        color="dark",
        dark=True,
        className="mb-4",
    )


__all__ = ["create_header"]
