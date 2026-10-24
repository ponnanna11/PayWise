"""
Reusable UI component library for PayWise.
Enforces consistent visual hierarchy, accessible contrast, semantic status indicators,
standard light-fintech layout patterns, and eliminates markdown code-block parsing bugs.
"""
import html
import textwrap
from typing import Any, Dict, Optional
import streamlit as st
from paywise.utils.formatters import format_inr


def render_page_header(title: str, subtitle: str = ""):
    """Renders a standardized page header with clean typography."""
    escaped_title = html.escape(title)
    escaped_sub = html.escape(subtitle) if subtitle else ""
    sub_html = f'<div class="pw-page-subtitle">{escaped_sub}</div>' if escaped_sub else ""
    markup = textwrap.dedent(f"""
        <div class="pw-page-header">
            <h1 class="pw-page-title">{escaped_title}</h1>
            {sub_html}
        </div>
    """).strip()
    st.markdown(markup, unsafe_allow_html=True)


def render_simulation_banner():
    """
    Deprecated: Simulation banner has been removed everywhere as requested.
    Kept as a no-op for backward compatibility with existing imports.
    """
    pass


def render_metric_card(label: str, value: str, subtext: str = "", value_color: Optional[str] = None):
    """Renders a minimalist SaaS metric card."""
    color_style = f"style='color: {value_color};'" if value_color else ""
    sub_html = f'<div class="pw-metric-subtext">{html.escape(subtext)}</div>' if subtext else ""
    markup = textwrap.dedent(f"""
        <div class="pw-metric-card">
            <div class="pw-metric-label">{html.escape(label)}</div>
            <div class="pw-metric-value" {color_style}>{html.escape(value)}</div>
            {sub_html}
        </div>
    """).strip()
    st.markdown(markup, unsafe_allow_html=True)


def render_status_badge(status: str) -> str:
    """Returns an HTML badge for proposal and transaction states."""
    status_upper = str(status).upper()
    badges = {
        "COMMITTED_SIMULATED": ("pw-badge-success", "✓ COMMITTED"),
        "APPROVED": ("pw-badge-success", "✓ APPROVED"),
        "AWAITING_APPROVAL": ("pw-badge-approval", "⏳ AWAITING APPROVAL"),
        "SIMULATED": ("pw-badge-warn", "⚡ SIMULATED"),
        "BLOCKED": ("pw-badge-block", "✕ BLOCKED"),
        "REJECTED": ("pw-badge-block", "✕ REJECTED"),
        "STALE": ("pw-badge-approval", "⚠️ STALE"),
        "DRAFT": ("pw-badge-neutral", "✎ DRAFT"),
        "VALID": ("pw-badge-success", "✓ VALID"),
        "NEEDS_APPROVAL": ("pw-badge-approval", "⏳ NEEDS APPROVAL"),
        "WARN": ("pw-badge-warn", "ℹ WARN"),
        "BLOCK": ("pw-badge-block", "✕ BLOCK"),
        "REQUIRE_APPROVAL": ("pw-badge-approval", "⏳ REQUIRE APPROVAL"),
    }
    cls, label = badges.get(status_upper, ("pw-badge-neutral", status_upper))
    return f"<span class='pw-badge {cls}'>{label}</span>"


def render_severity_callout(
    severity: str,
    rule_name: str,
    explanation: str,
    recommended_action: str = "",
    policy_id: str = "",
):
    """
    Renders structured policy engine finding callout as a clean light card.
    Uses dedented, unindented HTML so markdown parsers never mistake it for a code block.
    """
    sev = str(severity).upper()
    card_cls = "pw-finding-block" if sev == "BLOCK" else "pw-finding-approval" if sev == "REQUIRE_APPROVAL" else "pw-finding-warn"
    badge_cls = "pw-badge-block" if sev == "BLOCK" else "pw-badge-approval" if sev == "REQUIRE_APPROVAL" else "pw-badge-warn"
    icon = "🛑" if sev == "BLOCK" else "⚠️" if sev == "REQUIRE_APPROVAL" else "ℹ️"

    pid_html = f"<span style='font-size:0.825rem; font-weight:600; color:#526581;'>{html.escape(policy_id)}</span>" if policy_id else ""
    remedy_html = (
        f"<div class='pw-finding-remedy'><b>Recommended Action:</b> {html.escape(recommended_action)}</div>"
        if recommended_action
        else ""
    )

    markup = textwrap.dedent(f"""
        <div class="pw-finding-card {card_cls}">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="pw-badge {badge_cls}">{icon} {sev}</span>
                {pid_html}
            </div>
            <div class="pw-finding-title">{html.escape(rule_name)}</div>
            <div class="pw-finding-desc">{html.escape(explanation)}</div>
            {remedy_html}
        </div>
    """).strip()

    st.markdown(markup, unsafe_allow_html=True)


