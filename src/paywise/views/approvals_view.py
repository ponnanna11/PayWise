"""
Approvals View for PayWise.
Role-aware executive authorization console cryptographically binding decisions to exact hashes.
"""
import streamlit as st
import pandas as pd
from paywise.models.approval import ApprovalCreate, ApprovalDecision, ApproverRole
from paywise.repositories.approval_repo import ApprovalRepository
from paywise.repositories.proposal_repo import ProposalRepository
from paywise.services.approval_service import ApprovalService
from paywise.utils.formatters import format_inr, format_date
from paywise.views.components import (
    render_page_header,
    render_status_badge,
    render_empty_state,
    render_severity_callout,
)


def render_approvals_view(db_path: str):
    render_page_header(
        "Executive Authorization Console",
        "Role-aware governance workflow binding approvals cryptographically to exact proposal and ledger hashes.",
    )

    prop_repo = ProposalRepository(db_path)
    approval_repo = ApprovalRepository(db_path)
    approval_service = ApprovalService(db_path)

    # Approver Role Selector
    with st.container(border=True):
        r1, r2 = st.columns([1, 2])
        with r1:
            st.markdown("#### 👤 Approver Role (Simulated)")
            role_options = [r.value for r in ApproverRole]
            selected_role = st.selectbox(
                "Active Governance Role",
                role_options,
                index=1,  # Default to FINANCE_MANAGER
                help="Role-based access control. Authorized managers can sign off on pending disbursements.",
            )
        with r2:
            st.markdown("#### 🛡️ Authority Level")
            if selected_role == "BUSINESS_USER":
                st.warning("⚠️ **Viewer / Proposer Role**: Business users cannot grant sign-offs for proposals exceeding approval thresholds.")
            else:
                st.success(f"✅ **Authorized Signatory ({selected_role})**: Eligible to review and approve high-value batches and policy exceptions.")

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    # Proposals Awaiting Approval
    awaiting_proposals = [p for p in prop_repo.list_all() if p.status.value in ["AWAITING_APPROVAL", "STALE"]]

    st.subheader(f"Pending Authorizations ({len(awaiting_proposals)})")

    if not awaiting_proposals:
        render_empty_state(
            "No Authorizations Pending",
            "There are currently no proposals awaiting executive sign-off.",
            icon="✍️",
        )
    else:
        for prop in awaiting_proposals:
            preview = prop_repo.get_latest_preview(prop.id)
            with st.container(border=True):
                h1, h2 = st.columns([2.5, 1.2])
                with h1:
                    st.markdown(f"### {prop.title}")
                    st.caption(f"Proposal ID: `{prop.id}` • Version: **v{prop.version}** • Status: {render_status_badge(prop.status.value)}")
                    if prop.description:
                        st.write(prop.description)
                with h2:
                    st.markdown(f"<h3 style='margin:0; text-align:right;'>{format_inr(prop.total_amount)}</h3>", unsafe_allow_html=True)
                    st.caption(f"Disbursement Account: `{prop.account_id}`")

                # Show preview findings triggering approval
                if preview and preview.findings:
                    st.markdown("##### ⚠️ Policy Findings Requiring Sign-off:")
                    for f in preview.findings:
                        if f.severity.value in ["REQUIRE_APPROVAL", "WARN"]:
                            render_severity_callout(
                                severity=f.severity.value,
                                rule_name=f.rule_name,
                                explanation=f.explanation,
                                recommended_action=f.recommended_action,
                                policy_id=f.policy_id,
                            )

                # Cryptographic Hash preview
                if preview:
                    with st.expander("🔐 Cryptographic Binding Verification", expanded=False):
                        st.code(
                            f"Proposal Hash:   {prop.proposal_hash}\n"
                            f"Ledger Hash:     {preview.ledger_state_hash}\n"
                            f"Policy Set Hash: {preview.policy_set_hash}",
                            language="text",
                        )

                # Approval Decision Form
                if selected_role == "BUSINESS_USER":
                    st.info("ℹ️ Switch role above to an authorized manager to submit an approval decision.")
                else:
                    with st.form(key=f"appr_form_{prop.id}"):
                        justification = st.text_area(
                            "Mandatory Audit Justification",
                            placeholder="Enter business reason, approved budget code, or operational justification...",
                            key=f"just_{prop.id}",
                        )
                        c_app, c_rej = st.columns(2)
                        with c_app:
                            btn_approve = st.form_submit_button("✅ Authorize & Grant Approval", type="primary", use_container_width=True)
                        with c_rej:
                            btn_reject = st.form_submit_button("✕ Reject Proposal", use_container_width=True)

                        if btn_approve:
                            if not justification or len(justification.strip()) < 5:
                                st.error("Audit justification must be at least 5 characters.")
                            else:
                                try:
                                    app_create = ApprovalCreate(
                                        proposal_id=prop.id,
                                        preview_id=preview.id if preview else f"SIM-{prop.id}",
                                        approver_id=f"USR-{selected_role[:3]}-01",
                                        approver_name=f"Authorized {selected_role.title().replace('_', ' ')}",
                                        approver_role=ApproverRole(selected_role),
                                        decision=ApprovalDecision.APPROVED,
                                        justification=justification.strip(),
                                    )
                                    saved = approval_service.process_approval(app_create)
                                    st.success(f"Approval `{saved.id}` granted! Proposal '{prop.id}' is now APPROVED.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Approval Failed: {str(e)}")

                        if btn_reject:
                            if not justification or len(justification.strip()) < 5:
                                st.error("Audit justification is required when rejecting a proposal.")
                            else:
                                try:
                                    app_create = ApprovalCreate(
                                        proposal_id=prop.id,
                                        preview_id=preview.id if preview else f"SIM-{prop.id}",
                                        approver_id=f"USR-{selected_role[:3]}-01",
                                        approver_name=f"Authorized {selected_role.title().replace('_', ' ')}",
                                        approver_role=ApproverRole(selected_role),
                                        decision=ApprovalDecision.REJECTED,
                                        justification=justification.strip(),
                                    )
                                    saved = approval_service.process_approval(app_create)
                                    st.warning(f"Proposal '{prop.id}' has been REJECTED.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Rejection Failed: {str(e)}")

    # Historical Approvals Log
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    st.subheader("📜 Signed Approvals Registry")
    all_props = prop_repo.list_all()
    approval_records = []
    for p in all_props:
        apps = approval_repo.list_for_proposal(p.id)
        for a in apps:
            approval_records.append({
                "Approval ID": a.id,
                "Proposal ID": a.proposal_id,
                "Approver": a.approver_name,
                "Role": a.approver_role,
                "Decision": a.decision.value,
                "Status": "VALID" if a.is_valid else "INVALIDATED (TAMPER/UPDATE)",
                "Date": format_date(a.created_at),
                "Justification": a.justification,
            })

    if not approval_records:
        render_empty_state("No Signed Approvals", "No historical approval decisions recorded yet.", icon="✍️")
    else:
        st.dataframe(pd.DataFrame(approval_records), use_container_width=True, hide_index=True)
