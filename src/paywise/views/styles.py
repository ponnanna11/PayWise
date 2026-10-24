"""
Modern, minimalist SaaS design system stylesheet for PayWise.
Implements a clean typography hierarchy (Inter font), refined neutral palette,
subtle borders, restrained shadows, and semantic severity styling.
"""
import streamlit as st


def apply_custom_styles():
    st.markdown(
        """
        <style>
        /* Modern Inter font & base layout */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"], .stMarkdown {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: #0F172A;
        }

        /* App Background */
        .stApp {
            background-color: #F8FAFC;
        }

        /* Top Page Header */
        .pw-page-header {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 1.25rem 1.75rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04);
        }

        .pw-page-title {
            font-size: 1.625rem;
            font-weight: 700;
            color: #0F172A;
            margin: 0;
            letter-spacing: -0.02em;
        }

        .pw-page-subtitle {
            font-size: 0.925rem;
            color: #64748B;
            margin-top: 0.35rem;
            line-height: 1.45;
        }

        /* Metric Cards */
        .pw-metric-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 1.15rem 1.25rem;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
            transition: border-color 0.15s ease, box-shadow 0.15s ease;
            height: 100%;
        }

        .pw-metric-card:hover {
            border-color: #CBD5E1;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }

        .pw-metric-label {
            font-size: 0.775rem;
            font-weight: 600;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .pw-metric-value {
            font-size: 1.65rem;
            font-weight: 700;
            color: #0F172A;
            margin-top: 0.35rem;
            letter-spacing: -0.02em;
        }

        .pw-metric-subtext {
            font-size: 0.8rem;
            color: #94A3B8;
            margin-top: 0.25rem;
        }

        /* Status & Severity Badges */
        .pw-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.22rem 0.65rem;
            font-size: 0.775rem;
            font-weight: 600;
            border-radius: 9999px;
            letter-spacing: 0.02em;
        }

        .pw-badge-block {
            background-color: #FEF2F2;
            color: #991B1B;
            border: 1px solid #FCA5A5;
        }

        .pw-badge-approval {
            background-color: #FFFBEB;
            color: #92400E;
            border: 1px solid #FCD34D;
        }

        .pw-badge-warn {
            background-color: #EFF6FF;
            color: #1E40AF;
            border: 1px solid #BFDBFE;
        }

        .pw-badge-success {
            background-color: #F0FDF4;
            color: #166534;
            border: 1px solid #BBF7D0;
        }

        .pw-badge-neutral {
            background-color: #F1F5F9;
            color: #475569;
            border: 1px solid #E2E8F0;
        }

        /* Policy Finding Cards */
        .pw-finding-card {
            background: #FFFFFF;
            border-radius: 8px;
            padding: 1rem 1.25rem;
            margin-bottom: 0.85rem;
            border: 1px solid #E2E8F0;
            border-left-width: 4px;
        }

        .pw-finding-block {
            border-left-color: #DC2626;
            background-color: #FEF2F2;
        }

        .pw-finding-approval {
            border-left-color: #D97706;
            background-color: #FFFBEB;
        }

        .pw-finding-warn {
            border-left-color: #2563EB;
            background-color: #EFF6FF;
        }

        /* Simulation Banner */
        .pw-simulation-banner {
            background-color: #EFF6FF;
            border: 1px solid #BFDBFE;
            color: #1E40AF;
            padding: 0.65rem 1rem;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1.25rem;
        }

        /* Empty State */
        .pw-empty-state {
            background: #FFFFFF;
            border: 1px dashed #CBD5E1;
            border-radius: 10px;
            padding: 2.5rem 1.5rem;
            text-align: center;
            color: #64748B;
        }

        /* Refined Buttons */
        .stButton>button {
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.15s ease;
        }

        /* Tables & Dataframes */
        .stDataFrame {
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            overflow: hidden;
            background: #FFFFFF;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid #E2E8F0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
