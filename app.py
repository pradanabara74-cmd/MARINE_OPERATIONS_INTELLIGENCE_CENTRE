import streamlit as st
import pandas as pd
from datetime import datetime

# ============================================================
# MARINE OPERATIONS INTELLIGENCE CENTRE
# Foundation Application
# Version 1.0
# ============================================================

st.set_page_config(
    page_title="Marine Operations Intelligence Centre",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# FLEET MASTER - 21 VESSELS
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

# ============================================================
# SESSION STATE
# ============================================================

if "selected_menu" not in st.session_state:
    st.session_state.selected_menu = "Dashboard"

if "role" not in st.session_state:
    st.session_state.role = "Marine Superintendent"

# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 34px;
        font-weight: 700;
        margin-bottom: 0px;
    }

    .subtitle {
        font-size: 16px;
        color: #666666;
        margin-bottom: 25px;
    }

    .metric-card {
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #dddddd;
        background: #ffffff;
        text-align: center;
    }

    .section-title {
        font-size: 24px;
        font-weight: 650;
        margin-top: 10px;
        margin-bottom: 15px;
    }

    .status-ok {
        padding: 12px;
        border-radius: 8px;
        background: #e8f5e9;
        border: 1px solid #b7dfb9;
    }

    .status-info {
        padding: 12px;
        border-radius: 8px;
        background: #eef5ff;
        border: 1px solid #c9dcff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⚓ MARINE OIC")

st.sidebar.caption("Marine Operations Intelligence Centre")

st.sidebar.divider()

st.session_state.role = st.sidebar.selectbox(
    "Role",
    [
        "Marine Superintendent",
        "DPA",
        "Manager Operation Marine",
    ],
    index=0,
)

menu_items = [
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
    "WhatsApp Operations",
    "Executive Reports",
    "AI Marine Operations Copilot",
    "System",
]

menu = st.sidebar.radio(
    "MENU",
    menu_items,
)

st.sidebar.divider()

st.sidebar.metric("Fleet", "21 vessels")
st.sidebar.metric("Crew Master", "200")
st.sidebar.caption(
    "Marine Operations Intelligence Centre"
)

# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">⚓ MARINE OPERATIONS INTELLIGENCE CENTRE</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Fleet Intelligence • Marine Operations • HSSE • PMS • Crew • AI"
    "</div>",
    unsafe_allow_html=True,
)

# ============================================================
# DASHBOARD
# ============================================================

if menu == "Dashboard":

    st.markdown(
        '<div class="section-title">Operational Intelligence Dashboard</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Fleet",
            "21",
            "Active vessels",
        )

    with col2:
        st.metric(
            "Crew",
            "200",
            "Master database",
        )

    with col3:
        st.metric(
            "Voyages",
            "0",
            "Recorded",
        )

    with col4:
        st.metric(
            "Critical Risks",
            "0",
            "Awaiting live data",
        )

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Fleet Readiness")

        readiness = pd.DataFrame(
            {
                "Status": [
                    "Operational",
                    "Under Monitoring",
                    "Maintenance",
                    "Critical",
                ],
                "Vessels": [
                    21,
                    0,
                    0,
                    0,
                ],
            }
        )

        st.dataframe(
            readiness,
            use_container_width=True,
            hide_index=True,
        )

    with right:
        st.subheader("Priority Intelligence")

        st.info(
            "Belum ada data operasional live yang "
            "dimasukkan ke Intelligence Centre."
        )

        st.write(
            "AI Copilot nantinya akan membaca data "
            "Fleet, Voyage, HSSE/DPA, PMS, Defects, "
            "Certificates, Crew, Bunker, Cargo, "
            "Audit dan Action Tracker."
        )

    st.divider()

    st.subheader("Today's Marine Operations Focus")

    st.warning(
        "Data operasional belum terhubung ke database live. "
        "Sistem tidak akan mengarang kondisi kapal."
    )

# ============================================================
# FLEET
# ============================================================

elif menu == "Fleet 21":

    st.markdown(
        '<div class="section-title">Fleet Intelligence — 21 Vessels</div>',
        unsafe_allow_html=True,
    )

    fleet_df = pd.DataFrame(
        {
            "No": range(1, 22),
            "Vessel": FLEET,
            "Status": ["Active"] * 21,
            "Position": ["Not Available"] * 21,
            "Voyage": ["Not Recorded"] * 21,
            "Risk": ["Not Assessed"] * 21,
        }
    )

    st.dataframe(
        fleet_df,
        use_container_width=True,
        hide_index=True,
    )

