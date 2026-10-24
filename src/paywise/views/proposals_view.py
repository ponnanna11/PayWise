"""
Payment Proposals View for PayWise.
Enables filtering, searching, inspecting, and triggering simulations on financial proposals.
"""
import streamlit as st
import pandas as pd
from paywise.repositories.proposal_repo import ProposalRepository
from paywise.services.proposal_service import ProposalService
from paywise.utils.formatters import format_inr, format_date
from paywise.views.components import render_page_header, render_status_badge, render_empty_state


def render_proposals_view(db_path: str):
    render_page_header(
        "Payment Proposals",
        "Review, inspect, filter, and simulate disbursement requests prepared by AI agents or finance operators.",
    )

    prop_service = ProposalService(db_path)
    prop_repo = ProposalRepository(db_path)

    all_proposals = prop_repo.list_all()

    # Search & Filter Controls
    f_col1, f_col2, f_col3 = st.columns([1.5, 1.2, 1.2])
    with f_col1:
        search_query = st.text_input("🔍 Search Proposals", placeholder="Search by ID, title, or beneficiary...", key="prop_search")
    with f_col2:
        status_options = ["ALL", "DRAFT", "SIMULATED", "AWAITING_APPROVAL", "APPROVED", "COMMITTED_SIMULATED", "BLOCKED", "STALE", "REJECTED"]
        status_filter = st.selectbox("Status Filter", status_options, index=0)
    with f_col3:
        source_options = ["ALL", "AI_AGENT", "GEMINI_FLASH_AGENT", "MANUAL_ENTRY", "DETERMINISTIC_FALLBACK"]
        source_filter = st.selectbox("Origin / Source", source_options, index=0)

    # Filter logic
    filtered = all_proposals
    if status_filter != "ALL":
        filtered = [p for p in filtered if p.status.value == status_filter]
    if source_filter != "ALL":
        filtered = [p for p in filtered if p.source == source_filter]
    if search_query.strip():
        q = search_query.strip().lower()
        filtered = [
            p for p in filtered
            if q in p.id.lower() or q in p.title.lower() or any(q in t.beneficiary_name.lower() for t in p.transactions)
        ]

    st.markdown(f"**Showing {len(filtered)} of {len(all_proposals)} proposal(s)**")

    if not filtered:
        render_empty_state(
            "No Proposals Found",
            "No financial proposals match your active filters or search terms. Try clearing search or change status filter.",
            icon="📋",
        )
        return

    for prop in filtered:
        preview = prop_repo.get_latest_preview(prop.id)
        findings_count = len(preview.findings) if preview else 0
        has_block = any(f.severity.value == "BLOCK" for f in preview.findings) if preview else False

        with st.container(border=True):
            h_col1, h_col2, h_col3 = st.columns([2.5, 1.2, 1.3])

            with h_col1:
                st.markdown(
                    f"<div class='pw-column-eyebrow'>FINANCIAL PROPOSAL</div>"
                    f"<div style='font-weight:700; font-size:1.25rem; color:#172554; line-height:1.3; margin:0.25rem 0 0.35rem 0;'>{prop.title}</div>"
                    f"<div style='font-size:0.825rem; color:#526581; line-height:1.4;'>ID: <code style='font-size:0.8rem;'>{prop.id}</code> • Type: <b>{prop.proposal_type.value}</b> • Source: <code style='font-size:0.8rem;'>{prop.source}</code></div>",
                    unsafe_allow_html=True,
                )
                if prop.description:
                    st.markdown(f"<div style='font-size:0.9rem; color:#374151; margin-top:0.35rem; line-height:1.45;'>{prop.description}</div>", unsafe_allow_html=True)

            with h_col2:
                findings_html = ""
                if findings_count > 0:
                    badge_color = "#DC2626" if has_block else "#D97706"
                    findings_html = f"<div style='font-size:0.8rem; text-align:right; color:{badge_color}; margin-top:0.25rem; font-weight:600;'>{findings_count} Policy Finding(s)</div>"

                st.markdown(
                    f"<div class='pw-column-eyebrow-right'>PROPOSED OUTFLOW</div>"
                    f"<div style='text-align:right; font-weight:700; font-size:1.25rem; color:#172554; line-height:1.3; margin:0.25rem 0 0.35rem 0;'>{format_inr(prop.total_amount)}</div>"
                    f"<div style='text-align:right;'>{render_status_badge(prop.status.value)}</div>"
                    f"{findings_html}",
                    unsafe_allow_html=True,
                )

            with h_col3:
                st.markdown(
                    f"<div class='pw-column-eyebrow-right'>DISBURSEMENT ROUTE</div>"
                    f"<div style='text-align:right; font-size:0.9rem; font-weight:600; color:#172554; line-height:1.3; margin:0.25rem 0 0.35rem 0;'>Account: <code style='font-size:0.85rem;'>{prop.account_id}</code></div>"
                    f"<div style='text-align:right; font-size:0.825rem; color:#526581; line-height:1.4;'>Version: <b>v{prop.version}</b> • {format_date(prop.created_at)}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown("<div style='margin-top:0.5rem;'></div>", unsafe_allow_html=True)
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("⚡ Simulate", key=f"sim_btn_{prop.id}", type="primary" if prop.status.value in ["DRAFT", "STALE"] else "secondary", use_container_width=True):
                        with st.spinner("Executing simulation..."):
                            prop_service.run_simulation(prop.id, actor="operator_ui")
                            st.session_state["selected_proposal_id"] = prop.id
                            st.session_state["current_page"] = "Simulation & Preview"
                            st.rerun()
                with btn_col2:
                    if st.button("🔍 Details", key=f"view_btn_{prop.id}", use_container_width=True):
                        st.session_state["selected_proposal_id"] = prop.id
                        st.session_state["current_page"] = "Simulation & Preview"
                        st.rerun()

            # Expandable transaction breakdown
            with st.expander(f"📑 Transactions ({len(prop.transactions)}) & Line Item Breakdown", expanded=False):
                tx_data = []
                for t in prop.transactions:
                    tx_data.append({
                        "TX ID": t.id,
                        "Type": t.transaction_type.value,
                        "Beneficiary": t.beneficiary_name,
                        "Supplier ID": t.supplier_id or "-",
                        "Invoice ID": t.invoice_id or "-",
                        "Amount": format_inr(t.amount),
                        "Date": str(t.proposed_payment_date),
                        "Category": t.transaction_category,
                        "Description": t.description,
                    })
                st.dataframe(
                    pd.DataFrame(tx_data),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "TX ID": st.column_config.TextColumn("TX ID", width="small"),
                        "Type": st.column_config.TextColumn("Type", width="small"),
                        "Beneficiary": st.column_config.TextColumn("Beneficiary", width="medium"),
                        "Supplier ID": st.column_config.TextColumn("Supplier ID", width="small"),
                        "Invoice ID": st.column_config.TextColumn("Invoice ID", width="small"),
                        "Amount": st.column_config.TextColumn("Amount", width="small"),
                        "Date": st.column_config.TextColumn("Date", width="small"),
                        "Category": st.column_config.TextColumn("Category", width="small"),
                        "Description": st.column_config.TextColumn("Description", width="large"),
                    },
                )
