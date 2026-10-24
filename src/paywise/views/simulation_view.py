"""
Simulation & Consequence Preview View for PayWise.
Presents pre-execution impact, policy findings, visual severity callouts, AI explanations,
and the protected commit gateway.
"""
import streamlit as st
import pandas as pd
from paywise.repositories.account_repo import AccountRepository
from paywise.repositories.proposal_repo import ProposalRepository
from paywise.services.ai_adapter import AIAdapter
from paywise.services.commit_service import CommitError, CommitService, ConcurrencyError, DuplicateCommitError
from paywise.services.proposal_service import ProposalService
from paywise.utils.formatters import format_inr, format_date
from paywise.views.components import (
    render_page_header,
    render_status_badge,
    render_before_after_comparison,
    render_severity_callout,
    render_empty_state,
)


def render_simulation_view(db_path: str):
    render_page_header(
        "Simulation & Consequence Preview",
        "Deterministic virtual projection: S' = f(S, A) and policy evaluation: R = g(S, S', A, P)",
    )

    prop_service = ProposalService(db_path)
    prop_repo = ProposalRepository(db_path)
    commit_service = CommitService(db_path)
    acc_repo = AccountRepository(db_path)
    ai_adapter = AIAdapter()

    all_proposals = prop_repo.list_all()
    if not all_proposals:
        render_empty_state(
            "No Proposals Available",
            "Create a new proposal in 'Create Proposal' to model financial consequences.",
            icon="🔬",
        )
        return

    # Proposal Selector
    selected_id = st.session_state.get("selected_proposal_id", all_proposals[0].id)
    prop_ids = [p.id for p in all_proposals]
    selected_index = prop_ids.index(selected_id) if selected_id in prop_ids else 0

    s_col1, s_col2 = st.columns([2.8, 1.2])
    with s_col1:
        chosen_id = st.selectbox(
            "Select Proposal for Consequence Simulation",
            prop_ids,
            index=selected_index,
            format_func=lambda pid: f"{pid} — {next(p.title for p in all_proposals if p.id == pid)} ({format_inr(next(p.total_amount for p in all_proposals if p.id == pid))}) [{next(p.status.value for p in all_proposals if p.id == pid)}]",
        )
        st.session_state["selected_proposal_id"] = chosen_id

    proposal = prop_repo.get_by_id(chosen_id)
    preview = prop_repo.get_latest_preview(chosen_id)

    with s_col2:
        st.write("")
        st.write("")
        if st.button("🔄 Re-run Simulation & Policies", type="secondary", use_container_width=True):
            with st.spinner("Executing simulation..."):
                preview = prop_service.run_simulation(proposal.id, actor="operator_ui")
                proposal = prop_repo.get_by_id(proposal.id)
                st.rerun()

    if not preview:
        st.warning("This proposal has not been simulated yet.")
        if st.button("⚡ Run Simulation Now", type="primary"):
            preview = prop_service.run_simulation(proposal.id)
            st.rerun()
        return

    # 1. Proposal High-Level Summary Card
    status_val = proposal.status.value
    with st.container(border=True):
        p1, p2, p3 = st.columns([2.5, 1.2, 1.3])
        with p1:
            st.markdown(
                f"<div class='pw-column-eyebrow'>DISBURSEMENT PROPOSAL</div>"
                f"<div style='font-weight:700; font-size:1.25rem; color:#172554; line-height:1.3; margin:0.25rem 0 0.35rem 0;'>{proposal.title}</div>"
                f"<div style='font-size:0.825rem; color:#526581; line-height:1.4;'>Proposal ID: <code style='font-size:0.8rem;'>{proposal.id}</code> • Version: <b>v{proposal.version}</b> • Source: <code style='font-size:0.8rem;'>{proposal.source}</code></div>",
                unsafe_allow_html=True,
            )
            if proposal.description:
                st.markdown(f"<div style='font-size:0.9rem; color:#374151; margin-top:0.35rem; line-height:1.45;'>{proposal.description}</div>", unsafe_allow_html=True)
        with p2:
            st.markdown(
                f"<div class='pw-column-eyebrow-right'>PROPOSED OUTFLOW</div>"
                f"<div style='text-align:right; font-weight:700; font-size:1.35rem; color:#172554; line-height:1.3; margin:0.25rem 0 0.35rem 0;'>{format_inr(preview.total_outflow)}</div>"
                f"<div style='text-align:right; font-size:0.825rem; color:#526581; line-height:1.4;'>Disbursement Account: <code style='font-size:0.8rem;'>{proposal.account_id}</code></div>",
                unsafe_allow_html=True,
            )
        with p3:
            st.markdown(
                f"<div class='pw-column-eyebrow-right'>GOVERNANCE STATUS</div>"
                f"<div style='text-align:right; margin:0.25rem 0 0.35rem 0;'>{render_status_badge(status_val)}</div>"
                f"<div style='text-align:right; font-size:0.825rem; color:#526581; line-height:1.4;'>Simulated: {format_date(preview.simulated_at)}</div>",
                unsafe_allow_html=True,
            )

    # 2. Before-and-After Financial Comparison Grid
    st.markdown("<div style='margin-top: 1.25rem;'></div>", unsafe_allow_html=True)
    st.markdown("#### 📊 Deterministic State Projection (Before vs After)")
    render_before_after_comparison(
        current_balance=preview.current_balance,
        projected_balance=preview.projected_balance,
        reserved_balance=preview.reserved_balance,
        available_before=preview.available_balance_before,
        available_after=preview.available_balance_after,
        total_outflow=preview.total_outflow,
        account_id=proposal.account_id,
    )

    # 3. Policy Findings & AI Executive Explanation
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    f_head1, f_head2 = st.columns([2, 1])
    with f_head1:
        st.markdown(f"#### 🛡️ Policy Engine Safety Findings ({len(preview.findings)})")
    with f_head2:
        if preview.findings:
            if st.button("🤖 AI Executive Explanation", key="btn_ai_explain", use_container_width=True):
                with st.spinner("AI generating executive briefing..."):
                    explanation = ai_adapter.explain_findings(
                        findings=preview.findings,
                        proposal_title=proposal.title,
                        total_amount=proposal.total_amount,
                        projected_balance=preview.projected_balance,
                    )
                    st.session_state[f"ai_expl_{proposal.id}"] = explanation

    if f"ai_expl_{proposal.id}" in st.session_state:
        with st.container(border=True):
            st.markdown("##### 🤖 Executive Risk Summary:")
            st.markdown(st.session_state[f"ai_expl_{proposal.id}"])

    if not preview.findings:
        st.success("✅ **Zero Safety Policy Violations**: Proposal conforms to all active financial rules, reserves, and limits.")
    else:
        # Group findings by severity
        blocks = [f for f in preview.findings if f.severity.value == "BLOCK"]
        approvals = [f for f in preview.findings if f.severity.value == "REQUIRE_APPROVAL"]
        warns = [f for f in preview.findings if f.severity.value == "WARN"]

        if blocks:
            st.markdown(f"**🛑 Blocking Violations ({len(blocks)})** — Must be resolved before commit:")
            for b in blocks:
                render_severity_callout(
                    severity=b.severity.value,
                    rule_name=b.rule_name,
                    explanation=b.explanation,
                    recommended_action=b.recommended_action,
                    policy_id=b.policy_id,
                )

        if approvals:
            st.markdown(f"**⚠️ Required Authorizations ({len(approvals)})** — Requires manager sign-off:")
            for a in approvals:
                render_severity_callout(
                    severity=a.severity.value,
                    rule_name=a.rule_name,
                    explanation=a.explanation,
                    recommended_action=a.recommended_action,
                    policy_id=a.policy_id,
                )

        if warns:
            st.markdown(f"**ℹ️ Operational Cautions ({len(warns)})**:")
            for w in warns:
                render_severity_callout(
                    severity=w.severity.value,
                    rule_name=w.rule_name,
                    explanation=w.explanation,
                    recommended_action=w.recommended_action,
                    policy_id=w.policy_id,
                )

    # 4. Transaction-by-Transaction Breakdown Table
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("#### 📑 Transaction-Level Breakdown")
    tx_table = []
    for tx in proposal.transactions:
        outcome = next((o for o in preview.transaction_outcomes if o.transaction_id == tx.id), None)
        tx_table.append({
            "Transaction ID": tx.id,
            "Beneficiary": tx.beneficiary_name,
            "Supplier ID": tx.supplier_id or "-",
            "Invoice ID": tx.invoice_id or "-",
            "Amount": format_inr(tx.amount),
            "Execution Date": str(tx.proposed_payment_date),
            "Category": tx.transaction_category,
            "Outcome": outcome.status if outcome else "PROPOSED",
            "Projected Balance After": format_inr(outcome.projected_post_balance) if outcome else "-",
        })
    df_tx = pd.DataFrame(tx_table)
    st.dataframe(
        df_tx,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Transaction ID": st.column_config.TextColumn("Transaction ID", width="small"),
            "Beneficiary": st.column_config.TextColumn("Beneficiary", width="medium"),
            "Supplier ID": st.column_config.TextColumn("Supplier ID", width="small"),
            "Invoice ID": st.column_config.TextColumn("Invoice ID", width="small"),
            "Amount": st.column_config.TextColumn("Amount", width="small"),
            "Execution Date": st.column_config.TextColumn("Date", width="small"),
            "Category": st.column_config.TextColumn("Category", width="small"),
            "Outcome": st.column_config.TextColumn("Outcome", width="small"),
            "Projected Balance After": st.column_config.TextColumn("Projected Balance After", width="medium"),
        },
    )

    # 5. Cryptographic State Binding
    with st.expander("🔒 Cryptographic Hashes & Deterministic State Fingerprints", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Canonical Proposal Hash", value=preview.proposal_hash, disabled=True)
            st.text_input("Preview Hash", value=preview.id, disabled=True)
        with c2:
            st.text_input("Ledger State Hash", value=preview.ledger_state_hash, disabled=True)
            st.text_input("Active Policy Set Hash", value=preview.policy_set_hash, disabled=True)

    # 6. Action Execution Console
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("#### ⚡ Execution & Approval Gateways")

    if status_val == "COMMITTED_SIMULATED":
        st.success("🎉 **Proposal Committed to Simulated Ledger**: Transactions were executed atomically in SQLite. Account balances and invoice statuses have been updated.")
    elif status_val == "BLOCKED":
        st.error("🛑 **Commit Blocked by Safety Policies**: This proposal contains critical safety violations. You must modify line items or deposit funds before simulation can proceed.")
    elif status_val in ["AWAITING_APPROVAL", "STALE"]:
        st.warning("⚠️ **Manager Sign-off Required**: This disbursement exceeds discretionary thresholds. Please proceed to the Approvals console.")
        if st.button("👉 Open Approvals Console", type="primary"):
            st.session_state["current_page"] = "Approvals"
            st.rerun()
    elif status_val in ["SIMULATED", "APPROVED"]:
        st.info("✅ **Qualified for Simulated Commit**: Commit-time revalidation will atomically re-check ledger drift and policy integrity.")
        if st.button("🚀 Commit Simulated Payout (Atomic SQLite Transaction)", type="primary"):
            try:
                with st.spinner("Running 10-step commit revalidation and atomic database transaction..."):
                    result = commit_service.commit_proposal(proposal.id, actor="finance_operator")
                st.balloons()
                st.success(f"Disbursement committed! Commit ID: `{result['commit_id']}`. New Balance: **{format_inr(result['post_balance'])}**.")
                st.rerun()
            except DuplicateCommitError as dce:
                st.warning(f"Idempotency Safeguard: {str(dce)}")
            except CommitError as ce:
                st.error(f"Commit-Time Revalidation Halted Execution: {str(ce)}")
            except ConcurrencyError as cce:
                st.error(f"Optimistic Concurrency Collision: {str(cce)}")
            except Exception as ex:
                st.error(f"Execution Error: {str(ex)}")
