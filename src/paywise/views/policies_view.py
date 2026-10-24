"""
Safety Policies View for PayWise.
Enables viewing safety rules, configuring thresholds, activating policies, and drafting new policies via AI.
"""
import textwrap
import streamlit as st
import pandas as pd
from paywise.models.policy import Policy, PolicyRuleType, PolicySeverity
from paywise.repositories.policy_repo import PolicyRepository
from paywise.services.ai_adapter import AIAdapter
from paywise.services.policy_service import PolicyService
from paywise.utils.formatters import format_inr
from paywise.views.components import (
    render_page_header,
    render_empty_state,
)


def render_policies_view(db_path: str):
    render_page_header(
        "Safety Policies & Governance Rules",
        "Deterministic safety rules, configurable financial thresholds, and AI-assisted policy drafting.",
    )

    policy_service = PolicyService(db_path)
    policy_repo = PolicyRepository(db_path)
    policies = policy_repo.list_all()

    tab_active, tab_ai, tab_manual = st.tabs([
        "📋 Active & Mandatory Policies",
        "✨ AI Policy Drafting Assistant",
        "➕ Add Custom Financial Rule",
    ])

    # TAB 1: ACTIVE & MANDATORY POLICIES
    with tab_active:
        st.subheader("Configured Safety Rules & Thresholds")
        st.info("💡 **Mandatory Safety Rules** (such as Insufficient Funds, Minimum Reserve Protection, Stale State Detection) cannot be deactivated. **Configurable Business Rules** (such as Discretionary Approval Thresholds, Batch Ceilings, Split Detection) can have their thresholds tuned and their activation toggled.")

        # Separate into Mandatory Safety Guards vs Configurable Rules
        mandatories = [p for p in policies if p.is_mandatory]
        configurables = [p for p in policies if not p.is_mandatory]

        st.markdown(f"#### 🔒 Mandatory Safety Guards ({len(mandatories)})")
        for pol in mandatories:
            with st.container(border=True):
                p1, p2, p3 = st.columns([2.5, 1, 1.2])
                with p1:
                    st.markdown(
                        f"<div class='pw-column-eyebrow'>SAFETY INVARIANT</div>"
                        f"<div style='font-weight:700; font-size:1.1rem; color:#172554; line-height:1.3; margin:0.25rem 0 0.35rem 0;'>{pol.name} <code style='font-size:0.8rem; font-weight:normal;'>{pol.id}</code></div>",
                        unsafe_allow_html=True,
                    )
                    st.write(pol.description)
                    st.caption(f"Rule Type: `{pol.rule_type.value}` • Version: **v{pol.version}**")
                    if pol.parameters:
                        with st.expander("Parameters & Thresholds", expanded=False):
                            st.json(pol.parameters)
                with p2:
                    st.markdown(
                        f"<div class='pw-column-eyebrow'>POLICY SEVERITY</div>"
                        f"<div style='margin:0.25rem 0 0.35rem 0;'><span class='pw-badge pw-badge-block'>🛑 {pol.severity.value}</span></div>"
                        f"<div style='font-size:0.825rem; color:#B91C1C; font-weight:600;'>🔒 Mandatory Invariant</div>",
                        unsafe_allow_html=True,
                    )
                with p3:
                    st.markdown("<div class='pw-column-eyebrow-right'>STATUS</div>", unsafe_allow_html=True)
                    st.button("Active (Locked)", key=f"lock_{pol.id}", disabled=True, use_container_width=True)

        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown(f"#### ⚙️ Configurable Business Rules ({len(configurables)})")
        for pol in configurables:
            sev_val = pol.severity.value
            badge_cls = "pw-badge-approval" if sev_val == "REQUIRE_APPROVAL" else "pw-badge-warn"
            icon = "⚠️" if sev_val == "REQUIRE_APPROVAL" else "ℹ️"

            with st.container(border=True):
                p1, p2, p3 = st.columns([2.5, 1, 1.2])
                with p1:
                    st.markdown(
                        f"<div class='pw-column-eyebrow'>BUSINESS RULE</div>"
                        f"<div style='font-weight:700; font-size:1.1rem; color:#172554; line-height:1.3; margin:0.25rem 0 0.35rem 0;'>{pol.name} <code style='font-size:0.8rem; font-weight:normal;'>{pol.id}</code></div>",
                        unsafe_allow_html=True,
                    )
                    st.write(pol.description)
                    st.caption(f"Rule Type: `{pol.rule_type.value}` • Version: **v{pol.version}**")
                    if pol.parameters:
                        with st.expander("Parameters & Thresholds", expanded=False):
                            st.json(pol.parameters)
                with p2:
                    st.markdown(
                        f"<div class='pw-column-eyebrow'>POLICY SEVERITY</div>"
                        f"<div style='margin:0.25rem 0 0.35rem 0;'><span class='pw-badge {badge_cls}'>{icon} {sev_val}</span></div>"
                        f"<div style='font-size:0.825rem; color:#15803D; font-weight:600;'>⚙️ Configurable Rule</div>",
                        unsafe_allow_html=True,
                    )
                with p3:
                    st.markdown("<div class='pw-column-eyebrow-right'>ACTION</div>", unsafe_allow_html=True)
                    is_active = pol.is_active
                    btn_label = "Deactivate" if is_active else "Activate"
                    btn_type = "secondary" if is_active else "primary"
                    if st.button(btn_label, key=f"tog_{pol.id}", type=btn_type, use_container_width=True):
                        try:
                            policy_service.toggle_activation(pol.id, not is_active)
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

    # TAB 2: AI POLICY DRAFTING ASSISTANT
    with tab_ai:
        st.subheader("AI Policy Drafting Assistant (Untrusted Draft)")
        
        box_markup = textwrap.dedent("""
            <div style="background:#FFFFFF; border:1px solid #DCE6F5; border-left:4px solid #2563EB; padding:1.1rem 1.35rem; border-radius:10px; margin-bottom:1.25rem; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.02);">
                <div style="font-size:0.925rem; color:#172554; font-weight:600; margin-bottom:0.25rem;">
                    Natural Language Governance Translator:
                </div>
                <div style="font-size:0.9rem; color:#374151; line-height:1.5;">
                    Enter an operational policy rule in plain English (e.g. <i>'Payments exceeding ₹75,000 require manager approval'</i>).
                    The AI assistant translates it into a structured, validated candidate policy schema.
                </div>
                <div style="font-size:0.85rem; color:#B45309; margin-top:0.5rem; font-weight:500;">
                    ⚠️ <b>Safety Boundary</b>: The AI cannot activate policies directly. A human administrator must verify the candidate schema and explicitly authorize activation.
                </div>
            </div>
        """).strip()
        st.markdown(box_markup, unsafe_allow_html=True)

        ai_input = st.text_input(
            "Natural Language Business Policy",
            value="Disbursements exceeding ₹75,000 require manager approval.",
        )

        if st.button("✨ Draft Candidate Policy Schema", type="primary"):
            ai_adapter = AIAdapter()
            draft = ai_adapter.draft_policy_from_text(ai_input)
            st.session_state["candidate_policy"] = draft

        if "candidate_policy" in st.session_state:
            candidate = st.session_state["candidate_policy"]
            st.markdown("---")
            st.markdown("#### 📄 Candidate Policy Definition (Untrusted Draft)")
            with st.container(border=True):
                st.markdown(f"**Interpreted Intent**: {candidate['ai_interpretation']}")
                st.markdown(f"**Generated Rule Name**: `{candidate['name']}`")
                st.markdown(f"**Rule Type**: `{candidate['rule_type']}`")
                st.markdown(f"**Severity**: `{candidate['severity']}`")
                st.markdown(f"**Parameters**: `{candidate['parameters']}`")

                # Validation verification
                val = policy_service.validate_policy_draft(
                    name=candidate["name"],
                    rule_type=candidate["rule_type"],
                    severity=candidate["severity"],
                    parameters=candidate["parameters"],
                )

                if val["is_valid"]:
                    st.success("✅ Candidate passed schema and parameter validation!")
                    if st.button("Authorize & Activate Candidate Policy", type="primary"):
                        new_pol = Policy(
                            id=candidate["id"],
                            name=candidate["name"],
                            rule_type=PolicyRuleType(candidate["rule_type"]),
                            severity=PolicySeverity(candidate["severity"]),
                            parameters=candidate["parameters"],
                            description=candidate["description"],
                            is_mandatory=False,
                            is_active=True,
                            created_by="ai_assisted_admin",
                        )
                        policy_service.save_policy(new_pol, actor="policy_admin")
                        st.success(f"Policy `{new_pol.id}` activated successfully!")
                        del st.session_state["candidate_policy"]
                        st.rerun()
                else:
                    st.error(f"Validation Errors: {'; '.join(val['errors'])}")

    # TAB 3: MANUAL POLICY BUILDER
    with tab_manual:
        st.subheader("Add Custom Financial Rule")
        with st.form("manual_policy_form_v2"):
            p_name = st.text_input("Policy Rule Name", value="Custom Vendor Ceiling")
            p_rule_str = st.selectbox("Rule Type", [r.value for r in PolicyRuleType])
            p_sev_str = st.selectbox("Severity Level", [s.value for s in PolicySeverity], index=1)
            p_thresh = st.number_input("Threshold Amount (₹)", min_value=1000.0, value=75000.0, step=5000.0)
            p_desc = st.text_area("Description", value="Requires manager approval when transaction exceeds custom threshold.")

            if st.form_submit_button("Save & Activate Policy", type="primary"):
                try:
                    import uuid
                    new_id = f"POL-CUST-{uuid.uuid4().hex[:4].upper()}"
                    custom_pol = Policy(
                        id=new_id,
                        name=p_name,
                        rule_type=PolicyRuleType(p_rule_str),
                        severity=PolicySeverity(p_sev_str),
                        parameters={"threshold_amount": float(p_thresh)},
                        description=p_desc,
                        is_mandatory=False,
                        is_active=True,
                        created_by="policy_admin",
                    )
                    policy_service.save_policy(custom_pol, actor="policy_admin")
                    st.success(f"Custom Policy `{new_id}` created and activated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to create policy: {str(e)}")
