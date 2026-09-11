import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
from google import genai
from google.genai import types


def get_gemini_client():
    try:
        api_key = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
    except Exception:
        api_key = ""

    if not api_key:
        return None

    return genai.Client(api_key=api_key)


def ask_gemini_marine_copilot(prompt, role):
    client = get_gemini_client()

    if client is None:
        return (
            "Gemini AI belum aktif. "
            "Silakan konfigurasi GEMINI_API_KEY di Streamlit Secrets."
        )

    system_instruction = f"""
You are the MARINE OPERATIONS CO-PILOT for a marine fleet operations company.

Operational role: {role}
Fleet size: 21 vessels.

Your responsibilities include:
- Fleet operations
- Voyage operations
- HSSE / DPA
- PMS / Maintenance
- Defects
- Certificates
- Crew
- Bunker
- Cargo
- Audit & Findings
- Action Tracker
- Operational risk

Rules:
1. Be concise, professional and operational.
2. Give evidence-based recommendations.
3. NEVER invent vessel status, voyage, defect, certificate, PMS, HSSE,
   crew, bunker, cargo or other operational data.
4. If required data is unavailable, clearly state: DATA BELUM TERSEDIA.
5. For safety-critical matters, recommend appropriate escalation.
6. Prioritize safety, compliance and operational continuity.
"""

    last_error = None

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.7-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                    max_output_tokens=1200,
                ),
            )

            return response.text

        except Exception as e:
            last_error = e
            error_text = str(e)

            # Gemini quota habis
            if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
                return (
                    "Gemini sedang mencapai batas quota penggunaan. "
                    "Data berhasil dimuat, tetapi analisis AI belum dapat "
                    "dijalankan. Silakan coba lagi setelah quota tersedia."
                )

            # Gemini sedang high demand
            if "503" in error_text or "UNAVAILABLE" in error_text:
                if attempt < 2:
                    time.sleep(3 * (attempt + 1))
                    continue

                return (
                    "Gemini sedang mengalami high demand. "
                    "Silakan klik ANALYZE lagi beberapa saat kemudian."
                )

            raise

    if last_error is not None:
        raise last_error
# ============================================================
# MARINE OPERATIONS INTELLIGENCE CENTRE
# ============================================================

