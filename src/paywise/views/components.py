"""
Reusable UI component library for PayWise.
Enforces consistent visual hierarchy, accessible contrast, semantic status indicators,
and standard layout patterns.
"""
from typing import Any, Dict, Optional
import streamlit as st
from paywise.utils.formatters import format_inr


def render_page_header(title: str, subtitle: str = ""):
    """Renders a standardized page header with clean typography."""
    st.markdown(
        f"""
        <div class="pw-page-header">
            <h1 class="pw-page-title">{title}</h1>
            {f'<div class="pw-page-subtitle">{subtitle}</div>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_simulation_banner():
    """Renders the standard simulation-only sandbox notice."""
    st.markdown(
        """
        <div class="pw-simulation-banner">
            <span>🛡️ <b>Pre-Execution Simulation Environment</b>: PayWise models financial outcomes in an isolated virtual sandbox. No live banking APIs or real fund disbursements are executed.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: str, subtext: str = "", value_color: Optional[str] = None):
    """Renders a minimalist SaaS metric card."""
    color_style = f"style='color: {value_color};'" if value_color else ""
    st.markdown(
        f"""
        <div class="pw-metric-card">
            <div class="pw-metric-label">{label}</div>
            <div class="pw-metric-value" {color_style}>{value}</div>
            {f'<div class="pw-metric-subtext">{subtext}</div>' if subtext else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


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
    """Renders structured policy engine finding callout."""
    sev = str(severity).upper()
    card_cls = "pw-finding-block" if sev == "BLOCK" else "pw-finding-approval" if sev == "REQUIRE_APPROVAL" else "pw-finding-warn"
    badge_cls = "pw-badge-block" if sev == "BLOCK" else "pw-badge-approval" if sev == "REQUIRE_APPROVAL" else "pw-badge-warn"
    icon = "🛑" if sev == "BLOCK" else "⚠️" if sev == "REQUIRE_APPROVAL" else "ℹ️"

    pid_html = f"<span style='font-size:0.75rem; font-weight:600; color:#64748B;'>{policy_id}</span>" if policy_id else ""
    remedy_html = f"<div style='margin-top:0.4rem; font-size:0.85rem; color:#0D9488;'><b>Corrective Action:</b> {recommended_action}</div>" if recommended_action else ""

    st.markdown(
        f"""
        <div class="pw-finding-card {card_cls}">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="pw-badge {badge_cls}">{icon} {sev}</span>
                {pid_html}
            </div>
            <div style="font-weight:600; font-size:0.975rem; color:#0F172A; margin-top:0.4rem;">{rule_name}</div>
            <div style="font-size:0.875rem; color:#334155; margin-top:0.25rem; line-height:1.45;">{explanation}</div>
            {remedy_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


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
            subtext=f"Account: {account_id}",
        )

    with col2:
        projected_color = "#DC2626" if projected_balance < reserved_balance else "#0D9488"
        render_metric_card(
            "Projected Ledger Balance",
            format_inr(projected_balance),
            subtext=f"Net proposed outflow: -{format_inr(total_outflow)}",
            value_color=projected_color,
        )

    with col3:
        render_metric_card(
            "Mandatory Safety Reserve",
            format_inr(reserved_balance),
            subtext="Protected liquidity floor",
            value_color="#475569",
        )

    with col4:
        avail_color = "#0D9488" if available_after > 0 else "#DC2626"
        render_metric_card(
            "Available Funds After Batch",
            format_inr(available_after),
            subtext=f"Prior available: {format_inr(available_before)}",
            value_color=avail_color,
        )


def render_empty_state(title: str, message: str, icon: str = "📁"):
    """Renders an empty state placeholder."""
    st.markdown(
        f"""
        <div class="pw-empty-state">
            <div style="font-size: 2.25rem; margin-bottom: 0.5rem;">{icon}</div>
            <div style="font-weight: 600; font-size: 1.05rem; color: #1E293B;">{title}</div>
            <div style="font-size: 0.875rem; color: #64748B; margin-top: 0.25rem; max-width: 450px; margin-left: auto; margin-right: auto;">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ai_status_card(health: Dict[str, Any]):
    """Renders the AI Agent runtime status indicator."""
    status = health.get("status", "UNCONFIGURED")
    provider = health.get("provider", "Unknown")
    model = health.get("model", "Default")
    message = health.get("message", "")

    if status == "AVAILABLE":
        border_color = "#10B981"
        badge_cls = "pw-badge-success"
        icon = "🟢"
    elif status == "FALLBACK_ACTIVE":
        border_color = "#3B82F6"
        badge_cls = "pw-badge-warn"
        icon = "⚡"
    else:
        border_color = "#F59E0B"
        badge_cls = "pw-badge-approval"
        icon = "⚠️"

    st.markdown(
        f"""
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-left:4px solid {border_color}; border-radius:8px; padding:0.9rem 1.25rem; margin-bottom:1rem;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="font-weight:600; color:#0F172A;">{icon} AI Agent Runtime: {provider}</div>
                <span class="pw-badge {badge_cls}">{status}</span>
            </div>
            <div style="font-size:0.825rem; color:#64748B; margin-top:0.35rem;">
                <b>Model</b>: <code>{model}</code> • {message}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
