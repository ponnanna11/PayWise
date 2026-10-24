"""
System Information & Architecture View for PayWise.
Displays system principles, model/provider health status, database diagnostics,
and embedded PlantUML architecture diagrams.
"""
from pathlib import Path
import os
import streamlit as st
from paywise.config import AI_MODEL, AI_PROVIDER, DB_PATH, DEFAULT_CURRENCY, GEMINI_API_KEY
from paywise.services.ai_adapter import AIAdapter
from paywise.views.components import render_page_header, render_ai_status_card

DIAGRAMS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "diagrams"


def render_architecture_view():
    render_page_header(
        "System Architecture & Diagnostics",
        "Technical blueprints, runtime health checks, PlantUML diagrams, and formal safety invariants.",
    )

    ai_adapter = AIAdapter()
    health = ai_adapter.check_health()

    # Runtime Health & Environment Summary
    st.subheader("⚙️ Runtime Environment & AI Diagnostics")
    render_ai_status_card(health)

    h1, h2, h3, h4 = st.columns(4)
    with h1:
        st.markdown(
            f"""
            <div class="pw-metric-card">
                <div class="pw-metric-label">Application Version</div>
                <div class="pw-metric-value" style="font-size:1.3rem;">v1.0.0</div>
                <div class="pw-metric-subtext">Simulation Prototype</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with h2:
        db_exists = os.path.exists(DB_PATH)
        db_size_kb = os.path.getsize(DB_PATH) / 1024 if db_exists else 0
        st.markdown(
            f"""
            <div class="pw-metric-card">
                <div class="pw-metric-label">Database Health</div>
                <div class="pw-metric-value" style="font-size:1.3rem; color:#0D9488;">ONLINE</div>
                <div class="pw-metric-subtext">SQLite ({db_size_kb:.1f} KB)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with h3:
        api_status = "KEY_CONFIGURED" if GEMINI_API_KEY else "UNCONFIGURED"
        api_color = "#0D9488" if GEMINI_API_KEY else "#D97706"
        st.markdown(
            f"""
            <div class="pw-metric-card">
                <div class="pw-metric-label">Gemini API Key</div>
                <div class="pw-metric-value" style="font-size:1.3rem; color:{api_color};">{api_status}</div>
                <div class="pw-metric-subtext">Environment Variable</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with h4:
        st.markdown(
            f"""
            <div class="pw-metric-card">
                <div class="pw-metric-label">Base Currency</div>
                <div class="pw-metric-value" style="font-size:1.3rem;">{DEFAULT_CURRENCY} (₹)</div>
                <div class="pw-metric-subtext">Indian Lakh/Crore</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Core Principles Banner
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(
            """
            ### 🛡️ Core Operating Principle
            <div style="font-size:1.1rem; font-weight:600; color:#1E3A8A; background-color:#EFF6FF; padding:1rem; border-radius:8px; border-left:4px solid #2563EB;">
            "AI proposes. PayWise simulates. Policies enforce. Humans approve. Revalidation protects."
            </div>
            
            <div style="margin-top:0.85rem; color:#334155; font-size:0.9rem; line-height:1.6;">
            PayWise is a <b>pre-execution safety gateway</b> for AI-assisted financial operations. The AI agent operates in an untrusted sandbox:
            <ul>
                <li>The AI must <b>never directly modify the ledger</b>.</li>
                <li>The AI must <b>never bypass the policy engine</b>.</li>
                <li>The AI must <b>never grant itself approval</b>.</li>
                <li>The AI must <b>never activate its own proposed policies</b>.</li>
                <li>Every commit undergoes <b>cryptographic commit-time revalidation</b> to prevent stale state execution.</li>
            </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Architecture Diagrams
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    st.subheader("📐 PlantUML Architecture Diagrams")

    diag_tabs = st.tabs([
        "1. System Architecture",
        "2. Activity Diagram",
        "3. Sequence Diagram",
        "4. DFD Level 1",
        "5. PlantUML Source (.puml)",
    ])

    with diag_tabs[0]:
        st.markdown("#### System Component Architecture")
        svg_file = DIAGRAMS_DIR / "system_architecture.svg"
        if svg_file.exists():
            st.image(str(svg_file), use_container_width=True)
        else:
            st.info("Rendered SVG diagram available in docs/diagrams.")

    with diag_tabs[1]:
        st.markdown("#### Lifecycle Activity Diagram")
        svg_file = DIAGRAMS_DIR / "activity_diagram.svg"
        if svg_file.exists():
            st.image(str(svg_file), use_container_width=True)
        else:
            st.info("Rendered SVG diagram available in docs/diagrams.")

    with diag_tabs[2]:
        st.markdown("#### Execution Sequence Diagram")
        svg_file = DIAGRAMS_DIR / "sequence_diagram.svg"
        if svg_file.exists():
            st.image(str(svg_file), use_container_width=True)
        else:
            st.info("Rendered SVG diagram available in docs/diagrams.")

    with diag_tabs[3]:
        st.markdown("#### DFD Level 1 — Data Flow Diagram")
        svg_file = DIAGRAMS_DIR / "dfd_level1.svg"
        if svg_file.exists():
            st.image(str(svg_file), use_container_width=True)
        else:
            st.info("Rendered SVG diagram available in docs/diagrams.")

    with diag_tabs[4]:
        st.markdown("#### PlantUML Source Code Files")
        puml_files = list(DIAGRAMS_DIR.glob("*.puml"))
        for puml in puml_files:
            with st.expander(f"📄 {puml.name}", expanded=False):
                st.code(puml.read_text(encoding="utf-8"), language="plantuml")
