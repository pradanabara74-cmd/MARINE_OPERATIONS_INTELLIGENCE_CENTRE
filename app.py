import streamlit as st
import pandas as pd
import json
from datetime import datetime

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

    st.metric(
        "Maintenance Records",
        "0"
    )

    st.warning(
        "Belum ada PMS record."
    )

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

    st.info(
        """
        AI Copilot akan menjadi pusat intelligence:
        
        • Fleet risk assessment
        • Daily SITREP
        • Top operational risks
        • Defect prioritisation
        • PMS risk
        • Certificate risk
        • HSSE/DPA analysis
        • Voyage risk
        • Executive briefing
        • WhatsApp operational intelligence
        """
    )

    st.subheader(
        "Pertanyaan / Instruksi"
    )

    prompt = st.text_area(
        "Tanyakan kepada Marine Operations Copilot",
        placeholder=(
            "Contoh: Buatkan ringkasan kondisi 21 kapal, "
            "5 risiko tertinggi dan tindakan prioritas hari ini."
        ),
        height=150,
    )

    if st.button(
        "ASK AI",
        type="primary"
    ):

        if not prompt.strip():

            st.warning(
                "Masukkan pertanyaan terlebih dahulu."
            )

        else:

            # ------------------------------------------------
            # AI PLACEHOLDER
            # ------------------------------------------------

            response = f"""
## MARINE OPERATIONS INTELLIGENCE ANALYSIS

**Role:** {st.session_state.role}

### Request
{prompt}

### Current Database Facts

- Fleet: **21 vessels**
- Crew master: **200 employees**
- Active vessels recorded: **21**
- Voyage records available: **0**
- Defect records available: **0**
- Certificate records available: **0**
- PMS records available: **0**
- HSSE findings available: **0**

### Intelligence Assessment

Saat ini belum tersedia cukup data operasional
untuk menghasilkan risk ranking yang faktual.

**AI tidak akan mengarang data.**

### Immediate Priority

1. Lengkapi voyage data.
2. Lengkapi defect register.
3. Lengkapi certificate register.
4. Lengkapi PMS status.
5. Lengkapi HSSE / DPA findings.
6. Hubungkan operational reports / WhatsApp.
7. Jalankan AI risk assessment setelah data tersedia.

### Executive Decision

Data gap saat ini merupakan risiko informasi.
Prioritas pertama adalah membangun single source of truth
untuk seluruh 21 kapal.
"""

            st.markdown(response)

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
