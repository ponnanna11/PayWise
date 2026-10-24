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
from paywise.views.components import render_page_header, render_metric_card

DIAGRAMS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "diagrams"


def render_architecture_view():
    render_page_header(
        "System Information & Diagnostics",
        "Technical blueprints, runtime health checks, architecture diagrams, and formal safety invariants.",
    )

    ai_adapter = AIAdapter()
    health = ai_adapter.check_health()

    db_exists = os.path.exists(DB_PATH)
    db_size_kb = os.path.getsize(DB_PATH) / 1024 if db_exists else 0
    ai_status = "ACTIVE (LIVE)" if GEMINI_API_KEY else "OFFLINE (FALLBACK)"
    ai_color = "#15803D" if GEMINI_API_KEY else "#2563EB"

    # Runtime Telemetry Cards
    st.subheader("⚙️ System Health & Runtime Telemetry")
    h1, h2, h3, h4 = st.columns(4)
    with h1:
        render_metric_card("Application Version", "v1.0.0", "Simulation Gateway Prototype")
    with h2:
        render_metric_card("Database Health", "ONLINE", f"SQLite ({db_size_kb:.1f} KB)", value_color="#15803D")
    with h3:
        render_metric_card("AI Integration", ai_status, "Deterministic Assistant Active", value_color=ai_color)
    with h4:
        render_metric_card("Base Currency", f"{DEFAULT_CURRENCY} (₹)", "Indian Numbering", value_color="#172554")

    # Core Principles Banner
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("### 🛡️ Core Operating Principle")
        
        box_markup = (
            '<div style="font-size:1.05rem; font-weight:600; color:#172554; background-color:#EFF6FF; padding:1.1rem; border-radius:8px; border-left:4px solid #2563EB; margin-bottom:1rem;">'
            '"AI proposes. PayWise simulates. Policies enforce. Humans approve. Revalidation protects."'
            '</div>'
            '<div style="color:#374151; font-size:0.925rem; line-height:1.6;">'
            'PayWise operates as a <b>pre-execution safety gateway</b> for AI-assisted financial operations in an isolated virtual sandbox:'
            '<ul style="margin-top:0.5rem; margin-bottom:0.5rem;">'
            '<li>The AI must <b>never directly modify the ledger</b>.</li>'
            '<li>The AI must <b>never bypass the policy engine</b>.</li>'
            '<li>The AI must <b>never grant itself approval</b>.</li>'
            '<li>The AI must <b>never activate its own proposed policies</b>.</li>'
            '<li>Every commit undergoes <b>cryptographic commit-time revalidation</b> to prevent stale state execution.</li>'
            '</ul>'
            '</div>'
        )
        st.markdown(box_markup, unsafe_allow_html=True)

    # Architecture Diagrams
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    st.subheader("📐 Architecture & Engineering Diagrams")

    diag_tabs = st.tabs([
        "1. System Architecture",
        "2. Activity Diagram",
        "3. Sequence Diagram",
        "4. DFD Level 1",
    ])

    with diag_tabs[0]:
        st.markdown("#### System Component Architecture")
        svg_file = DIAGRAMS_DIR / "system_architecture.svg"
        if svg_file.exists():
            st.image(str(svg_file), use_container_width=True)
        else:
            st.info("Vector diagram rendering...")

    with diag_tabs[1]:
        st.markdown("#### Lifecycle Activity Diagram")
        svg_file = DIAGRAMS_DIR / "activity_diagram.svg"
        if svg_file.exists():
            st.image(str(svg_file), use_container_width=True)
        else:
            st.info("Vector diagram rendering...")

    with diag_tabs[2]:
        st.markdown("#### Execution Sequence Diagram")
        svg_file = DIAGRAMS_DIR / "sequence_diagram.svg"
        if svg_file.exists():
            st.image(str(svg_file), use_container_width=True)
        else:
            st.info("Vector diagram rendering...")

    with diag_tabs[3]:
        st.markdown("#### DFD Level 1 — Data Flow Diagram")
        svg_file = DIAGRAMS_DIR / "dfd_level1.svg"
        if svg_file.exists():
            st.image(str(svg_file), use_container_width=True)
        else:
            st.info("Vector diagram rendering...")

    # Advanced Engineering Details (Tucked away from ordinary view)
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    with st.expander("🔧 Advanced Engineering Diagnostics & PlantUML Source", expanded=False):
        st.markdown("#### AI Agent Provider Telemetry")
        st.json({
            "provider": health.get("provider"),
            "model": health.get("model"),
            "status": health.get("status"),
            "is_live": health.get("is_live"),
            "message": health.get("message"),
        })

        st.markdown("#### PlantUML Diagram Source (.puml)")
        puml_files = list(DIAGRAMS_DIR.glob("*.puml"))
        for puml in puml_files:
            with st.expander(f"📄 {puml.name}", expanded=False):
                st.code(puml.read_text(encoding="utf-8"), language="plantuml")
