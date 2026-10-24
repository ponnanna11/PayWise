"""
Reusable UI component library for PayWise.
Enforces consistent visual hierarchy, accessible contrast, semantic status indicators,
standard light-fintech layout patterns, and eliminates markdown code-block parsing bugs.
"""
import html
from typing import Any, Dict, Optional
import streamlit as st
from paywise.utils.formatters import format_inr


def render_page_header(title: str, subtitle: str = ""):
    """Renders a standardized page header with clean typography."""
    escaped_title = html.escape(title)
    escaped_sub = html.escape(subtitle) if subtitle else ""
    sub_html = f'<div class="pw-page-subtitle">{escaped_sub}</div>' if escaped_sub else ""
    markup = f'<div class="pw-page-header"><h1 class="pw-page-title">{escaped_title}</h1>{sub_html}</div>'
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
    markup = (
        f'<div class="pw-metric-card">'
        f'<div class="pw-metric-label">{html.escape(label)}</div>'
        f'<div class="pw-metric-value" {color_style}>{html.escape(value)}</div>'
        f'{sub_html}'
        f'</div>'
    )
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
    Uses native Streamlit containers to eliminate markdown parsing errors,
    prevent raw HTML leaks, and guarantee strict column boundary containment.
    """
    sev = str(severity).upper()
    is_block = sev in ["BLOCK", "REJECTED", "FAILED", "ERROR"]
    is_approval = sev in ["REQUIRE_APPROVAL", "NEEDS_APPROVAL", "AWAITING_APPROVAL"]
    badge_cls = (
        "pw-badge-block"
        if is_block
        else "pw-badge-approval"
        if is_approval
        else "pw-badge-warn"
    )
    icon = "🛑" if is_block else "⏳" if is_approval else "ℹ️"
    accent_color = (
        "#DC2626"
        if is_block
        else "#D97706"
        if is_approval
        else "#2563EB"
    )
    display_label = "BLOCK" if is_block else "REQUIRE APPROVAL" if is_approval else sev

    clean_rule = html.unescape(str(rule_name))
    clean_expl = html.unescape(str(explanation))
    clean_action = html.unescape(str(recommended_action)) if recommended_action else ""

    with st.container(border=True):
        st.markdown(
            f'<div style="height:3px; background-color:{accent_color}; border-radius:2px; margin-bottom:0.5rem;"></div>',
            unsafe_allow_html=True,
        )
        if policy_id:
            c_badge, c_pid = st.columns([3, 1])
            with c_badge:
                st.markdown(
                    f'<span class="pw-badge {badge_cls}">{icon} {display_label}</span>',
                    unsafe_allow_html=True,
                )
            with c_pid:
                st.markdown(
                    f'<div style="text-align:right; font-size:0.825rem; font-weight:600; color:#526581; line-height:1.8;">{html.escape(policy_id, quote=False)}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                f'<span class="pw-badge {badge_cls}">{icon} {display_label}</span>',
                unsafe_allow_html=True,
            )

        st.markdown(
            f'<div style="font-weight:600; font-size:1.025rem; color:#172554; margin:0.35rem 0 0.25rem 0; line-height:1.35;">{html.escape(clean_rule, quote=False)}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="font-size:0.925rem; color:#374151; line-height:1.5;">{html.escape(clean_expl, quote=False)}</div>',
            unsafe_allow_html=True,
        )

        if clean_action:
            st.markdown(
                f'<div style="margin-top:0.45rem; padding:0.5rem 0.75rem; background:#F8FAFC; border-left:3px solid #2563EB; border-radius:4px; font-size:0.85rem; color:#1E293B;"><b>Recommended Action:</b> {html.escape(clean_action, quote=False)}</div>',
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
    markup = (
        f'<div class="pw-empty-state">'
        f'<div style="font-size: 2.25rem; margin-bottom: 0.5rem;">{icon}</div>'
        f'<div style="font-weight: 600; font-size: 1.1rem; color: #172554;">{html.escape(title)}</div>'
        f'<div style="font-size: 0.925rem; color: #526581; margin-top: 0.35rem; max-width: 450px; margin-left: auto; margin-right: auto; line-height: 1.5;">{html.escape(message)}</div>'
        f'</div>'
    )
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

    markup = (
        f'<div style="background:#FFFFFF; border:1px solid #DCE6F5; border-left:4px solid {border_color}; border-radius:10px; padding:1rem 1.35rem; margin-bottom:1rem; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.02);">'
        f'<div style="display:flex; justify-content:space-between; align-items:center;">'
        f'<div style="font-weight:600; font-size:1rem; color:#172554;">{icon} AI Agent Runtime: {html.escape(provider)}</div>'
        f'<span class="pw-badge {badge_cls}">{html.escape(status)}</span>'
        f'</div>'
        f'<div style="font-size:0.875rem; color:#526581; margin-top:0.4rem; line-height:1.45;">'
        f'<b>Model</b>: <code>{html.escape(model)}</code> • {html.escape(message)}'
        f'</div>'
        f'</div>'
    )
    st.markdown(markup, unsafe_allow_html=True)