st.set_page_config(
    page_title="Marine Operations Intelligence Centre",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CONFIGURATION
# ============================================================

FLEET = [
    "ASL MANTRUS",
    "ASL MULIA",
    "ASL SENTOSA",
    "ASL VICTORY",
    "ASL INTAN",
    "ASL GEMINI",
    "ASL BEAVER",
    "ASL CRESST",
    "ASL CALYPSO",
    "ASL PHOENIX",
    "ASL MARINE 8",
    "AST LEGEND",
    "TERAS HYDRA",
    "AST MAJU",
    "KARYA ABADI 8",
    "NUSANTARA ABADI 1",
    "CAPITOL T2002",
    "CAPITOL T2001",
    "TB1000-06",
    "TB1000-07",
    "WHALE 3",
]

ROLES = [
    "Marine Superintendent",
    "DPA",
    "Manager Operation Marine",
]

# ============================================================
# SAMPLE OPERATIONAL DATABASE
# ============================================================

VESSEL_DATA = []

for vessel in FLEET:
    VESSEL_DATA.append(
        {
            "Vessel": vessel,
            "Status": "Active",
            "Location": "Data belum tersedia",
            "Voyage": "Data belum tersedia",
            "Defect": "Tidak ada data",
            "Certificate": "Tidak ada data",
            "PMS": "Tidak ada data",
            "Risk": "Belum dinilai",
        }
    )

VESSELS_DF = pd.DataFrame(VESSEL_DATA)

# ============================================================
# SESSION STATE
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "role" not in st.session_state:
    st.session_state.role = "Marine Superintendent"

if "ai_history" not in st.session_state:
    st.session_state.ai_history = []

# ============================================================
# LOGIN
# ============================================================

if not st.session_state.logged_in:

    st.title("⚓ MARINE OPERATIONS INTELLIGENCE CENTRE")

    st.subheader("Secure Operations Portal")

    st.markdown(
        """
        **Fleet Intelligence • HSSE • PMS • Voyage • Risk • AI Copilot**
        
        Silakan login untuk masuk ke Marine Operations Intelligence Centre.
        """
    )

    with st.form("login_form"):

        username = st.text_input("Username")

        password = st.text_input(
            "Password",
            type="password"
        )

        role = st.selectbox(
            "Operational Role",
            ROLES
        )

        submitted = st.form_submit_button(
            "LOGIN"
        )

        if submitted:
            # LOGIN menggunakan Streamlit Secrets
            admin_username = st.secrets.get("ADMIN_USERNAME", "admin")
            admin_password = st.secrets.get("ADMIN_PASSWORD", "")

            if username.strip() == admin_username and password == admin_password:
                st.session_state.logged_in = True
                st.session_state.role = role
                st.rerun()
            else:
                st.error("Username atau password tidak benar.")

        st.stop()

    

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        # ⚓ MARINE OPERATIONS
        ## INTELLIGENCE CENTRE
        """
    )

    st.caption(
        "Fleet Intelligence & Marine Operations Command"
    )

    st.divider()

    role = st.selectbox(
        "Operational Role",
        ROLES,
        index=ROLES.index(st.session_state.role)
    )

    st.session_state.role = role

    st.divider()

    menu = st.radio(
        "MENU",
        [
            "Dashboard",
            "Fleet 21",
            "Crew 200",
            "Voyage Operations",
            "HSSE / DPA",
            "PMS / Maintenance",
            "Defects",
            "Certificates",
            "Bunker",
            "Cargo",
            "Audit & Findings",
            "Action Tracker",
            "AI Marine Copilot",
            "Executive Reports",
            "WhatsApp Operations",
            "System",
        ]
    )

    st.divider()

    st.metric(
        "Fleet",
        "21"
    )

    st.metric(
        "Crew Master",
        "200"
    )

    st.caption(
        f"Role: {st.session_state.role}"
    )

    if st.button("Logout"):

        st.session_state.logged_in = False

        st.rerun()

# ============================================================
# HEADER
# ============================================================

st.title(
    "⚓ MARINE OPERATIONS INTELLIGENCE CENTRE"
)

st.caption(
    f"Operational Intelligence Platform • {st.session_state.role}"
)

st.divider()

# ============================================================
# DASHBOARD
# ============================================================

if menu == "Dashboard":

    st.header("📊 Operations Command Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Fleet",
            "21 Vessels"
        )

    with col2:
        st.metric(
            "Crew",
            "200"
        )

    with col3:
        st.metric(
            "Active Vessels",
            "21"
        )

    with col4:
        st.metric(
            "Critical Alerts",
            "0"
        )

    st.divider()

    st.subheader(
        "Fleet Operational Overview"
    )

    dashboard_df = pd.DataFrame(
        {
            "Indicator": [
                "Fleet",
                "Active Vessel",
                "Voyage Records",
                "Open Defects",
                "Certificate Records",
                "PMS Records",
                "HSSE Findings",
                "Pending Actions",
            ],
            "Value": [
                21,
                21,
                0,
                0,
                0,
                0,
                0,
                0,
            ],
            "Status": [
                "ACTIVE",
                "ACTIVE",
                "DATA GAP",
                "DATA GAP",
                "DATA GAP",
                "DATA GAP",
                "DATA GAP",
                "DATA GAP",
            ],
        }
    )

    st.dataframe(
        dashboard_df,
        use_container_width=True,
        hide_index=True
    )

    st.info(
        """
        Intelligence Centre saat ini menggunakan database awal.
        Data operasional nyata akan dimasukkan secara bertahap
        tanpa mengganggu aplikasi MARINE OPERATION VESSEL PRO.
        """
    )

# ============================================================
# FLEET
# ============================================================

elif menu == "Fleet 21":

    st.header("🚢 Fleet 21")

    st.write(
        "Daftar armada yang menjadi basis Intelligence Centre."
    )

    st.dataframe(
        VESSELS_DF,
        use_container_width=True,
        hide_index=True
    )

    selected_vessel = st.selectbox(
        "Pilih kapal",
        FLEET
    )

    vessel = VESSELS_DF[
        VESSELS_DF["Vessel"] == selected_vessel
    ].iloc[0]

    st.subheader(
        f"Vessel Intelligence — {selected_vessel}"
    )

    a, b, c, d = st.columns(4)

    with a:
        st.metric(
            "Status",
            vessel["Status"]
        )

    with b:
        st.metric(
            "Voyage",
            "N/A"
        )

    with c:
        st.metric(
            "Defect",
            "N/A"
        )

    with d:
        st.metric(
            "Risk",
            "N/A"
        )

# ============================================================
# CREW
# ============================================================

elif menu == "Crew 200":

    st.header("👨‍✈️ Crew Intelligence")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Total Crew", "200")

    with c2:
        st.metric("Officers", "Data Gap")

    with c3:
        st.metric("Ratings", "Data Gap")

    with c4:
        st.metric("Expiring Certificates", "Data Gap")

    st.info(
        "Modul crew akan dikembangkan dengan matrix competence, "
        "certificate validity, rank, vessel assignment dan fatigue monitoring."
    )

# ============================================================
# VOYAGE
# ============================================================

elif menu == "Voyage Operations":

    st.header("🧭 Voyage Operations Intelligence")

    st.warning(
        "Belum ada voyage record pada database Intelligence Centre."
    )

    voyage_df = pd.DataFrame(
        columns=[
            "Vessel",
            "Voyage",
            "Origin",
            "Destination",
            "ETD",
            "ETA",
            "Status",
        ]
    )

    st.dataframe(
        voyage_df,
        use_container_width=True,
        hide_index=True
    )

# ============================================================
# HSSE / DPA
# ============================================================

elif menu == "HSSE / DPA":

    st.header("🛡️ HSSE / DPA Intelligence")

    st.caption(
        "HSSE Intelligence menganalisis data Incident, Near Miss, "
        "Finding dan Safety Observation yang tersedia."
    )

    uploaded_hsse = st.file_uploader(
        "Upload HSSE / DPA Data (CSV)",
        type=["csv"],
        key="hsse_upload",
    )

    if uploaded_hsse is None:

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("Incidents", "0")

        with c2:
            st.metric("Near Miss", "0")

        with c3:
            st.metric("Open Findings", "0")

        st.warning(
            "DATA BELUM TERSEDIA — belum ada HSSE / DPA data."
        )

        st.info(
            """
            Format CSV yang disarankan:

            vessel,event_date,event_type,severity,status,remarks

            Contoh event_type:
            Incident / Near Miss / Finding / Safety Observation

            Contoh severity:
            Critical / High / Medium / Low

            Contoh status:
            Open / Closed / Under Investigation
            """
        )

    else:

        try:
            hsse_df = pd.read_csv(uploaded_hsse)

        except Exception as e:

            st.error(
                f"Gagal membaca file HSSE / CSV: {e}"
            )

        else:

            st.metric(
                "HSSE Records",
                len(hsse_df)
            )

            st.subheader("HSSE / DPA Records")

            st.dataframe(
                hsse_df,
                use_container_width=True
            )

            st.subheader("HSSE Intelligence")

            if st.button(
                "ANALYZE HSSE",
                type="primary",
                key="analyze_hsse",
            ):

                hsse_context = json.dumps(
                    hsse_df.to_dict(
                        orient="records"
                    ),
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )

                hsse_prompt = f"""
USER REQUEST:
Analyze the supplied HSSE / DPA data.

HSSE / DPA DATA:
{hsse_context}

HSSE INTELLIGENCE RULES:

- Analyze ONLY the supplied HSSE data.
- NEVER invent incidents, near misses, findings,
  dates, severity, vessel condition or corrective actions.
- If required information is missing, state:
  DATA BELUM TERSEDIA.
- Identify critical safety risks only when the supplied
  data supports the assessment.
- Identify open findings only from the supplied status.
- Prioritize safety and regulatory compliance.
- Clearly separate:

FACTS

DATA GAPS

HSSE RISK

PRIORITY ACTIONS

ESCALATION REQUIRED
"""

                try:

                    with st.spinner(
                        "Gemini sedang menganalisis HSSE..."
                    ):

                        hsse_answer = ask_gemini_marine_copilot(
                            hsse_prompt,
                            st.session_state.get(
                                "role",
                                "Marine Superintendent",
                            ),
                        )

                    st.markdown(
                        "### HSSE / DPA Intelligence Assessment"
                    )

                    st.markdown(hsse_answer)

                except Exception as e:

                    if (
                        "503" in str(e)
                        or "UNAVAILABLE" in str(e)
                    ):
                        st.warning(
                            "Data HSSE berhasil dimuat. "
                            "Gemini sedang mengalami high demand. "
                            "Silakan klik ANALYZE HSSE lagi."
                        )
                    else:
                        st.error(
                            f"Gagal menganalisis HSSE: {e}"
                        )

# ============================================================
# PMS
# ============================================================
elif menu == "PMS / Maintenance":

    st.header("🔧 PMS / Maintenance Intelligence")

    st.caption(
        "PMS Intelligence menganalisis data maintenance yang tersedia. "
        "Tidak ada data maintenance yang akan dibuat atau diasumsikan oleh sistem."
    )

    uploaded_pms = st.file_uploader(
        "Upload PMS / Maintenance Data (CSV)",
        type=["csv"],
        key="pms_upload",
    )

    if uploaded_pms is None:

        st.metric("Maintenance Records", "0")

        st.warning(
            "DATA BELUM TERSEDIA — belum ada PMS / Maintenance data."
        )

        st.info(
            """
            Format CSV yang disarankan:

            vessel,maintenance_task,due_date,status,priority,remarks

            Contoh nilai status:
            Planned / Due / Overdue / Completed

            Contoh priority:
            Critical / High / Medium / Low
            """
        )

    else:

        try:
            pms_df = pd.read_csv(uploaded_pms)

            st.metric(
                "Maintenance Records",
                len(pms_df)
            )

            st.subheader("PMS / Maintenance Records")
            st.dataframe(
                pms_df,
                use_container_width=True
            )

            st.subheader("PMS Intelligence")

            if st.button(
                "ANALYZE PMS",
                type="primary",
                key="analyze_pms",
            ):

                pms_context = json.dumps(
                    pms_df.to_dict(
                        orient="records"
                    ),
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )

                pms_prompt = f"""
USER REQUEST:
Analyze the supplied PMS / Maintenance data.

PMS / MAINTENANCE DATA:
{pms_context}

PMS INTELLIGENCE RULES:

IMPORTANT OUTPUT REQUIREMENT:
Your response MUST contain ALL FOUR sections below.
Do NOT stop after FACTS.
Do NOT omit any section, even if information is missing.

1. FACTS
- Summarize only facts directly supported by the supplied PMS data.
- Include total maintenance tasks.
- Include status breakdown.
- Identify overdue tasks and their vessels when supported by the data.

2. DATA GAPS
- State important PMS information that is missing from the supplied data.
- Consider missing running hours, maintenance intervals, completion evidence,
  responsible person, work order status, technical findings, and verification.
- If a particular item is not required, say "Tidak ada gap material yang teridentifikasi."
- NEVER invent missing information.

3. MAINTENANCE RISK
- Assess maintenance risk using ONLY the supplied status, priority,
  due date and remarks.
- Identify vessels/tasks with the highest maintenance risk.
- Critical + Overdue items must receive the highest attention.
- High + Overdue or High + Due items must be highlighted.
- NEVER invent technical condition or equipment failure.

4. PRIORITY ACTIONS
- Give practical actions based ONLY on the supplied PMS data.
- Prioritize overdue and critical maintenance first.
- Identify the vessel and maintenance task whenever supported.
- Recommend verification, completion, escalation or follow-up only when justified.
- NEVER invent work orders, completion dates or technical findings.

FINAL OUTPUT REQUIREMENT:

You MUST complete BOTH sections before ending the response.

1. FACTS
2. DATA GAPS

Do NOT add Maintenance Risk or Priority Actions.

Section 1 MUST contain facts directly supported by the supplied PMS data.

Section 2 MUST contain important PMS information that is missing from the supplied data.

If information is missing, write "DATA BELUM TERSEDIA."

The response is NOT COMPLETE until sections 1 and 2 are displayed.
IMPORTANT:
Write section 2 immediately after section 1.
Do not end the response after section 1.
"""

                with st.spinner(
                    "Gemini sedang menganalisis PMS..."
                ):

                    pms_answer = ask_gemini_marine_copilot(
                        pms_prompt,
                        st.session_state.get(
                            "role",
                            "Marine Superintendent",
                        ),
                    )

                st.markdown(
                    "### PMS Maintenance Intelligence Analysis"
                )

                st.markdown(pms_answer)

                st.markdown("### 2. DATA GAPS")

                required_pms_columns = [
                    "vessel",
                    "maintenance_task",
                    "due_date",
                    "status",
                    "priority",
                    "remarks",
                ]

                missing_columns = [
                    col for col in required_pms_columns
                    if col not in pms_df.columns
                ]

                if missing_columns:
                    st.warning(
                        "DATA BELUM TERSEDIA — kolom PMS berikut belum tersedia: "
                        + ", ".join(missing_columns)
                    )
                else:
                    st.markdown(
                        "- Running Hours & Maintenance Intervals: "
                        "DATA BELUM TERSEDIA."
                    )
                    st.markdown(
                        "- Work Order / Completion Date: DATA BELUM TERSEDIA."
                    )
                    st.markdown(
                        "- Technical Findings / Maintenance Condition: "
                        "DATA BELUM TERSEDIA."
                    )

        except Exception as e:
            st.error(f"Gagal membaca PMS data: {e}")


# ============================================================
# DEFECTS
# ============================================================

elif menu == "Defects":

    st.header("⚠️ Defect Intelligence")

    st.caption(
        "Defect Intelligence menganalisis defect yang tersedia. "
        "Tidak ada defect yang akan dibuat atau diasumsikan oleh sistem."
    )

    uploaded_defects = st.file_uploader(
        "Upload Defect Data (CSV)",
        type=["csv"],
        key="defects_upload",
    )

    if uploaded_defects is None:

        st.metric("Defect Records", "0")

        st.warning(
            "DATA BELUM TERSEDIA — belum ada defect data."
        )

        st.info(
            """
            Format CSV yang disarankan:

            vessel,defect,severity,reported,due_date,status,responsible

            Severity:
            Critical / High / Medium / Low

            Status:
            Open / In Progress / Closed
            """
        )

    else:

        try:
            defect_df = pd.read_csv(uploaded_defects)

        except Exception as e:

            st.error(
                f"Gagal membaca file Defects/CSV: {e}"
            )

        else:

            st.metric(
                "Defect Records",
                len(defect_df)
            )

            st.subheader("Defect Records")

            st.dataframe(
                defect_df,
                use_container_width=True,
                hide_index=True
            )

            st.subheader("Defect Intelligence")

            required_columns = [
                "vessel",
                "defect",
                "severity",
                "reported",
                "due_date",
                "status",
                "responsible",
            ]

            missing_columns = [
                col for col in required_columns
                if col not in defect_df.columns
            ]

            if missing_columns:

                st.error(
                    "Kolom wajib belum lengkap: "
                    + ", ".join(missing_columns)
                )

            else:

                analysis_df = defect_df.copy()

                analysis_df["due_date"] = pd.to_datetime(
                    analysis_df["due_date"],
                    errors="coerce"
                )

                analysis_df["status"] = (
                    analysis_df["status"]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                )

                analysis_df["severity"] = (
                    analysis_df["severity"]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                )

                today = pd.Timestamp(datetime.now().date())

                overdue_df = analysis_df[
                    (analysis_df["due_date"].notna())
                    & (analysis_df["due_date"] < today)
                    & (analysis_df["status"] != "closed")
                ]

                critical_df = analysis_df[
                    (analysis_df["severity"] == "critical")
                    & (analysis_df["status"] != "closed")
                ]

                high_df = analysis_df[
                    (analysis_df["severity"] == "high")
                    & (analysis_df["status"] != "closed")
                ]

                open_df = analysis_df[
                    analysis_df["status"].isin(
                        ["open", "in progress"]
                    )
                ]

                st.markdown("### Defect Summary")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Total Defects",
                        len(analysis_df)
                    )

                with col2:
                    st.metric(
                        "Open / In Progress",
                        len(open_df)
                    )

                with col3:
                    st.metric(
                        "Overdue",
                        len(overdue_df)
                    )

                with col4:
                    st.metric(
                        "Critical",
                        len(critical_df)
                    )

                st.markdown("### Critical Defects")

                if critical_df.empty:

                    st.info(
                        "Tidak ada Critical Defect aktif "
                        "berdasarkan data yang diberikan."
                    )

                else:

                    st.dataframe(
                        critical_df[
                            [
                                "vessel",
                                "defect",
                                "severity",
                                "due_date",
                                "status",
                                "responsible",
                            ]
                        ],
                        use_container_width=True,
                        hide_index=True
                    )

                st.markdown("### Overdue Defects")

                if overdue_df.empty:

                    st.info(
                        "Tidak ada Overdue Defect aktif "
                        "berdasarkan data yang diberikan."
                    )

                else:

                    st.dataframe(
                        overdue_df[
                            [
                                "vessel",
                                "defect",
                                "severity",
                                "due_date",
                                "status",
                                "responsible",
                            ]
                        ],
                        use_container_width=True,
                        hide_index=True
                    )

                st.markdown("### High Severity Defects")

                if high_df.empty:

                    st.info(
                        "Tidak ada High Severity Defect aktif."
                    )

                else:

                    st.dataframe(
                        high_df[
                            [
                                "vessel",
                                "defect",
                                "severity",
                                "due_date",
                                "status",
                                "responsible",
                            ]
                        ],
                        use_container_width=True,
                        hide_index=True
                    )

                st.markdown("### Defect Intelligence Assessment")

                st.markdown(
                    f"""
**FACTS**

- Total defect records: **{len(analysis_df)}**
- Open / In Progress: **{len(open_df)}**
- Overdue active defects: **{len(overdue_df)}**
- Critical active defects: **{len(critical_df)}**
- High severity active defects: **{len(high_df)}**

**DATA GAPS**

- Jika informasi teknis defect tidak tersedia: **DATA BELUM TERSEDIA.**
- Jika root cause tidak tersedia: **DATA BELUM TERSEDIA.**
- Jika corrective action tidak tersedia: **DATA BELUM TERSEDIA.**
- Jika completion evidence tidak tersedia: **DATA BELUM TERSEDIA.**
"""
                )

# =========================================================
# CERTIFICATES
# =========================================================

# ============================================================
# CERTIFICATES
# ============================================================

elif menu == "Certificates":

    st.header("📜 Certificate Intelligence")

    st.caption(
        "Certificate Intelligence menganalisis expiry, statutory, "
        "class, flag dan operational certificates berdasarkan data yang tersedia."
    )

    uploaded_certificates = st.file_uploader(
        "Upload Certificate Data (CSV)",
        type=["csv"],
        key="certificates_upload",
    )

    if uploaded_certificates is None:

        st.metric("Certificate Records", "0")

        st.warning(
            "DATA BELUM TERSEDIA — belum ada certificate data."
        )

        st.info(
            """
            Format CSV yang disarankan:

            vessel,certificate,certificate_type,issue_date,expiry_date,status,remarks

            Contoh certificate_type:
            Statutory / Class / Flag / Operational

            Contoh status:
            Valid / Expired / Suspended
            """
        )

    else:

        try:
            certificates_df = pd.read_csv(
                uploaded_certificates
            )

            certificates_df["expiry_date"] = pd.to_datetime(
                certificates_df["expiry_date"],
                errors="coerce"
            )

            today = pd.Timestamp.today().normalize()

            certificates_df["days_to_expiry"] = (
                certificates_df["expiry_date"] - today
            ).dt.days

            expired_df = certificates_df[
                certificates_df["days_to_expiry"] < 0
            ]

            expiring_df = certificates_df[
                (certificates_df["days_to_expiry"] >= 0)
                & (certificates_df["days_to_expiry"] <= 30)
            ]

            st.metric(
                "Certificate Records",
                len(certificates_df)
            )

            st.subheader("Certificate Records")

            st.dataframe(
                certificates_df,
                use_container_width=True
            )

            st.subheader("Certificate Intelligence")

            c1, c2, c3 = st.columns(3)

            with c1:
                st.metric(
                    "Expired",
                    len(expired_df)
                )

            with c2:
                st.metric(
                    "Expiring ≤ 30 Days",
                    len(expiring_df)
                )

            with c3:
                st.metric(
                    "Valid / Other",
                    len(certificates_df)
                    - len(expired_df)
                    - len(expiring_df)
                )

            if len(expired_df) > 0:

                st.subheader("🔴 Expired Certificates")

                st.dataframe(
                    expired_df,
                    use_container_width=True
                )

            if len(expiring_df) > 0:

                st.subheader("🟠 Certificates Expiring ≤ 30 Days")

                st.dataframe(
                    expiring_df,
                    use_container_width=True
                )

            if st.button(
                "ANALYZE CERTIFICATES",
                type="primary",
                key="analyze_certificates",
            ):

                certificate_context = json.dumps(
                    certificates_df.to_dict(
                        orient="records"
                    ),
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )

                certificate_prompt = f"""
USER REQUEST:
Analyze the supplied vessel certificate data.

CERTIFICATE DATA:
{certificate_context}

CERTIFICATE INTELLIGENCE RULES:
- Analyze ONLY the supplied certificate data.
- NEVER invent certificate records.
- NEVER invent expiry dates.
- NEVER invent statutory, class, flag or operational status.
- Identify expired certificates only from the supplied expiry_date.
- Identify certificates expiring within 30 days only from the supplied data.
- If required information is missing, state:
  DATA BELUM TERSEDIA.
- Clearly separate:
  FACTS
  EXPIRY RISK
  COMPLIANCE RISK
  DATA GAPS
  PRIORITY ACTIONS
- Safety and statutory compliance issues must be escalated appropriately.
"""

                with st.spinner(
                    "Gemini sedang menganalisis certificates..."
                ):

                    certificate_answer = ask_gemini_marine_copilot(
                        certificate_prompt,
                        st.session_state.get(
                            "role",
                            "Marine Superintendent",
                        ),
                    )

                st.markdown(
                    "### Certificate Intelligence Assessment"
                )

                st.markdown(
                    certificate_answer
                )

        except Exception as e:

            st.error(
                f"Gagal membaca Certificate data: {e}"
            )

# ============================================================
# BUNKER
# ============================================================

elif menu == "Bunker":

    st.header("⛽ Bunker Intelligence")

    st.caption(
        "Bunker Intelligence menganalisis data bunker yang tersedia. "
        "Tidak ada konsumsi, quantity, ROB atau alert yang akan dibuat "
        "atau diasumsikan oleh sistem."
    )

    uploaded_bunker = st.file_uploader(
        "Upload Bunker Data (CSV)",
        type=["csv"],
        key="bunker_upload",
    )

    if uploaded_bunker is None:

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("Vessels", "21")

        with c2:
            st.metric("Bunker Reports", "0")

        with c3:
            st.metric("Consumption Alerts", "0")

        st.warning(
            "DATA BELUM TERSEDIA — belum ada bunker data."
        )

        st.info(
            """
            Format CSV yang disarankan:

            vessel,date,fuel_type,quantity_mt,rob_mt,consumption_mt_day,remarks

            Contoh fuel_type:
            MGO / HFO / VLSFO

            Data harus berasal dari laporan bunker aktual.
            """
        )

    else:

        try:
            bunker_df = pd.read_csv(uploaded_bunker)

        except Exception as e:

            st.error(
                f"Gagal membaca file Bunker/CSV: {e}"
            )

        else:

            st.metric(
                "Bunker Reports",
                len(bunker_df)
            )

            st.subheader("Bunker Records")

            st.dataframe(
                bunker_df,
                use_container_width=True
            )

            st.subheader("Bunker Intelligence")

            alert_count = 0

            if "remarks" in bunker_df.columns:

                alert_count = bunker_df["remarks"].astype(
                    str
                ).str.contains(
                    "alert|low|high consumption|abnormal",
                    case=False,
                    na=False
                ).sum()

            elif "consumption_mt_day" in bunker_df.columns:

                values = pd.to_numeric(
                    bunker_df["consumption_mt_day"],
                    errors="coerce"
                )

                if values.notna().any():

                    average_consumption = values.mean()

                    alert_count = (
                        values >
                        average_consumption * 1.20
                    ).sum()

            c1, c2 = st.columns(2)

            with c1:
                st.metric(
                    "Bunker Reports",
                    len(bunker_df)
                )

            with c2:
                st.metric(
                    "Consumption Alerts",
                    int(alert_count)
                )

            if alert_count > 0:

                st.warning(
                    f"⚠️ {int(alert_count)} bunker record "
                    "memerlukan review."
                )

            if st.button(
                "ANALYZE BUNKER",
                type="primary",
                key="analyze_bunker",
            ):

                bunker_context = json.dumps(
                    bunker_df.to_dict(
                        orient="records"
                    ),
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )

                bunker_prompt = f"""
USER REQUEST:
Analyze the supplied Bunker data for marine fleet operations.

BUNKER DATA:
{bunker_context}

BUNKER INTELLIGENCE RULES:

- Analyze ONLY the supplied bunker data.
- NEVER invent fuel quantity.
- NEVER invent ROB.
- NEVER invent fuel consumption.
- NEVER invent bunker price.
- NEVER invent bunker delivery.
- NEVER invent vessel operating condition.
- NEVER invent fuel shortage.
- Identify abnormal consumption ONLY when the supplied
  data supports the assessment.
- Identify low ROB ONLY when the supplied data explicitly
  contains sufficient ROB information.
- If required information is missing, state:
  DATA BELUM TERSEDIA.

Clearly separate:

FACTS
DATA GAPS
BUNKER RISK
CONSUMPTION ALERTS
PRIORITY ACTIONS

Prioritize:
1. Safety
2. Operational continuity
3. Fuel availability
4. Abnormal consumption
5. Data quality

Do not make assumptions beyond the supplied data.
"""

                try:

                    with st.spinner(
                        "Gemini sedang menganalisis Bunker..."
                    ):

                        bunker_answer = (
                            ask_gemini_marine_copilot(
                                bunker_prompt,
                                st.session_state.get(
                                    "role",
                                    "Marine Superintendent",
                                ),
                            )
                        )

                    st.markdown(
                        "### Bunker Intelligence Assessment"
                    )

                    st.markdown(
                        bunker_answer
                    )

                except Exception as e:

                    if (
                        "503" in str(e)
                        or "UNAVAILABLE" in str(e)
                    ):

                        st.warning(
                            "Data Bunker berhasil dimuat, "
                            "tetapi Gemini sedang mengalami "
                            "high demand. Silakan klik "
                            "ANALYZE BUNKER lagi."
                        )

                    else:

                        st.error(
                            f"Gagal melakukan analisis Bunker: {e}"
                        )

# ============================================================
# CARGO
# ============================================================

# ============================================================
# CARGO
# ============================================================

elif menu == "Cargo":

    st.header("📦 Cargo Operations")

    uploaded_cargo = st.file_uploader(
        "Upload Cargo Data (CSV)",
        type=["csv"],
        key="cargo_upload",
    )

    if uploaded_cargo is None:

        cargo_df = pd.DataFrame(
            columns=[
                "vessel",
                "cargo_date",
                "cargo_type",
                "quantity_mt",
                "origin",
                "destination",
                "status",
                "remarks",
            ]
        )

        st.info(
            "Upload Cargo Data (CSV) untuk menjalankan "
            "Cargo Intelligence."
        )

    else:

        try:
            cargo_df = pd.read_csv(uploaded_cargo)

        except Exception as e:
            st.error(f"Gagal membaca file Cargo/CSV: {e}")
            cargo_df = pd.DataFrame()

        if not cargo_df.empty:

            st.subheader("📋 Cargo Records")

            st.dataframe(
                cargo_df,
                use_container_width=True,
                hide_index=True,
            )

            # ====================================================
            # CARGO METRICS
            # ====================================================

            total_cargo = len(cargo_df)

            delayed_cargo = 0

            if "status" in cargo_df.columns:
                delayed_cargo = int(
                    cargo_df["status"]
                    .astype(str)
                    .str.contains(
                        "delayed|delay",
                        case=False,
                        na=False,
                    )
                    .sum()
                )

            attention_cargo = 0

            if "remarks" in cargo_df.columns:
                attention_cargo = int(
                    cargo_df["remarks"]
                    .astype(str)
                    .str.contains(
                        "delay|delayed|shortage|damage|risk|abnormal",
                        case=False,
                        na=False,
                    )
                    .sum()
                )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Cargo Records",
                    total_cargo,
                )

            with col2:
                st.metric(
                    "Delayed Cargo",
                    delayed_cargo,
                )

            with col3:
                st.metric(
                    "Attention Required",
                    attention_cargo,
                )

            # ====================================================
            # CARGO INTELLIGENCE
            # ====================================================

            if st.button(
                "ANALYZE CARGO",
                type="primary",
                key="analyze_cargo",
            ):

                cargo_context = cargo_df.to_csv(
                    index=False
                )

                cargo_prompt = f"""
USER REQUEST:
Analyze supplied Cargo data for marine fleet operations.

CARGO DATA:
{cargo_context}

CARGO INTELLIGENCE RULES:
- Analyze ONLY supplied cargo data.
- NEVER invent cargo quantity, cargo type, origin,
  destination, status, delay, damage, shortage,
  vessel condition, ETA or voyage linkage.
- Identify delay or cargo risk only when explicitly
  supported by supplied data.
- If required information is missing, state:
  DATA BELUM TERSEDIA.
- Clearly separate:

FACTS
DATA GAPS
CARGO RISK
PRIORITY ACTIONS

- Prioritize safety, cargo integrity,
  operational continuity and compliance.
- Do not make assumptions beyond supplied data.
"""

                try:

                    with st.spinner(
                        "Gemini sedang menganalisis Cargo..."
                    ):

                        cargo_answer = ask_gemini_marine_copilot(
                            cargo_prompt,
                            st.session_state.get(
                                "role",
                                "Marine Superintendent",
                            ),
                        )

                    st.markdown(
                        "### Cargo Intelligence Assessment"
                    )

                    st.markdown(cargo_answer)

                except Exception as e:

                    if (
                        "503" in str(e)
                        or "UNAVAILABLE" in str(e)
                    ):

                        st.warning(
                            "Data Cargo berhasil dimuat, "
                            "tetapi Gemini sedang mengalami "
                            "high demand. Silakan klik "
                            "ANALYZE CARGO lagi."
                        )

                    else:

                        st.error(
                            f"Gagal melakukan analisis Cargo: {e}"
                        )

# ============================================================
# ACTION TRACKER
# ============================================================

elif menu == "Action Tracker":

    st.header("✅ Action Tracker")

    action_df = pd.DataFrame(
        columns=[
            "Action ID",
            "Description",
            "Priority",
            "Responsible",
            "Due Date",
            "Status",
        ]
    )

    st.dataframe(
        action_df,
        use_container_width=True,
        hide_index=True
    )

# ============================================================
# AI MARINE COPILOT
# ============================================================
elif menu == "AI Marine Copilot":

    st.header("🤖 AI Marine Operations Copilot")

    st.caption(
        f"Decision support untuk {st.session_state.role}"
    )

    st.subheader("Fleet Intelligence")

    st.info(
        """
AI Copilot sekarang terhubung dengan data Fleet 21.
AI hanya boleh menggunakan data yang tersedia dan tidak boleh
mengarang status kapal, voyage, defect, PMS, certificate,
HSSE atau risk.
"""
    )

    prompt = st.text_area(
        "Pertanyaan / Instruksi",
        placeholder=(
            "Contoh: Buatkan Fleet Risk Assessment untuk 21 kapal "
            "dan tunjukkan data gap yang harus segera dilengkapi."
        ),
        height=150,
    )

    if st.button("ASK AI", type="primary"):

        if not prompt.strip():

            st.warning(
                "Masukkan pertanyaan terlebih dahulu."
            )

        else:

            try:

                # ==========================================
                # FLEET 21 REAL DATA
                # ==========================================

                if (
                    "VESSEL_DF" in globals()
                    and hasattr(VESSEL_DF, "to_dict")
                ):

                    fleet_context = json.dumps(
                        VESSEL_DF.to_dict(
                            orient="records"
                        ),
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                    )

                else:

                    fleet_context = json.dumps(
                        VESSEL_DATA,
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                    )

                # ==========================================
                # FLEET INTELLIGENCE PROMPT
                # ==========================================

                fleet_prompt = f"""
USER REQUEST:
{prompt.strip()}

FLEET 21 OPERATIONAL DATA:
{fleet_context}

FLEET INTELLIGENCE RULES:

1. Analyze ONLY the supplied Fleet 21 data.

2. NEVER invent:
- vessel status
- vessel position
- voyage
- defect
- PMS condition
- certificate condition
- HSSE finding
- crew condition
- bunker data
- cargo data
- operational risk

3. If information is missing, unavailable, or marked
"Data belum tersedia", "Tidak ada data", or
"Belum dinilai", state clearly:

DATA BELUM TERSEDIA.

4. Do not create a risk ranking when the supplied data
does not contain enough factual risk information.

5. Separate the answer into:

FLEET SUMMARY
RISK ASSESSMENT
TOP PRIORITIES
DATA GAPS
RECOMMENDED ACTIONS

6. For safety-critical matters, recommend escalation
to the appropriate responsible person.

7. Be concise and operational.

8. Never present assumptions as facts.
"""

                with st.spinner(
                    "Gemini sedang menganalisis Fleet 21..."
                ):

                    answer = ask_gemini_marine_copilot(
                        fleet_prompt,
                        st.session_state.role,
                    )

                st.markdown(
                    "### 🚢 Fleet Intelligence Analysis"
                )

                st.markdown(answer)

            except Exception as e:

                st.error(
                    f"Gemini gagal memproses Fleet 21: {e}"
                )

        

# ============================================================
# EXECUTIVE REPORTS
# ============================================================

elif menu == "Executive Reports":

    st.header("📑 Executive Reports")

    st.subheader(
        "Daily Marine Operations Brief"
    )

    report_date = datetime.now().strftime(
        "%d %B %Y"
    )

    st.write(
        f"Report date: **{report_date}**"
    )

    report = {
        "Fleet": 21,
        "Crew": 200,
        "Critical Risks": 0,
        "Open Defects": 0,
        "Open HSSE Findings": 0,
        "Overdue Actions": 0,
    }

    st.json(report)

    st.info(
        "Executive report otomatis akan dihubungkan "
        "ke AI Copilot setelah database operasional aktif."
    )

# ============================================================
# WHATSAPP
# ============================================================

elif menu == "WhatsApp Operations":

    st.header("📱 WhatsApp Operations Intelligence")

    st.info(
        """
        Modul ini disiapkan untuk integrasi operational
        communication.

        Tahap berikutnya:
        1. WhatsApp Business Platform / Cloud API
        2. Webhook backend
        3. Operational message database
        4. AI classification
        5. Risk extraction
        6. Vessel mapping
        7. Escalation
        """
    )

    whatsapp_df = pd.DataFrame(
        columns=[
            "Time",
            "Vessel",
            "Sender",
            "Message",
            "Risk",
            "Status",
        ]
    )

    st.dataframe(
        whatsapp_df,
        use_container_width=True,
        hide_index=True
    )

# ============================================================
# SYSTEM
# ============================================================

elif menu == "System":

    st.header("⚙️ System Control Centre")

    st.subheader(
        "System Status"
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.success(
            "Application Online"
        )

    with c2:
        st.success(
            "Fleet Database Online"
        )

    with c3:
        st.success(
            "AI Framework Ready"
        )

    st.divider()

    st.subheader(
        "Architecture"
    )

    st.markdown(
        """
        **Marine Operations Intelligence Centre**

        Application Layer
        → Streamlit

        Intelligence Layer
        → AI Marine Operations Copilot

        Data Layer
        → Fleet / Crew / Voyage / PMS / HSSE / Defects /
        Certificates / Bunker / Cargo

        Communication Layer
        → WhatsApp Business Platform

        Executive Layer
        → SITREP / Risk Dashboard / Executive Reports
        """
    )

    st.divider()

    st.subheader(
        "Deployment Information"
    )

    st.write(
        "Version: Intelligence Centre Foundation 1.0"
    )

    st.write(
        "Fleet: 21 vessels"
    )

    st.write(
        "Crew master: 200"
    )

    st.write(
        f"Current role: {st.session_state.role}"
    )

# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "MARINE OPERATIONS INTELLIGENCE CENTRE • "
    "Fleet • HSSE • PMS • Voyage • Risk • AI Copilot"
)
