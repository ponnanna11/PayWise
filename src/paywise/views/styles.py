"""
Modern, accessible light fintech SaaS design system stylesheet for PayWise.
Implements a refined light-blue fintech palette, clear typography hierarchy (Inter),
subtle card borders, accessible contrast, semantic status indicators,
and precise vertical and horizontal text alignment.
"""
import streamlit as st


def apply_custom_styles():
    st.markdown(
        """
        <style>
        /* Import Inter and Material Symbols Rounded fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap');

        /* Global Typography & Resets - Do not override span and div with !important to protect icon fonts */
        html, body, .stApp {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: #1F2937;
        }

        .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, input, textarea, select, button {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }

        /* Preserve Streamlit Material Symbols Icon Font & Ligatures Everywhere */
        [data-testid*="stIcon"],
        [data-testid="stIconMaterial"],
        [data-testid="stIconEmoji"],
        [data-testid="stExpanderStepChevron"],
        [data-testid*="Chevron"],
        span[translate="no"],
        span[data-testid="stIconMaterial"],
        .material-symbols-rounded,
        .material-symbols-outlined,
        .material-icons {
            font-family: "Material Symbols Rounded", "Material Symbols Outlined", sans-serif !important;
            font-style: normal !important;
            font-weight: normal !important;
            text-transform: none !important;
            letter-spacing: normal !important;
            word-wrap: normal !important;
            white-space: nowrap !important;
            direction: ltr !important;
            -webkit-font-feature-settings: 'liga' 1 !important;
            font-feature-settings: 'liga' 1 !important;
            -webkit-font-smoothing: antialiased !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
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

        /* Standardized Heading Styles with Clean Margins */
        h1, .pw-page-title {
            font-size: 1.85rem !important;
            font-weight: 700 !important;
            color: #172554 !important;
            letter-spacing: -0.025em !important;
            margin: 0 0 0.35rem 0 !important;
            padding: 0 !important;
            line-height: 1.25 !important;
        }

        h2, h3, .stSubheader {
            font-size: 1.35rem !important;
            font-weight: 600 !important;
            color: #172554 !important;
            letter-spacing: -0.015em !important;
            margin-top: 1.25rem !important;
            margin-bottom: 0.75rem !important;
            line-height: 1.3 !important;
        }

        h4 {
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            color: #172554 !important;
            margin-top: 0.75rem !important;
            margin-bottom: 0.35rem !important;
            line-height: 1.3 !important;
        }

        p, .stMarkdown p {
            font-size: 0.95rem !important;
            line-height: 1.55 !important;
            color: #374151 !important;
            margin-top: 0 !important;
            margin-bottom: 0.4rem !important;
        }

        /* Universal Baseline Alignment for Columns and Cards */
        div[data-testid="column"] {
            min-width: 0 !important;
        }

        div[data-testid="column"] .stMarkdown:first-child,
        div[data-testid="column"] .stMarkdown:first-child > div,
        div[data-testid="column"] .stMarkdown:first-child > div > h1,
        div[data-testid="column"] .stMarkdown:first-child > div > h2,
        div[data-testid="column"] .stMarkdown:first-child > div > h3,
        div[data-testid="column"] .stMarkdown:first-child > div > h4,
        div[data-testid="column"] .stMarkdown:first-child > div > p,
        div[data-testid="column"] .stCaption:first-child,
        div[data-testid="column"] .stCaption:first-child > div,
        div[data-testid="column"] .stCaption:first-child p,
        div[data-testid="column"] div:first-child > .pw-column-eyebrow,
        div[data-testid="stVerticalBlockBorderWrapper"] .stMarkdown:first-child > div > h1,
        div[data-testid="stVerticalBlockBorderWrapper"] .stMarkdown:first-child > div > h2,
        div[data-testid="stVerticalBlockBorderWrapper"] .stMarkdown:first-child > div > h3,
        div[data-testid="stVerticalBlockBorderWrapper"] .stMarkdown:first-child > div > p {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }

        /* Column Eyebrow Labels for Perfect Horizontal Rhythms */
        .pw-column-eyebrow {
            font-size: 0.775rem !important;
            font-weight: 600 !important;
            color: #526581 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            margin: 0 0 0.35rem 0 !important;
            padding: 0 !important;
            line-height: 1.2 !important;
            text-align: left !important;
        }

        .pw-column-eyebrow-right {
            font-size: 0.775rem !important;
            font-weight: 600 !important;
            color: #526581 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            margin: 0 0 0.35rem 0 !important;
            padding: 0 !important;
            line-height: 1.2 !important;
            text-align: right !important;
        }

        /* Page Header Banner Component */
        .pw-page-header {
            background: #FFFFFF;
            border: 1px solid #DCE6F5;
            border-radius: 12px;
            padding: 1.35rem 1.75rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px 0 rgba(37, 99, 235, 0.04);
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .pw-page-title {
            font-size: 1.85rem !important;
            font-weight: 700 !important;
            color: #172554 !important;
            margin: 0 0 0.35rem 0 !important;
            padding: 0 !important;
            line-height: 1.25 !important;
            text-align: left !important;
        }

        .pw-page-subtitle {
            font-size: 0.95rem !important;
            color: #526581 !important;
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1.5 !important;
            text-align: left !important;
        }

        /* Metric Cards - Aligned Horizontally Across Rows */
        .pw-metric-card {
            background: #FFFFFF;
            border: 1px solid #DCE6F5;
            border-radius: 10px;
            padding: 1.15rem 1.25rem;
            box-shadow: 0 1px 2px 0 rgba(37, 99, 235, 0.03);
            transition: border-color 0.15s ease, box-shadow 0.15s ease;
            height: 100%;
            min-height: 112px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-sizing: border-box;
            text-align: left;
        }

        .pw-metric-card:hover {
            border-color: #BFDBFE;
            box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.06);
        }

        .pw-metric-label {
            font-size: 0.8rem;
            font-weight: 600;
            color: #526581;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin: 0;
            line-height: 1.2;
            text-align: left;
        }

        .pw-metric-value {
            font-size: 1.85rem;
            font-weight: 700;
            color: #172554;
            margin: 0.35rem 0 0 0;
            letter-spacing: -0.02em;
            line-height: 1.2;
            text-align: left;
        }

        .pw-metric-subtext {
            font-size: 0.825rem;
            color: #64748B;
            margin: 0.35rem 0 0 0;
            font-weight: 400;
            line-height: 1.3;
            text-align: left;
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
            line-height: 1.3;
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
            text-align: left;
            word-break: break-word !important;
            overflow-wrap: break-word !important;
            box-sizing: border-box !important;
            max-width: 100% !important;
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
            font-weight: 600 !important;
            font-size: 1.05rem !important;
            color: #172554 !important;
            margin: 0.5rem 0 0.25rem 0 !important;
            line-height: 1.35 !important;
            text-align: left !important;
        }

        .pw-finding-desc {
            font-size: 0.925rem !important;
            color: #374151 !important;
            line-height: 1.5 !important;
            margin: 0.25rem 0 0 0 !important;
            text-align: left !important;
        }

        .pw-finding-remedy {
            margin-top: 0.6rem !important;
            padding: 0.5rem 0.75rem !important;
            background: #EFF6FF !important;
            border: 1px solid #DBEAFE !important;
            border-radius: 6px !important;
            font-size: 0.875rem !important;
            color: #1E40AF !important;
            line-height: 1.4 !important;
            text-align: left !important;
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

        /* Sidebar Nav Button Styles: Explicit Left Text Alignment */
        .stSidebar .stButton > button,
        .stSidebar div[data-testid="stButton"] button {
            text-align: left !important;
            justify-content: flex-start !important;
            align-items: center !important;
            display: flex !important;
            font-size: 0.925rem !important;
            font-weight: 500 !important;
            padding: 0.6rem 0.9rem !important;
            border-radius: 8px !important;
            margin-bottom: 0.25rem !important;
            width: 100% !important;
        }

        .stSidebar .stButton > button *,
        .stSidebar div[data-testid="stButton"] button *,
        .stSidebar .stButton > button div[data-testid="stMarkdownContainer"],
        .stSidebar .stButton > button div[data-testid="stMarkdownContainer"] > p,
        .stSidebar .stButton > button span {
            text-align: left !important;
            justify-content: flex-start !important;
            align-items: center !important;
            display: flex !important;
            width: 100% !important;
            margin: 0 !important;
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
        .stTextInput label, .stNumberInput label, .stSelectbox label, .stTextArea label, .stDateInput label,
        label[data-testid="stWidgetLabel"], label[data-testid="stWidgetLabel"] p {
            font-size: 0.925rem !important;
            font-weight: 600 !important;
            color: #172554 !important;
            margin-bottom: 0.35rem !important;
            text-align: left !important;
            justify-content: flex-start !important;
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

        /* Streamlit Expander - Clean card styling, no overlapping chevron text */
        div[data-testid="stExpander"],
        details[data-testid="stExpander"] {
            background-color: #FFFFFF !important;
            border: 1px solid #DCE6F5 !important;
            border-radius: 10px !important;
            margin-top: 0.75rem !important;
            margin-bottom: 0.75rem !important;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.02) !important;
            overflow: hidden !important;
        }

        details[data-testid="stExpander"] > summary {
            padding: 0.75rem 1rem !important;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
            color: #172554 !important;
            display: flex !important;
            align-items: center !important;
            gap: 0.65rem !important;
            cursor: pointer !important;
        }

        details[data-testid="stExpander"] > summary:hover {
            background-color: #F8FAFC !important;
            color: #2563EB !important;
        }

        details[data-testid="stExpander"] > summary [data-testid="stExpanderStepChevron"],
        details[data-testid="stExpander"] > summary span[data-testid*="stIcon"],
        details[data-testid="stExpander"] > summary svg {
            flex-shrink: 0 !important;
            min-width: 1.25rem !important;
            width: 1.25rem !important;
            height: 1.25rem !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin-right: 0.25rem !important;
        }

        details[data-testid="stExpander"] > summary p,
        details[data-testid="stExpander"] > summary span {
            margin: 0 !important;
            padding: 0 !important;
        }

        details[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
            padding: 1rem 1.25rem !important;
            border-top: 1px solid #EDF2F7 !important;
            background-color: #FFFFFF !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