def render_before_after_comparison(
    current_balance: float,
    projected_balance: float,
    reserved_balance: float,
    available_before: float,
    available_after: float,
    total_outflow: float,
    account_id: str = "",
):
    """Renders 4-column before-and-after financial comparison grid."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric_card(
            "Current Ledger Balance",
            format_inr(current_balance),
            subtext=f"Account: {account_id}" if account_id else "Starting Balance",
        )

    with col2:
        projected_color = "#DC2626" if projected_balance < reserved_balance else "#16A34A"
        render_metric_card(
            "Projected Balance",
            format_inr(projected_balance),
            subtext=f"Proposed outflow: -{format_inr(total_outflow)}",
            value_color=projected_color,
        )

    with col3:
        render_metric_card(
            "Mandatory Reserve",
            format_inr(reserved_balance),
            subtext="Protected liquidity floor",
            value_color="#172554",
        )

    with col4:
        avail_color = "#16A34A" if available_after > 0 else "#DC2626"
        render_metric_card(
            "Available Funds After Batch",
            format_inr(available_after),
            subtext=f"Prior available: {format_inr(available_before)}",
            value_color=avail_color,
        )


def render_empty_state(title: str, message: str, icon: str = "📁"):
    """Renders an empty state placeholder."""
    markup = textwrap.dedent(f"""
        <div class="pw-empty-state">
            <div style="font-size: 2.25rem; margin-bottom: 0.5rem;">{icon}</div>
            <div style="font-weight: 600; font-size: 1.1rem; color: #172554;">{html.escape(title)}</div>
            <div style="font-size: 0.925rem; color: #526581; margin-top: 0.35rem; max-width: 450px; margin-left: auto; margin-right: auto; line-height: 1.5;">{html.escape(message)}</div>
        </div>
    """).strip()
    st.markdown(markup, unsafe_allow_html=True)


def render_ai_status_card(health: Dict[str, Any]):
    """Renders the AI Agent runtime status indicator."""
    status = health.get("status", "UNCONFIGURED")
    provider = health.get("provider", "Unknown")
    model = health.get("model", "Default")
    message = health.get("message", "")

    if status == "AVAILABLE":
        border_color = "#16A34A"
        badge_cls = "pw-badge-success"
        icon = "🟢"
    elif status == "FALLBACK_ACTIVE":
        border_color = "#2563EB"
        badge_cls = "pw-badge-warn"
        icon = "⚡"
    else:
        border_color = "#D97706"
        badge_cls = "pw-badge-approval"
        icon = "⚠️"

    markup = textwrap.dedent(f"""
        <div style="background:#FFFFFF; border:1px solid #DCE6F5; border-left:4px solid {border_color}; border-radius:10px; padding:1rem 1.35rem; margin-bottom:1rem; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.02);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="font-weight:600; font-size:1rem; color:#172554;">{icon} AI Agent Runtime: {html.escape(provider)}</div>
                <span class="pw-badge {badge_cls}">{html.escape(status)}</span>
            </div>
            <div style="font-size:0.875rem; color:#526581; margin-top:0.4rem; line-height:1.45;">
                <b>Model</b>: <code>{html.escape(model)}</code> • {html.escape(message)}
            </div>
        </div>
    """).strip()

    st.markdown(markup, unsafe_allow_html=True)
