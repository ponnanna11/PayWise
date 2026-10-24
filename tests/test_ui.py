"""
UI Tests for PayWise Streamlit Application.
Tests page loading, navigation transitions, component rendering, and error states.
"""
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from paywise.views.components import (
    render_status_badge,
    render_metric_card,
    render_severity_callout,
    render_before_after_comparison,
    render_empty_state,
)

APP_PATH = str((Path(__file__).resolve().parent.parent / "app.py").resolve())


def test_ui_components_markup_generation():
    """Verifies that reusable UI components render valid markup without errors."""
    badge_html = render_status_badge("COMMITTED_SIMULATED")
    assert "COMMITTED" in badge_html
    assert "pw-badge-success" in badge_html

    blocked_badge = render_status_badge("BLOCKED")
    assert "BLOCKED" in blocked_badge
    assert "pw-badge-block" in blocked_badge


def test_apptest_loads_dashboard_without_exception():
    """Scenario: Verifies that app.py initializes and renders the Dashboard successfully."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception
    # Check that navigation radio exists
    assert len(at.sidebar.radio) > 0


def test_apptest_navigation_all_pages():
    """Scenario: Cycles through all pages to ensure no unhandled exceptions on render."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception

    # Available nav options in sidebar radio
    pages = [
        "Dashboard",
        "Proposals",
        "New Proposal",
        "Simulation & Preview",
        "Approvals",
        "Policy Management",
        "Ledger",
        "Audit Trail",
        "System Information",
    ]

    for page_name in pages:
        at.sidebar.radio[0].set_value(page_name).run()
        assert not at.exception, f"Exception occurred while rendering page: {page_name}"
