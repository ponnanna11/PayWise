"""
Create Proposal View for PayWise.
Features AI-assisted proposal creation, interactive safety presets,
and a deterministic manual transaction builder.
"""
from datetime import date, timedelta
import streamlit as st
import textwrap
from pydantic import ValidationError
from paywise.models.proposal import (
    ProposalCreate,
    ProposalType,
    ProposedTransaction,
    TransactionType,
)
from paywise.repositories.account_repo import AccountRepository
from paywise.repositories.invoice_repo import InvoiceRepository
from paywise.repositories.supplier_repo import SupplierRepository
from paywise.services.ai_adapter import AIAdapter
from paywise.services.proposal_service import ProposalService
from paywise.utils.formatters import format_inr
from paywise.views.components import render_page_header


def render_new_proposal_view(db_path: str):
    render_page_header(
        "Create Proposal",
        "Prepare financial disbursement proposals using AI assistance, interactive safety presets, or manual specification.",
    )

    acc_repo = AccountRepository(db_path)
    sup_repo = SupplierRepository(db_path)
    inv_repo = InvoiceRepository(db_path)
    prop_service = ProposalService(db_path)
    ai_adapter = AIAdapter()

    accounts = acc_repo.list_all()
    suppliers = sup_repo.list_all()
    invoices = inv_repo.list_all()

    account_options = {f"{a.account_name} ({a.bank_name}) — Avail: {format_inr(a.available_funds)}": a.id for a in accounts}
    supplier_options = {f"{s.name} ({s.id}) [{s.status.value}]": s.id for s in suppliers}
    invoice_options = {"None (Direct Payout / Unlinked)": None}
    for inv in invoices:
        invoice_options[f"{inv.invoice_number} ({inv.id}) — {format_inr(inv.amount)} [{inv.status.value}]"] = inv.id

    tab_agent, tab_presets, tab_manual = st.tabs([
        "✨ AI-Assisted Proposal",
        "⚡ Quick Safety Presets",
        "📝 Manual Entry",
    ])

    # TAB 1: AI-ASSISTED PROPOSAL CREATION
    with tab_agent:
        st.subheader("AI-Assisted Proposal Drafting")
        
        info_markup = textwrap.dedent("""
            <div style="background:#FFFFFF; border:1px solid #DCE6F5; border-left:4px solid #2563EB; padding:1.1rem 1.35rem; border-radius:10px; margin-bottom:1.25rem; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.02);">
                <div style="font-weight:600; font-size:0.95rem; color:#172554; margin-bottom:0.25rem;">Safety Invariant & Architecture:</div>
                <div style="font-size:0.9rem; color:#374151; line-height:1.5;">
                    The AI drafts candidate proposals from plain English instructions. PayWise's deterministic engine independently verifies schemas, computes in-memory consequence simulations, and enforces mandatory policy rules before any human authorization or commit.
                </div>
            </div>
        """).strip()
        st.markdown(info_markup, unsafe_allow_html=True)

        agent_prompt = st.text_area(
            "Natural Language Financial Instruction",
            value="Prepare payments for eligible pending supplier invoices, but maintain at least ₹5,00,000 in the primary operating account.",
            height=100,
            help="Describe the intended financial action, vendor settlements, or reserve constraints in plain English.",
        )

        acc_col, btn_col = st.columns([2, 1])
        with acc_col:
            selected_acc_label = st.selectbox("Target Disbursement Account", list(account_options.keys()), key="ai_target_acc")
            selected_acc_id = account_options[selected_acc_label]

        with btn_col:
            st.write("")
            st.write("")
            draft_btn = st.button("✨ Draft Candidate Proposal", type="primary", use_container_width=True)

        if draft_btn:
            with st.spinner("AI drafting proposal based on verified suppliers and open invoices..."):
                sup_dicts = [s.model_dump() for s in suppliers]
                inv_dicts = [i.model_dump() for i in invoices]
                candidate = ai_adapter.generate_proposal_from_prompt(
                    prompt=agent_prompt,
                    account_id=selected_acc_id,
                    available_suppliers=sup_dicts,
                    available_invoices=inv_dicts,
                )
                st.session_state["candidate_draft"] = candidate

        if "candidate_draft" in st.session_state:
            candidate = st.session_state["candidate_draft"]
            st.markdown("---")
            st.markdown("#### 📄 Candidate Proposal Draft (Awaiting Simulation)")

            with st.container(border=True):
                c1, c2 = st.columns([2.5, 1])
                with c1:
                    st.markdown(f"**Title**: {candidate.title}")
                    st.caption(f"Source: `{candidate.source}` • Initiator: `{candidate.created_by}`")
                    st.write(candidate.description)
                with c2:
                    total_cand = sum(t.amount for t in candidate.transactions)
                    st.markdown(f"<div style='text-align:right; font-weight:700; font-size:1.4rem; color:#172554;'>{format_inr(total_cand)}</div>", unsafe_allow_html=True)
                    st.caption(f"Account: `{candidate.account_id}` • Currency: `{candidate.currency}`")

                st.markdown("##### Line Items:")
                for tx in candidate.transactions:
                    st.markdown(f"- **{tx.beneficiary_name}**: {format_inr(tx.amount)} on {tx.proposed_payment_date} (`{tx.description}`)")

                c_sub1, c_sub2 = st.columns([1, 2])
                with c_sub1:
                    if st.button("🚀 Accept Draft & Run Safety Simulation", type="primary", key="btn_accept_ai"):
                        new_prop = prop_service.create_proposal(candidate)
                        prop_service.run_simulation(new_prop.id, actor=candidate.created_by)
                        st.session_state["selected_proposal_id"] = new_prop.id
                        st.session_state["current_page"] = "Simulation & Preview"
                        del st.session_state["candidate_draft"]
                        st.rerun()
                with c_sub2:
                    if st.button("✕ Discard Draft", key="btn_discard_ai"):
                        del st.session_state["candidate_draft"]
                        st.rerun()

    # TAB 2: PRESET TEST SCENARIOS
    with tab_presets:
        st.subheader("Interactive Safety Gate Scenarios")
        st.write("Load pre-configured test scenarios to verify how PayWise simulates, blocks, or escalates financial risks.")

        p1, p2, p3 = st.columns(3)

        with p1:
            with st.container(border=True):
                st.markdown("### 🟢 Safe Vendor Settlement")
                st.write("Routine disbursement matching an approved invoice within normal operating liquidity.")
                st.markdown("- **Beneficiary**: Bharti Airtel Enterprise Ltd\n- **Amount**: ₹28,500.00\n- **Account**: HDFC Main Account\n- **Expected Outcome**: Pass without blocks or approvals.")
                if st.button("Load Safe Batch", key="btn_preset_safe", type="primary", use_container_width=True):
                    tx = ProposedTransaction(
                        id=f"TX-SAFE-{date.today().strftime('%Y%m%d')}-01",
                        transaction_type=TransactionType.SUPPLIER_PAYMENT,
                        invoice_id="INV-2026-003",
                        supplier_id="SUP-AIRTEL-03",
                        beneficiary_name="Bharti Airtel Enterprise Ltd",
                        amount=28500.00,
                        proposed_payment_date=date.today() + timedelta(days=2),
                        transaction_category="Telecom & Connectivity",
                        description="Routine monthly leased line connectivity invoice",
                    )
                    prop = prop_service.create_proposal(
                        ProposalCreate(
                            title="Safe Leased Line Settlement",
                            description="Routine telecom billing settlement.",
                            account_id="ACC-HDFC-MAIN",
                            transactions=[tx],
                        )
                    )
                    prop_service.run_simulation(prop.id)
                    st.session_state["selected_proposal_id"] = prop.id
                    st.session_state["current_page"] = "Simulation & Preview"
                    st.rerun()

        with p2:
            with st.container(border=True):
                st.markdown("### 🟡 High-Value Milestone")
                st.write("An enterprise milestone exceeding the single transaction threshold (₹50,000) requiring sign-off.")
                st.markdown("- **Beneficiary**: Tata Consultancy Services Ltd\n- **Amount**: ₹1,85,000.00\n- **Account**: HDFC Main Account\n- **Expected Outcome**: Triggers REQUIRE_APPROVAL for CFO.")
                if st.button("Load High-Value Batch", key="btn_preset_high", use_container_width=True):
                    tx = ProposedTransaction(
                        id=f"TX-HIGH-{date.today().strftime('%Y%m%d')}-01",
                        transaction_type=TransactionType.SUPPLIER_PAYMENT,
                        invoice_id="INV-2026-001",
                        supplier_id="SUP-TCS-01",
                        beneficiary_name="Tata Consultancy Services Ltd",
                        amount=185000.00,
                        proposed_payment_date=date.today() + timedelta(days=3),
                        transaction_category="Cloud & IT Services",
                        description="Enterprise cloud migration milestone 1 settlement",
                    )
                    prop = prop_service.create_proposal(
                        ProposalCreate(
                            title="Enterprise Cloud Migration Milestone 1",
                            description="Major cloud migration milestone payout.",
                            account_id="ACC-HDFC-MAIN",
                            transactions=[tx],
                        )
                    )
                    prop_service.run_simulation(prop.id)
                    st.session_state["selected_proposal_id"] = prop.id
                    st.session_state["current_page"] = "Simulation & Preview"
                    st.rerun()

        with p3:
            with st.container(border=True):
                st.markdown("### 🔴 Multi-Risk Safety Barrier")
                st.write("Disbursement attempting to settle a cancelled facility contract and an already-settled invoice.")
                st.markdown("- **Transactions**: 2 line items\n- **Amount**: ₹44,000.00\n- **Policy Violations**: Cancelled invoice, Duplicate payee\n- **Expected Outcome**: Immediate BLOCK.")
                if st.button("Load Risky Batch", key="btn_preset_risky", use_container_width=True):
                    tx1 = ProposedTransaction(
                        id=f"TX-RISK-{date.today().strftime('%Y%m%d')}-01",
                        transaction_type=TransactionType.SUPPLIER_PAYMENT,
                        invoice_id="INV-2026-005",
                        supplier_id="SUP-APEX-04",
                        beneficiary_name="Apex Facilities & Logistics Pvt Ltd",
                        amount=12000.00,
                        proposed_payment_date=date.today() + timedelta(days=2),
                        transaction_category="Office Maintenance",
                        description="Payment attempt on cancelled deep cleaning contract",
                    )
                    tx2 = ProposedTransaction(
                        id=f"TX-RISK-{date.today().strftime('%Y%m%d')}-02",
                        transaction_type=TransactionType.SUPPLIER_PAYMENT,
                        invoice_id="INV-2026-004",
                        supplier_id="SUP-AIRTEL-03",
                        beneficiary_name="Bharti Airtel Enterprise Ltd",
                        amount=32000.00,
                        proposed_payment_date=date.today() + timedelta(days=2),
                        transaction_category="Telecom",
                        description="Duplicate attempt on already-settled microwave bandwidth invoice",
                    )
                    prop = prop_service.create_proposal(
                        ProposalCreate(
                            title="Multi-Risk Safety Test Batch",
                            description="Test batch intended to activate safety barriers.",
                            account_id="ACC-ICICI-EXP",
                            proposal_type=ProposalType.PAYMENT_BATCH,
                            transactions=[tx1, tx2],
                        )
                    )
                    prop_service.run_simulation(prop.id)
                    st.session_state["selected_proposal_id"] = prop.id
                    st.session_state["current_page"] = "Simulation & Preview"
                    st.rerun()

    # TAB 3: MANUAL TRANSACTION BUILDER
    with tab_manual:
        st.subheader("Manual Proposal Entry")
        with st.form("manual_proposal_form_v2"):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Proposal Title", value="Vendor Invoice Settlement")
                prop_type_str = st.selectbox("Proposal Action Type", [t.value for t in ProposalType], index=0)
                selected_acc_label = st.selectbox("Disbursement Account", list(account_options.keys()), key="man_acc_sel")
                account_id = account_options[selected_acc_label]
            with col2:
                description = st.text_area("Business Justification", value="Scheduled operational payout for verified service invoices.")
                created_by = st.text_input("Initiator Role", value="finance_analyst")

            st.markdown("---")
            st.markdown("#### Transaction Line Items")

            t_col1, t_col2, t_col3, t_col4 = st.columns([1.5, 1.2, 1, 1.2])
            with t_col1:
                beneficiary = st.text_input("Beneficiary Name", value="Tata Consultancy Services Ltd", key="man_ben")
                sup_label = st.selectbox("Linked Supplier Profile", list(supplier_options.keys()), key="man_sup")
                supplier_id = supplier_options[sup_label]
            with t_col2:
                inv_label = st.selectbox("Matching Invoice", list(invoice_options.keys()), key="man_inv")
                invoice_id = invoice_options[inv_label]
                tx_type_str = st.selectbox("Disbursement Category", [tt.value for tt in TransactionType], key="man_type")
            with t_col3:
                amount = st.number_input("Amount (₹)", min_value=1.0, value=185000.0, step=1000.0, key="man_amt")
                currency = st.selectbox("Currency", ["INR", "USD", "EUR"], index=0, key="man_curr")
            with t_col4:
                pay_date = st.date_input("Proposed Date", value=date.today() + timedelta(days=2), key="man_date")
                tx_desc = st.text_input("Line Item Detail", value="Enterprise cloud infrastructure settlement", key="man_desc")

            submitted = st.form_submit_button("Submit Proposal for Simulation", type="primary")
            if submitted:
                try:
                    tx = ProposedTransaction(
                        id=f"TX-{date.today().strftime('%Y%m%d')}-01",
                        transaction_type=TransactionType(tx_type_str),
                        invoice_id=invoice_id,
                        supplier_id=supplier_id,
                        beneficiary_name=beneficiary,
                        amount=float(amount),
                        currency=currency,
                        proposed_payment_date=pay_date,
                        transaction_category="Vendor Payment",
                        description=tx_desc,
                    )
                    prop_create = ProposalCreate(
                        title=title,
                        description=description,
                        proposal_type=ProposalType(prop_type_str),
                        account_id=account_id,
                        currency=currency,
                        source="MANUAL_ENTRY",
                        created_by=created_by,
                        transactions=[tx],
                    )
                    new_prop = prop_service.create_proposal(prop_create)
                    prop_service.run_simulation(new_prop.id, actor=created_by)
                    st.session_state["selected_proposal_id"] = new_prop.id
                    st.session_state["current_page"] = "Simulation & Preview"
                    st.rerun()
                except ValidationError as ve:
                    st.error(f"Schema Validation Error: {ve}")
                except Exception as e:
                    st.error(f"Failed to create proposal: {str(e)}")
