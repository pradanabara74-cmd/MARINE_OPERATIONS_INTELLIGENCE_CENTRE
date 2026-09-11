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
        return "Gemini AI belum aktif. Silakan konfigurasi GEMINI_API_KEY di Streamlit Secrets."

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

            if "503" not in error_text and "UNAVAILABLE" not in error_text:
                raise

            if attempt < 2:
                time.sleep(3 * (attempt + 1))

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

    st.header("🛡️ HSSE / DPA Command")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Incidents",
            "0"
        )

    with c2:
        st.metric(
            "Near Miss",
            "0"
        )

    with c3:
        st.metric(
            "Open Findings",
            "0"
        )

    st.info(
        "Risk intelligence akan menggabungkan HSSE, defects, "
        "certificates, PMS dan operational reports."
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

    defect_df = pd.DataFrame(
        columns=[
            "Vessel",
            "Defect",
            "Severity",
            "Reported",
            "Due Date",
            "Status",
            "Responsible",
        ]
    )

    st.dataframe(
        defect_df,
        use_container_width=True,
        hide_index=True
    )

# ============================================================
# CERTIFICATES
# ============================================================

elif menu == "Certificates":

    st.header("📜 Certificate Intelligence")

    st.info(
        "Certificate tracking akan mencakup expiry, statutory, "
        "class, flag dan operational certificates."
    )

# ============================================================
# BUNKER
# ============================================================

elif menu == "Bunker":

    st.header("⛽ Bunker Intelligence")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Vessels",
            "21"
        )

    with c2:
        st.metric(
            "Bunker Reports",
            "0"
        )

    with c3:
        st.metric(
            "Consumption Alerts",
            "0"
        )

# ============================================================
# CARGO
# ============================================================

elif menu == "Cargo":

    st.header("📦 Cargo Operations")

    st.info(
        "Cargo intelligence module siap dikembangkan untuk "
        "cargo status, quantity, destination, operational risk "
        "dan voyage linkage."
    )

# ============================================================
# AUDIT
# ============================================================

elif menu == "Audit & Findings":

    st.header("🔍 Audit & Findings")

    audit_df = pd.DataFrame(
        columns=[
            "Finding ID",
            "Vessel",
            "Finding",
            "Severity",
            "Due Date",
            "Status",
            "Owner",
        ]
    )

    st.dataframe(
        audit_df,
        use_container_width=True,
        hide_index=True
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
