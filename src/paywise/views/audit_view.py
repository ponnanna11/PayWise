"""
Audit Trail View for PayWise.
Provides searching, filtering, and inspection of immutable application governance events.
"""
import streamlit as st
import pandas as pd
from paywise.repositories.audit_repo import AuditRepository
from paywise.utils.formatters import format_date
from paywise.views.components import render_page_header, render_empty_state


def render_audit_view(db_path: str):
    render_page_header(
        "Governance Audit Trail",
        "Chronological, immutable event log capturing proposal lifecycles, policy interceptions, approvals, and commits.",
    )

    audit_repo = AuditRepository(db_path)

    f1, f2, f3 = st.columns(3)
    with f1:
        proposal_filter = st.text_input("Filter by Proposal ID", placeholder="e.g. PROP-2026-001")
    with f2:
        event_types = [
            "ALL",
            "PROPOSAL_CREATED",
            "PROPOSAL_VALIDATION_FAILED",
            "SIMULATION_GENERATED",
            "POLICY_VIOLATION_DETECTED",
            "APPROVAL_GRANTED",
            "APPROVAL_REJECTED",
            "PROPOSAL_MODIFIED",
            "REVALIDATION_FAILED",
            "SIMULATED_COMMIT_SUCCEEDED",
            "POLICY_ACTIVATED",
            "POLICY_DEACTIVATED",
        ]
        selected_event = st.selectbox("Event Category Filter", event_types)
    with f3:
        outcomes = ["ALL", "SUCCESS", "BLOCKED", "REJECTED", "WARNING", "FAILED"]
        selected_outcome = st.selectbox("Execution Outcome", outcomes)

    events = audit_repo.list_all(
        proposal_id=proposal_filter.strip() if proposal_filter else None,
        event_type=selected_event if selected_event != "ALL" else None,
        outcome=selected_outcome if selected_outcome != "ALL" else None,
        limit=200,
    )

    st.markdown(f"**Showing {len(events)} event record(s)**")

    if not events:
        render_empty_state("No Audit Events Found", "No events match the selected filters.", icon="📜")
        return

    # Table view
    table_rows = []
    for ev in events:
        table_rows.append({
            "Audit ID": ev.id,
            "Timestamp": format_date(ev.timestamp),
            "Event Type": ev.event_type.value,
            "Proposal ID": ev.proposal_id or "-",
            "Actor": ev.actor,
            "Outcome": ev.outcome,
        })
    df_audit = pd.DataFrame(table_rows)
    st.dataframe(
        df_audit,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Audit ID": st.column_config.TextColumn("Audit ID", width="small"),
            "Timestamp": st.column_config.TextColumn("Timestamp", width="small"),
            "Event Type": st.column_config.TextColumn("Event Type", width="medium"),
            "Proposal ID": st.column_config.TextColumn("Proposal ID", width="small"),
            "Actor": st.column_config.TextColumn("Actor", width="small"),
            "Outcome": st.column_config.TextColumn("Outcome", width="small"),
        },
    )

    # Detailed Inspector
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    st.subheader("🔍 Structured Payload Inspector")
    ev_ids = [e.id for e in events]
    selected_ev_id = st.selectbox("Select Audit Event to Inspect", ev_ids)
    inspected_ev = next(e for e in events if e.id == selected_ev_id)

    with st.container(border=True):
        st.markdown(f"**Event**: `{inspected_ev.event_type.value}` • **Audit ID**: `{inspected_ev.id}`")
        st.caption(f"Timestamp: {format_date(inspected_ev.timestamp)} • Actor: `{inspected_ev.actor}` • Outcome: `{inspected_ev.outcome}`")
        if inspected_ev.proposal_id:
            st.caption(f"Linked Proposal: `{inspected_ev.proposal_id}`")
        st.json(inspected_ev.details)
