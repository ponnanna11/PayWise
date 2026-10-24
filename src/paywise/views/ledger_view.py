"""
Ledger View for PayWise.
Displays simulated bank accounts, supplier directory, and accounts payable invoices.
"""
import streamlit as st
import pandas as pd
from paywise.repositories.account_repo import AccountRepository
from paywise.repositories.invoice_repo import InvoiceRepository
from paywise.repositories.supplier_repo import SupplierRepository
from paywise.utils.formatters import format_inr, format_date
from paywise.utils.seed_data import seed_database
from paywise.views.components import render_page_header, render_simulation_banner, render_empty_state


def render_ledger_view(db_path: str):
    render_page_header(
        "Simulated Financial Ledger",
        "Inspection view of simulated corporate bank accounts, verified suppliers directory, and accounts payable invoices.",
    )
    render_simulation_banner()

    acc_repo = AccountRepository(db_path)
    sup_repo = SupplierRepository(db_path)
    inv_repo = InvoiceRepository(db_path)

    tab_acc, tab_sup, tab_inv, tab_reset = st.tabs([
        "🏦 Treasury Accounts",
        "🏢 Verified Suppliers",
        "📄 Accounts Payable Invoices",
        "🔄 Database Initialization",
    ])

    with tab_acc:
        st.subheader("Simulated Treasury Accounts")
        accounts = acc_repo.list_all()
        acc_data = []
        for a in accounts:
            acc_data.append({
                "Account ID": a.id,
                "Bank Institution": a.bank_name,
                "Account Name": a.account_name,
                "Account Number": a.account_number,
                "Current Balance": format_inr(a.current_balance),
                "Mandatory Reserve": format_inr(a.reserved_balance),
                "Available Funds": format_inr(a.available_funds),
                "Status": a.status.value,
                "Version": a.version,
                "Last Updated": format_date(a.updated_at),
            })
        st.dataframe(pd.DataFrame(acc_data), use_container_width=True, hide_index=True)

    with tab_sup:
        st.subheader("Suppliers Directory & KYC Risk Profiles")
        suppliers = sup_repo.list_all()
        sup_data = []
        for s in suppliers:
            sup_data.append({
                "Supplier ID": s.id,
                "Legal Name": s.name,
                "GSTIN": s.gstin or "Unregistered",
                "PAN": s.pan or "None",
                "IFSC Code": s.bank_ifsc,
                "Bank Account Number": s.bank_account_number,
                "Compliance Status": s.status.value,
                "Risk Tier": s.risk_tier.value,
                "Category": s.default_category,
            })
        st.dataframe(pd.DataFrame(sup_data), use_container_width=True, hide_index=True)

    with tab_inv:
        st.subheader("Accounts Payable Invoices")
        invoices = inv_repo.list_all()
        inv_data = []
        for i in invoices:
            inv_data.append({
                "Invoice ID": i.id,
                "Invoice Reference #": i.invoice_number,
                "Supplier ID": i.supplier_id,
                "Invoice Amount": format_inr(i.amount),
                "Issue Date": str(i.invoice_date),
                "Due Date": str(i.due_date),
                "Status": i.status.value,
                "Description": i.description or "-",
                "Paid Timestamp": format_date(i.paid_at) if i.paid_at else "-",
            })
        st.dataframe(pd.DataFrame(inv_data), use_container_width=True, hide_index=True)

    with tab_reset:
        st.subheader("Re-seed Synthetic Demo Ledger")
        st.warning("⚠️ Re-initializing the database restores all baseline accounts, suppliers, invoices, and standard policies to their initial demo state.")
        if st.button("🔄 Reset to Default Seed Data", type="primary"):
            seed_database(db_path)
            st.success("Database successfully re-initialized with clean seed records.")
            st.rerun()
