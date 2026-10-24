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
    render_metric_card,
    render_severity_callout,
    render_empty_state,
)


def render_dashboard(db_path: str):
    # Top Section: Title & Short Subtitle (No repeated simulation disclaimer banner!)
    render_page_header(
        "Financial Safety Dashboard",
        "Real-time pre-execution consequence simulation, liquidity reserve management & governance telemetry",
    )

    acc_repo = AccountRepository(db_path)
    prop_repo = ProposalRepository(db_path)
    audit_repo = AuditRepository(db_path)
    ai_adapter = AIAdapter()

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

    # 1. Six Financial Metrics in a Balanced Grid
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1:
        render_metric_card("Simulated Cash", format_inr(total_cash), f"{len(accounts)} Accounts", value_color="#172554")
    with k2:
        render_metric_card("Reserved Funds", format_inr(total_reserved), "Mandatory Liquidity Floor", value_color="#526581")
    with k3:
        render_metric_card("Available Funds", format_inr(total_available), "Liquid & Unencumbered", value_color="#15803D")
    with k4:
        render_metric_card("Pending Outflow", format_inr(total_pending_outflow), f"{len(pending_proposals)} Batch(es)", value_color="#2563EB")
    with k5:
        render_metric_card("Awaiting Sign-off", str(len(awaiting_approval)), "Requires Manager Authorization", value_color="#D97706")
    with k6:
        render_metric_card("Blocked Proposals", str(len(blocked_proposals)), "Policy Violations Intercepted", value_color="#DC2626")

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # 2. Middle Row: Treasury Accounts & Active Proposals
    col_left, col_right = st.columns([1.15, 1.35])

    with col_left:
        st.subheader("🏦 Treasury Accounts Overview")
        for acc in accounts:
            with st.container(border=True):
                c1, c2 = st.columns([1.4, 1])
                with c1:
                    st.markdown(
                        f"<div style='display:flex; flex-direction:column; justify-content:center; min-height:46px;'>"
                        f"<div style='font-weight:600; font-size:1.05rem; color:#172554; line-height:1.3;'>{acc.account_name}</div>"
                        f"<div style='font-size:0.825rem; color:#526581; line-height:1.4; margin-top:2px;'>{acc.bank_name} • Account ending in <code style='font-size:0.8rem;'>...{acc.account_number[-4:]}</code></div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                with c2:
                    st.markdown(
                        f"<div style='display:flex; flex-direction:column; justify-content:center; align-items:flex-end; min-height:46px; text-align:right;'>"
                        f"<div style='font-weight:700; font-size:1.15rem; color:#172554; line-height:1.3;'>{format_inr(acc.current_balance)}</div>"
                        f"<div style='font-size:0.825rem; color:#15803D; font-weight:600; line-height:1.4; margin-top:2px;'>Available: {format_inr(acc.available_funds)}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                ratio = min(1.0, max(0.0, acc.reserved_balance / acc.current_balance)) if acc.current_balance > 0 else 0
                st.progress(ratio, text=f"Mandatory Reserve: {format_inr(acc.reserved_balance)} ({ratio*100:.1f}%)")

    with col_right:
        st.subheader("📋 Active Financial Proposals")
        if not proposals:
            render_empty_state("No Proposals Found", "Create a new financial proposal to begin pre-execution simulation.", icon="📝")
        else:
            table_data = []
            for p in proposals[:6]:
                table_data.append({
                    "Proposal": p.id,
                    "Title": p.title,
                    "Amount": format_inr(p.total_amount),
                    "Status": p.status.value,
                    "Source": p.source,
                    "Created": format_date(p.created_at),
                })
            df_proposals = pd.DataFrame(table_data)
            st.dataframe(
                df_proposals,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Proposal": st.column_config.TextColumn("Proposal ID", width="small"),
                    "Title": st.column_config.TextColumn("Title", width="medium"),
                    "Amount": st.column_config.TextColumn("Amount", width="small"),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                    "Source": st.column_config.TextColumn("Source", width="small"),
                    "Created": st.column_config.TextColumn("Date", width="small"),
                },
            )

    # 3. Bottom Row: Safety Interceptions & Audit Trail
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    b_left, b_right = st.columns(2)

    with b_left:
        st.subheader("⚠️ Recent Safety Findings & Policy Interceptions")
        violation_events = [e for e in audit_events if e.event_type.value in ["POLICY_VIOLATION_DETECTED", "REVALIDATION_FAILED"]]
        if not violation_events:
            st.success("✅ **Zero Recent Safety Violations**: All recent financial operations strictly conformed to safety policies.")
        else:
            for ev in violation_events[:3]:
                rule = ev.details.get("rule_name") or ev.details.get("revalidation_failure") or "Financial Policy Barrier"
                expl = ev.details.get("explanation") or ev.details.get("revalidation_failure") or "Policy conditions failed pre-execution check."
                render_severity_callout(
                    severity=ev.outcome,
                    rule_name=rule,
                    explanation=expl,
                    policy_id=ev.details.get("policy_id", ""),
                )

    with b_right:
        st.subheader("📜 Recent Governance Audit Events")
        if not audit_events:
            render_empty_state("No Audit Events", "No historical audit events logged yet.", icon="📜")
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
            df_audit = pd.DataFrame(audit_rows)
            st.dataframe(
                df_audit,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Timestamp": st.column_config.TextColumn("Timestamp", width="small"),
                    "Event": st.column_config.TextColumn("Event", width="medium"),
                    "Proposal": st.column_config.TextColumn("Proposal", width="small"),
                    "Actor": st.column_config.TextColumn("Actor", width="small"),
                    "Outcome": st.column_config.TextColumn("Outcome", width="small"),
                },
            )
