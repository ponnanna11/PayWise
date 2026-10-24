"""
PayWise — Pre-execution Safety Gateway for AI-Assisted Financial Operations
Simulate Before You Pay
Main Streamlit Application Entrypoint
"""
import os
import sys
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

# Apply custom SaaS stylesheet
apply_custom_styles()

# Sidebar Navigation
logo_path = Path(__file__).parent / "assets" / "paywise_logo.png"

with st.sidebar:
    if logo_path.exists():
        st.image(str(logo_path), width=240)
    else:
        st.markdown("## 🛡️ **PayWise**")
        st.caption("Simulate Before You Pay")

    st.markdown("<div style='margin-bottom:0.75rem;'></div>", unsafe_allow_html=True)

    nav_icons = {
        "Dashboard": "📊 Dashboard",
        "Proposals": "📋 Proposals",
        "New Proposal": "🤖 Agent Operations",
        "Simulation & Preview": "🔬 Simulation & Preview",
        "Approvals": "✍️ Approvals",
        "Policy Management": "🛡️ Policy Management",
        "Ledger": "🏦 Simulated Ledger",
        "Audit Trail": "📜 Audit Trail",
        "System Information": "⚙️ System Information",
    }

    nav_options = list(nav_icons.keys())

    current_page = st.session_state.get("current_page", "Dashboard")
    if current_page not in nav_options:
        current_page = "Dashboard"

    selected_page = st.radio(
        "Navigation",
        nav_options,
        index=nav_options.index(current_page),
        format_func=lambda x: nav_icons.get(x, x),
        key="nav_radio",
    )
    st.session_state["current_page"] = selected_page

    st.markdown("---")
    st.markdown(
        """
        <div style="font-size: 0.8rem; color: #64748B; line-height: 1.5; background: #F8FAFC; padding: 0.75rem; border-radius: 6px; border: 1px solid #E2E8F0;">
            <b style="color:#0F172A;">Core Safety Invariant:</b><br>
            <i>AI proposes. PayWise simulates. Policies enforce. Humans approve. Revalidation protects.</i>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("PayWise v1.0.0 • SQLite • Simulation Only")

# Router
page = st.session_state["current_page"]

if page == "Dashboard":
    render_dashboard(DB_PATH)
elif page == "Proposals":
    render_proposals_view(DB_PATH)
elif page == "New Proposal":
    render_new_proposal_view(DB_PATH)
elif page == "Simulation & Preview":
    render_simulation_view(DB_PATH)
elif page == "Approvals":
    render_approvals_view(DB_PATH)
elif page == "Policy Management":
    render_policies_view(DB_PATH)
elif page == "Ledger":
    render_ledger_view(DB_PATH)
elif page == "Audit Trail":
    render_audit_view(DB_PATH)
elif page == "System Information":
    render_architecture_view()