# ============================================================
# CREW
# ============================================================

elif menu == "Crew 200":

    st.markdown(
        '<div class="section-title">Crew Intelligence</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Crew Master", "200")
    col2.metric("Active Crew", "0")
    col3.metric("Expiring Documents", "0")

    st.info(
        "Crew database module siap dikembangkan "
        "untuk rank, vessel assignment, certification, "
        "medical fitness, training dan rotation."
    )

# ============================================================
# VOYAGE
# ============================================================

elif menu == "Voyage Operations":

    st.markdown(
        '<div class="section-title">Voyage & Operations Intelligence</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "Modul Voyage Operations akan menjadi pusat "
        "monitoring perjalanan, port call, cargo, ETA/ETD, "
        "operational status dan voyage risk."
    )

    st.dataframe(
        pd.DataFrame(
            columns=[
                "Vessel",
                "Voyage",
                "Origin",
                "Destination",
                "ETA",
                "Status",
                "Risk",
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

# ============================================================
# HSSE / DPA
# ============================================================

elif menu == "HSSE / DPA":

    st.markdown(
        '<div class="section-title">HSSE / DPA Intelligence</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Incidents", "0")
    col2.metric("Near Miss", "0")
    col3.metric("Open Findings", "0")
    col4.metric("Critical HSSE", "0")

    st.info(
        "HSSE intelligence akan menghubungkan incident, "
        "near miss, unsafe condition, DPA reports, "
        "ISM / ISPS / MARPOL compliance dan corrective actions."
    )

# ============================================================
# PMS
# ============================================================

elif menu == "PMS / Maintenance":

    st.markdown(
        '<div class="section-title">PMS / Maintenance Intelligence</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("PMS Due", "0")
    col2.metric("Overdue", "0")
    col3.metric("Critical Machinery", "0")

    st.info(
        "PMS module akan digunakan untuk planned maintenance, "
        "overdue jobs, machinery condition dan maintenance risk."
    )

# ============================================================
# DEFECTS
# ============================================================

elif menu == "Defects":

    st.markdown(
        '<div class="section-title">Defect Management</div>',
        unsafe_allow_html=True,
    )

    st.metric("Open Defects", "0")

    st.dataframe(
        pd.DataFrame(
            columns=[
                "Vessel",
                "Defect",
                "Category",
                "Priority",
                "Responsible",
                "Due Date",
                "Status",
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

# ============================================================
# CERTIFICATES
# ============================================================

elif menu == "Certificates":

    st.markdown(
        '<div class="section-title">Certificate Intelligence</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Certificates", "0")
    col2.metric("Expiring < 30 Days", "0")
    col3.metric("Expired", "0")

    st.info(
        "Certificate monitoring akan mencakup statutory, "
        "class, flag, safety dan operational certificates."
    )

# ============================================================
# BUNKER
# ============================================================

elif menu == "Bunker":

    st.markdown(
        '<div class="section-title">Bunker Intelligence</div>',
        unsafe_allow_html=True,
    )

    st.metric("Bunker Records", "0")

    st.info(
        "Monitoring fuel consumption, ROB, bunker delivery "
        "dan abnormal consumption akan ditambahkan di tahap berikutnya."
    )

# ============================================================
# CARGO
# ============================================================

elif menu == "Cargo":

    st.markdown(
        '<div class="section-title">Cargo Operations Intelligence</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "Cargo module akan mencatat cargo operation, "
        "quantity, loading/discharging status dan operational risk."
    )

# ============================================================
# AUDIT
# ============================================================

elif menu == "Audit & Findings":

    st.markdown(
        '<div class="section-title">Audit & Findings Intelligence</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Open Findings", "0")
    col2.metric("Overdue Findings", "0")
    col3.metric("Critical Findings", "0")

# ============================================================
# ACTION TRACKER
# ============================================================

elif menu == "Action Tracker":

    st.markdown(
        '<div class="section-title">Action Tracker</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "Central action tracker untuk memastikan setiap "
        "temuan memiliki responsible person, due date, "
        "priority dan closure evidence."
    )

    st.dataframe(
        pd.DataFrame(
            columns=[
                "Action",
                "Source",
                "Vessel",
                "Priority",
                "Responsible",
                "Due Date",
                "Status",
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

# ============================================================
# WHATSAPP
# ============================================================

elif menu == "WhatsApp Operations":

    st.markdown(
        '<div class="section-title">WhatsApp Operations Intelligence</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "WhatsApp Operations akan menjadi sumber operational "
        "reports dari vessel dan shore team."
    )

    st.write(
        "Tahap berikutnya akan menambahkan:"
    )

    st.write(
        """
        • Group mapping 21 vessel
        • Incoming operational reports
        • Message classification
        • Incident / defect extraction
        • Alert generation
        • AI summarisation
        • Escalation
        """
    )

    st.warning(
        "Integrasi WhatsApp resmi akan dibuat menggunakan "
        "WhatsApp Business Platform / Cloud API. "
        "Tidak menggunakan WhatsApp Web scraping."
    )

# ============================================================
# EXECUTIVE REPORTS
# ============================================================

elif menu == "Executive Reports":

    st.markdown(
        '<div class="section-title">Executive Marine Reports</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "Executive reporting akan menghasilkan laporan "
        "operasional harian untuk Marine Superintendent, "
        "DPA dan Manager Operation Marine."
    )

    report_type = st.selectbox(
        "Report Type",
        [
            "Daily Fleet SITREP",
            "HSSE Executive Report",
            "Maintenance Executive Report",
            "Voyage Operations Report",
            "Marine Management Report",
        ],
    )

    if st.button("GENERATE REPORT", type="primary"):
        st.success(
            f"Template {report_type} siap. "
            "AI reporting akan diaktifkan pada tahap berikutnya."
        )

# ============================================================
# AI COPILOT
# ============================================================

elif menu == "AI Marine Operations Copilot":

    st.markdown(
        '<div class="section-title">🤖 AI Marine Operations Copilot</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        f"Role: {st.session_state.role} • "
        "Fleet: 21 Vessels • Crew Master: 200"
    )

    st.success(
        "AI Copilot Foundation READY"
    )

    st.write(
        "AI Copilot akan menjadi pusat intelligence untuk:"
    )

    st.write(
        """
        **1. Fleet Intelligence**
        
        Kondisi seluruh 21 kapal dan prioritas risiko.
        
        **2. Operational Risk**
        
        Identifikasi risiko berdasarkan data aktual.
        
        **3. HSSE / DPA**
        
        Incident, near miss, findings dan compliance.
        
        **4. PMS / Defects**
        
        Maintenance risk dan overdue actions.
        
        **5. Voyage**
        
        Voyage status dan operational continuity.
        
        **6. WhatsApp Intelligence**
        
        Operational reports dari vessel / shore team.
        
        **7. Executive Decision Support**
        
        Prioritas tindakan untuk management.
        """
    )

    question = st.text_area(
        "Pertanyaan / instruksi kepada AI",
        placeholder=(
            "Contoh: Buatkan ringkasan kondisi operasional "
            "21 kapal dan 5 risiko tertinggi berdasarkan "
            "data yang tersedia."
        ),
        height=140,
    )

    if st.button("ASK AI", type="primary"):

        if not question.strip():
            st.warning(
                "Masukkan pertanyaan terlebih dahulu."
            )
        else:
            st.info(
                "AI engine belum dihubungkan. "
                "Connection ke Gemini akan kita pasang "
                "setelah fondasi aplikasi berhasil dijalankan."
            )

# ============================================================
# SYSTEM
# ============================================================

elif menu == "System":

    st.markdown(
        '<div class="section-title">System Configuration</div>',
        unsafe_allow_html=True,
    )

    st.subheader("Application Information")

    st.write(
        "Application: MARINE OPERATIONS INTELLIGENCE CENTRE"
    )

    st.write("Fleet Master: 21 vessels")
    st.write("Crew Master: 200 employees")
    st.write(
        "Current Role: "
        + st.session_state.role
    )

    st.divider()

    st.subheader("System Status")

    st.success("Application foundation: ONLINE")
    st.success("Fleet master: READY")
    st.success("Navigation framework: READY")
    st.info("AI Engine: PENDING INTEGRATION")
    st.info("Database: PENDING INTEGRATION")
    st.info("WhatsApp API: PENDING INTEGRATION")

    st.caption(
        "Build progressively. Existing MARINE_OPERATION_VESSEL_PRO "
        "is not modified by this application."
    )

# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "MARINE OPERATIONS INTELLIGENCE CENTRE • "
    f"© {datetime.now().year} • "
    "Operational Intelligence Platform"
)
