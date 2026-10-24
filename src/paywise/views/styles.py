"""
Modern, accessible light fintech SaaS design system stylesheet for PayWise.
Implements a refined light-blue fintech palette, clear typography hierarchy (Inter),
subtle card borders, accessible contrast, semantic status indicators,
and eliminates dark bands and code-block rendering anomalies.
"""
import streamlit as st


def apply_custom_styles():
    st.markdown(
        """
        <style>
        /* Import Inter font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* Global Typography & Resets */
        html, body, [class*="css"], .stMarkdown, .stText, p, span, label, div {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            color: #1F2937;
        }

        /* Base App Canvas */
        .stApp {
            background-color: #F5F8FF !important;
            color: #1F2937 !important;
        }

        /* 1. Remove Top Black Band & Seamlessly Style Streamlit Header */
        header[data-testid="stHeader"] {
            background-color: #F5F8FF !important;
            border-bottom: 1px solid #DCE6F5 !important;
            color: #172554 !important;
            height: 2.75rem !important;
        }

        header[data-testid="stHeader"] svg {
            fill: #172554 !important;
        }

        /* Content Container Spacing */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 3rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 1400px !important;
        }

        /* Headings Hierarchy */
        h1, .pw-page-title {
            font-size: 1.85rem !important;
            font-weight: 700 !important;
            color: #172554 !important;
            letter-spacing: -0.025em !important;
            margin-bottom: 0.35rem !important;
        }

        h2, h3, .stSubheader {
            font-size: 1.35rem !important;
            font-weight: 600 !important;
            color: #172554 !important;
            letter-spacing: -0.015em !important;
            margin-top: 1.25rem !important;
            margin-bottom: 0.75rem !important;
        }

        h4 {
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            color: #172554 !important;
        }

        p, .stMarkdown p {
            font-size: 0.95rem !important;
            line-height: 1.55 !important;
            color: #374151 !important;
        }

        /* Page Header Banner Component */
        .pw-page-header {
            background: #FFFFFF;
            border: 1px solid #DCE6F5;
            border-radius: 12px;
            padding: 1.35rem 1.75rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px 0 rgba(37, 99, 235, 0.04);
        }

        .pw-page-title {
            font-size: 1.85rem !important;
            font-weight: 700;
            color: #172554;
            margin: 0;
            line-height: 1.25;
        }

        .pw-page-subtitle {
            font-size: 0.95rem;
            color: #526581;
            margin-top: 0.35rem;
            line-height: 1.5;
        }

        /* Metric Cards */
        .pw-metric-card {
            background: #FFFFFF;
            border: 1px solid #DCE6F5;
            border-radius: 10px;
            padding: 1.25rem 1.35rem;
            box-shadow: 0 1px 2px 0 rgba(37, 99, 235, 0.03);
            transition: border-color 0.15s ease, box-shadow 0.15s ease;
            height: 100%;
        }

        .pw-metric-card:hover {
            border-color: #BFDBFE;
            box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.06);
        }

        .pw-metric-label {
            font-size: 0.825rem;
            font-weight: 600;
            color: #526581;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .pw-metric-value {
            font-size: 1.85rem;
            font-weight: 700;
            color: #172554;
            margin-top: 0.4rem;
            letter-spacing: -0.02em;
            line-height: 1.2;
        }

        .pw-metric-subtext {
            font-size: 0.85rem;
            color: #64748B;
            margin-top: 0.35rem;
            font-weight: 400;
        }

        /* Status & Severity Badges */
        .pw-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.25rem 0.75rem;
            font-size: 0.825rem;
            font-weight: 600;
            border-radius: 9999px;
            letter-spacing: 0.02em;
            white-space: nowrap;
        }

        .pw-badge-block {
            background-color: #FEF2F2 !important;
            color: #B91C1C !important;
            border: 1px solid #FCA5A5 !important;
        }

        .pw-badge-approval {
            background-color: #FFFBEB !important;
            color: #B45309 !important;
            border: 1px solid #FCD34D !important;
        }

        .pw-badge-warn {
            background-color: #EFF6FF !important;
            color: #1D4ED8 !important;
            border: 1px solid #BFDBFE !important;
        }

        .pw-badge-success {
            background-color: #F0FDF4 !important;
            color: #15803D !important;
            border: 1px solid #86EFAC !important;
        }

        .pw-badge-neutral {
            background-color: #F8FAFC !important;
            color: #475569 !important;
            border: 1px solid #DCE6F5 !important;
        }

        /* Policy Finding Cards — Light, accessible styling */
        .pw-finding-card {
            background: #FFFFFF;
            border-radius: 10px;
            padding: 1.15rem 1.35rem;
            margin-bottom: 0.85rem;
            border: 1px solid #DCE6F5;
            border-left-width: 5px;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
        }

        .pw-finding-block {
            border-left-color: #DC2626 !important;
            background-color: #FFFFFF !important;
        }

        .pw-finding-approval {
            border-left-color: #D97706 !important;
            background-color: #FFFFFF !important;
        }

        .pw-finding-warn {
            border-left-color: #2563EB !important;
            background-color: #FFFFFF !important;
        }

        .pw-finding-title {
            font-weight: 600;
            font-size: 1.05rem;
            color: #172554;
            margin-top: 0.45rem;
            margin-bottom: 0.25rem;
        }

        .pw-finding-desc {
            font-size: 0.925rem;
            color: #374151;
            line-height: 1.5;
            margin-top: 0.25rem;
        }

        .pw-finding-remedy {
            margin-top: 0.6rem;
            padding: 0.5rem 0.75rem;
            background: #EFF6FF;
            border: 1px solid #DBEAFE;
            border-radius: 6px;
            font-size: 0.875rem;
            color: #1E40AF;
        }

        /* Empty State */
        .pw-empty-state {
            background: #FFFFFF;
            border: 1px dashed #CBD5E1;
            border-radius: 10px;
            padding: 2.5rem 1.5rem;
            text-align: center;
            color: #526581;
        }

        /* Primary and Secondary Buttons */
        .stButton > button {
            border-radius: 8px !important;
            font-weight: 500 !important;
            font-size: 0.95rem !important;
            padding: 0.5rem 1.15rem !important;
            transition: all 0.15s ease !important;
        }

        .stButton > button[kind="primary"] {
            background-color: #2563EB !important;
            border-color: #2563EB !important;
            color: #FFFFFF !important;
            box-shadow: 0 1px 2px 0 rgba(37, 99, 235, 0.2) !important;
        }

        .stButton > button[kind="primary"]:hover {
            background-color: #1D4ED8 !important;
            border-color: #1D4ED8 !important;
            box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3) !important;
        }

        .stButton > button[kind="secondary"] {
            background-color: #FFFFFF !important;
            border-color: #DCE6F5 !important;
            color: #172554 !important;
        }

        .stButton > button[kind="secondary"]:hover {
            border-color: #93C5FD !important;
            background-color: #EFF6FF !important;
            color: #2563EB !important;
        }

        /* Clean Light Tables & DataFrames */
        .stDataFrame, div[data-testid="stDataFrame"] {
            border: 1px solid #DCE6F5 !important;
            border-radius: 10px !important;
            overflow: hidden !important;
            background-color: #FFFFFF !important;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.02) !important;
        }

        div[data-testid="stDataFrame"] div[role="grid"] {
            font-size: 0.925rem !important;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #DCE6F5 !important;
            box-shadow: 1px 0 3px 0 rgba(37, 99, 235, 0.03) !important;
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.5rem !important;
            padding-left: 1.25rem !important;
            padding-right: 1.25rem !important;
        }

        /* Sidebar Nav Button Styles */
        .stSidebar .stButton > button {
            text-align: left !important;
            justify-content: flex-start !important;
            font-size: 0.925rem !important;
            font-weight: 500 !important;
            padding: 0.55rem 0.85rem !important;
            border-radius: 8px !important;
            margin-bottom: 0.25rem !important;
            width: 100% !important;
        }

        /* Form Inputs */
        .stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {
            border: 1px solid #DCE6F5 !important;
            border-radius: 8px !important;
            font-size: 0.95rem !important;
            color: #1F2937 !important;
            background-color: #FFFFFF !important;
        }

        .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
            border-color: #2563EB !important;
            box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15) !important;
        }

        /* Form Labels */
        .stTextInput label, .stNumberInput label, .stSelectbox label, .stTextArea label, .stDateInput label {
            font-size: 0.925rem !important;
            font-weight: 600 !important;
            color: #172554 !important;
            margin-bottom: 0.35rem !important;
        }

        /* Card Container (Native st.container with border) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #FFFFFF !important;
            border: 1px solid #DCE6F5 !important;
            border-radius: 10px !important;
            padding: 1.25rem !important;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.02) !important;
        }

        /* Progress Bar */
        .stProgress > div > div > div > div {
            background-color: #2563EB !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
