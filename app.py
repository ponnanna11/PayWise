"""
PayWise — Pre-execution Safety Gateway for AI-Assisted Financial Operations
Simulate Before You Pay
Main Streamlit Application Entrypoint
"""
import os
import sys
import textwrap
from pathlib import Path

# Ensure src is in Python path for local execution and Streamlit
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import streamlit as st

from paywise.config import DB_PATH
from paywise.utils.seed_data import seed_database
from paywise.views import (
    apply_custom_styles,
    render_architecture_view,
    render_audit_view,
    render_approvals_view,
    render_dashboard,
    render_ledger_view,
    render_new_proposal_view,
    render_policies_view,
    render_proposals_view,
    render_simulation_view,
)

# Page configuration
st.set_page_config(
    page_title="PayWise — Simulate Before You Pay",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize and seed database if not already present
@st.cache_resource
def setup_database():
    seed_database(DB_PATH)
    return True

setup_database()

# Apply custom light fintech stylesheet
apply_custom_styles()

# Sidebar Navigation
logo_path = Path(__file__).parent / "assets" / "paywise_logo.png"

with st.sidebar:
    if logo_path.exists():
        st.image(str(logo_path), width=230)
    else:
        st.markdown("## 🛡️ **PayWise**")
        st.caption("Simulate Before You Pay")

    st.markdown("<div style='margin-bottom: 0.75rem;'></div>", unsafe_allow_html=True)

    nav_items = [
        ("Dashboard", "📊  Dashboard"),
        ("Payment Proposals", "📋  Payment Proposals"),
        ("Create Proposal", "✨  Create Proposal"),
        ("Simulation & Preview", "🔬  Simulation & Preview"),
        ("Approvals", "✍️  Approvals"),
        ("Safety Policies", "🛡️  Safety Policies"),
        ("Simulated Ledger", "🏦  Simulated Ledger"),
        ("Audit Trail", "📜  Audit Trail"),
        ("System Information", "⚙️  System Information"),
    ]

    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Dashboard"

    current_page = st.session_state["current_page"]
    nav_keys = [item[0] for item in nav_items]
    if current_page not in nav_keys:
        current_page = "Dashboard"
        st.session_state["current_page"] = "Dashboard"

    for key, label in nav_items:
        is_active = (key == current_page)
        btn_type = "primary" if is_active else "secondary"
        if st.button(label, key=f"nav_btn_{key}", type=btn_type, use_container_width=True):
            if current_page != key:
                st.session_state["current_page"] = key
                st.rerun()

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("---")

    footer_markup = textwrap.dedent("""
        <div style="font-size: 0.825rem; color: #526581; line-height: 1.5; background: #F5F8FF; padding: 0.85rem; border-radius: 8px; border: 1px solid #DCE6F5;">
            <b style="color:#172554;">Core Safety Invariant:</b><br>
            <i>AI proposes. PayWise simulates. Policies enforce. Humans approve. Revalidation protects.</i>
        </div>
    """).strip()
    st.markdown(footer_markup, unsafe_allow_html=True)
    st.caption("PayWise v1.0.0 • SQLite • Simulation Only")

# Page Router
page = st.session_state.get("current_page", "Dashboard")

if page == "Dashboard":
    render_dashboard(DB_PATH)
elif page == "Payment Proposals":
    render_proposals_view(DB_PATH)
elif page == "Create Proposal":
    render_new_proposal_view(DB_PATH)
elif page == "Simulation & Preview":
    render_simulation_view(DB_PATH)
elif page == "Approvals":
    render_approvals_view(DB_PATH)
elif page == "Safety Policies":
    render_policies_view(DB_PATH)
elif page == "Simulated Ledger":
    render_ledger_view(DB_PATH)
elif page == "Audit Trail":
    render_audit_view(DB_PATH)
elif page == "System Information":
    render_architecture_view()
