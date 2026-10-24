"""
Operations Dashboard View for PayWise.
Displays live treasury cash, reserves, liquidity, pending outflows, risk alerts, and audit events.
"""
import streamlit as st
import pandas as pd
from paywise.repositories.account_repo import AccountRepository
from paywise.repositories.proposal_repo import ProposalRepository
from paywise.repositories.audit_repo import AuditRepository
from paywise.services.ai_adapter import AIAdapter
from paywise.utils.formatters import format_inr, format_date
from paywise.views.components import (
    render_page_header,
    render_simulation_banner,
    render_metric_card,
    render_ai_status_card,
    render_severity_callout,
    render_empty_state,
)


def render_dashboard(db_path: str):
    render_page_header(
        "Financial Operations Dashboard",
        "Real-time governance gateway monitoring simulated treasury liquidity, proposed batches, and safety barriers.",
    )
    render_simulation_banner()

    acc_repo = AccountRepository(db_path)
    prop_repo = ProposalRepository(db_path)
    audit_repo = AuditRepository(db_path)
    ai_adapter = AIAdapter()

    # AI Runtime Health Indicator
    ai_health = ai_adapter.check_health()
    render_ai_status_card(ai_health)

    accounts = acc_repo.list_all()
    proposals = prop_repo.list_all()
    audit_events = audit_repo.list_all(limit=10)

    total_cash = sum(a.current_balance for a in accounts)
    total_reserved = sum(a.reserved_balance for a in accounts)
    total_available = sum(a.available_funds for a in accounts)

    pending_proposals = [p for p in proposals if p.status.value in ["DRAFT", "SIMULATED", "AWAITING_APPROVAL"]]
    awaiting_approval = [p for p in proposals if p.status.value == "AWAITING_APPROVAL"]
    blocked_proposals = [p for p in proposals if p.status.value == "BLOCKED"]
    total_pending_outflow = sum(p.total_amount for p in pending_proposals)

    # Top KPI Metrics Row
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1:
        render_metric_card("Simulated Cash", format_inr(total_cash), f"{len(accounts)} Accounts")
    with k2:
        render_metric_card("Reserved Funds", format_inr(total_reserved), "Mandatory Floor", value_color="#475569")
    with k3:
        render_metric_card("Available Funds", format_inr(total_available), "Liquid & Safe", value_color="#0D9488")
    with k4:
        render_metric_card("Pending Outflow", format_inr(total_pending_outflow), f"{len(pending_proposals)} Batches", value_color="#2563EB")
    with k5:
        render_metric_card("Awaiting Sign-off", str(len(awaiting_approval)), "Needs Manager Approval", value_color="#D97706")
    with k6:
        render_metric_card("Blocked Proposals", str(len(blocked_proposals)), "Safety Policy Barrier", value_color="#DC2626")

    st.markdown("<div style='margin-top: 1.25rem;'></div>", unsafe_allow_html=True)

    # Middle Row: Treasury Accounts & Active Proposals
    col_left, col_right = st.columns([1.1, 1.4])

    with col_left:
        st.subheader("🏦 Treasury Accounts Overview")
        for acc in accounts:
            with st.container(border=True):
                c1, c2 = st.columns([1.5, 1])
                with c1:
                    st.markdown(f"**{acc.account_name}**")
                    st.caption(f"{acc.bank_name} • `{acc.account_number}`")
                with c2:
                    st.markdown(f"<h4 style='margin:0; text-align:right;'>{format_inr(acc.current_balance)}</h4>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin:0; font-size:0.75rem; color:#0D9488; text-align:right;'>Available: {format_inr(acc.available_funds)}</p>", unsafe_allow_html=True)

                ratio = min(1.0, max(0.0, acc.reserved_balance / acc.current_balance)) if acc.current_balance > 0 else 0
                st.progress(ratio, text=f"Mandatory Reserve: {format_inr(acc.reserved_balance)} ({ratio*100:.1f}%)")

    with col_right:
        st.subheader("📋 Active Financial Proposals")
        if not proposals:
            render_empty_state("No Proposals Found", "Create a new financial proposal to begin simulation.", icon="📝")
        else:
            table_data = []
            for p in proposals[:6]:
                table_data.append({
                    "Proposal ID": p.id,
                    "Title": p.title,
                    "Source": p.source,
                    "Amount": format_inr(p.total_amount),
                    "Status": p.status.value,
                    "Created": format_date(p.created_at),
                })
            st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

    # Bottom Row: Safety Interceptions & Audit Trail
    st.markdown("<div style='margin-top: 1.25rem;'></div>", unsafe_allow_html=True)
    b_left, b_right = st.columns(2)

    with b_left:
        st.subheader("⚠️ Recent Safety Findings & Policy Interceptions")
        violation_events = [e for e in audit_events if e.event_type.value in ["POLICY_VIOLATION_DETECTED", "REVALIDATION_FAILED"]]
        if not violation_events:
            st.success("✅ **Zero Recent Safety Violations**: All recent financial operations conformed to active safety rules.")
        else:
            for ev in violation_events[:3]:
                rule = ev.details.get("rule_name") or ev.details.get("revalidation_failure") or "Policy Rule"
                expl = ev.details.get("explanation") or ev.details.get("revalidation_failure") or ""
                render_severity_callout(
                    severity=ev.outcome,
                    rule_name=rule,
                    explanation=expl,
                    policy_id=ev.details.get("policy_id", ""),
                )

    with b_right:
        st.subheader("📜 Recent Governance Audit Events")
        if not audit_events:
            render_empty_state("No Audit Events", "No historical audit records logged yet.", icon="📜")
        else:
            audit_rows = []
            for ev in audit_events[:6]:
                audit_rows.append({
                    "Timestamp": format_date(ev.timestamp),
                    "Event": ev.event_type.value,
                    "Proposal": ev.proposal_id or "-",
                    "Actor": ev.actor,
                    "Outcome": ev.outcome,
                })
            st.dataframe(pd.DataFrame(audit_rows), use_container_width=True, hide_index=True)
