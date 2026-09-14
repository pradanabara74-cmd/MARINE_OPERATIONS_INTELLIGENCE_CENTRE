import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
import uuid
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from google import genai
from google.genai import types


# ============================================================
# GEMINI AI
# ============================================================

def get_gemini_client():
    try:
        api_key = str(
            st.secrets.get("GEMINI_API_KEY", "")
        ).strip()
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
   crew, bunker, cargo, audit finding, action status or other operational data.
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
                    max_output_tokens=2500,
                ),
            )

            return response.text

        except Exception as e:
            last_error = e
            error_text = str(e)

            if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
                return (
                    "Gemini sedang mencapai batas quota penggunaan. "
                    "Data berhasil dimuat, tetapi analisis AI belum dapat "
                    "dijalankan. Silakan coba lagi setelah quota tersedia."
                )

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
# PERSISTENT DATA LAYER - SUPABASE
# ============================================================

SUPABASE_URL = ""
SUPABASE_KEY = ""

try:
    SUPABASE_URL = str(
        st.secrets.get("SUPABASE_URL", "")
    ).strip().rstrip("/")

    SUPABASE_KEY = str(
        st.secrets.get("SUPABASE_SECRET_KEY", "")
    ).strip()

    if not SUPABASE_KEY:
        SUPABASE_KEY = str(
            st.secrets.get("SUPABASE_SERVICE_ROLE_KEY", "")
        ).strip()

except Exception:
    SUPABASE_URL = ""
    SUPABASE_KEY = ""


def supabase_enabled():
    return bool(SUPABASE_URL and SUPABASE_KEY)


def supabase_request(method, table, params=None, payload=None):
    """
    REST client Supabase.
    Tidak membutuhkan package supabase tambahan.
    """

    if not supabase_enabled():
        return []

    query = ""

    if params:
        query = "?" + urlencode(
            params,
            doseq=True,
        )

    url = f"{SUPABASE_URL}/rest/v1/{table}{query}"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    if method.upper() in [
        "POST",
        "PATCH",
        "DELETE",
    ]:
        headers["Prefer"] = "return=representation"

        if params and "on_conflict" in params:
            headers["Prefer"] = (
                "resolution=merge-duplicates,"
                "return=representation"
            )

    body = None

    if payload is not None:
        body = json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")

    request = Request(
        url,
        data=body,
        headers=headers,
        method=method.upper(),
    )

    try:
        with urlopen(
            request,
            timeout=20,
        ) as response:

            raw = response.read().decode("utf-8")

            if not raw:
                return []

            return json.loads(raw)

    except HTTPError as exc:
        detail = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"Supabase HTTP {exc.code}: {detail}"
        ) from exc

    except URLError as exc:
        raise RuntimeError(
            f"Supabase connection error: {exc.reason}"
        ) from exc


# ============================================================
# ACTION TRACKER DATABASE
# ============================================================

def normalize_action_record(row):
    return {
        "Action ID": row.get("action_id", ""),
        "Vessel": row.get("vessel", "All Fleet"),
        "Source": row.get("source", "Other"),
        "Description": row.get("description", ""),
        "Priority": row.get("priority", "Medium"),
        "Responsible": row.get("responsible", ""),
        "Due Date": row.get("due_date", ""),
        "Status": row.get("status", "Open"),
        "Remarks": row.get("remarks", ""),
        "Created": row.get("created_at", ""),
        "Updated": row.get("updated_at", ""),
        "Completed": row.get("completed_at", ""),
        "Created By": row.get("created_by", ""),
        "Role": row.get("role", ""),
    }


def load_actions_from_db():
    if not supabase_enabled():
        return []

    rows = supabase_request(
        "GET",
        "actions",
        params={
            "select": "*",
            "order": "created_at.desc",
        },
    )

    return [
        normalize_action_record(row)
        for row in rows
    ]


def action_to_db_row(action):
    completed_at = action.get(
        "Completed",
        None,
    )

    if str(
        action.get("Status", "")
    ).lower() == "completed":

        if not completed_at:
            completed_at = datetime.now().isoformat()

    else:
        completed_at = None

    return {
        "action_id": action.get(
            "Action ID",
            "",
        ),
        "vessel": action.get(
            "Vessel",
            "All Fleet",
        ),
        "source": action.get(
            "Source",
            "Other",
        ),
        "description": action.get(
            "Description",
            "",
        ),
        "priority": action.get(
            "Priority",
            "Medium",
        ),
        "responsible": action.get(
            "Responsible",
            "",
        ),
        "due_date": str(
            action.get(
                "Due Date",
                "",
            )
        ) or None,
        "status": action.get(
            "Status",
            "Open",
        ),
        "remarks": action.get(
            "Remarks",
            "",
        ),
        "created_by": action.get(
            "Created By",
            "",
        ),
        "role": action.get(
            "Role",
            "",
        ),
        "completed_at": completed_at,
    }


def create_action_persistent(action):

    if supabase_enabled():

        payload = action_to_db_row(
            action
        )

        payload["created_at"] = (
            action.get("Created")
            or datetime.now().isoformat()
        )

        payload["updated_at"] = (
            datetime.now().isoformat()
        )

        return supabase_request(
            "POST",
            "actions",
            payload=payload,
        )

    if "action_records" not in st.session_state:
        st.session_state["action_records"] = []

    st.session_state[
        "action_records"
    ].append(action)

    return [action]


def update_action_persistent(
    action_id,
    action,
):

    if supabase_enabled():

        payload = action_to_db_row(
            action
        )

        payload["updated_at"] = (
            datetime.now().isoformat()
        )

        return supabase_request(
            "PATCH",
            "actions",
            params={
                "action_id": f"eq.{action_id}"
            },
            payload=payload,
        )

    records = st.session_state.get(
        "action_records",
        [],
    )

    for index, record in enumerate(records):
        if record.get(
            "Action ID"
        ) == action_id:
            records[index] = action
            break

    st.session_state[
        "action_records"
    ] = records

    return [action]


def delete_action_persistent(
    action_id,
):

    if supabase_enabled():

        return supabase_request(
            "DELETE",
            "actions",
            params={
                "action_id": f"eq.{action_id}"
            },
        )

    records = st.session_state.get(
        "action_records",
        [],
    )

    records = [
        record
        for record in records
        if record.get(
            "Action ID"
        ) != action_id
    ]

    st.session_state[
        "action_records"
    ] = records

    return []


def load_actions():

    if supabase_enabled():
        try:
            return load_actions_from_db()

        except Exception as e:
            st.error(
                f"Database Action Tracker error: {e}"
            )
            return []

    return st.session_state.get(
        "action_records",
        [],
    )


def next_action_id(actions):

    numbers = []

    for action in actions:

        value = str(
            action.get(
                "Action ID",
                "",
            )
        )

        if value.startswith("ACT-"):
            try:
                numbers.append(
                    int(
                        value.replace(
                            "ACT-",
                            "",
                        )
                    )
                )
            except Exception:
                pass

    next_number = (
        max(numbers) + 1
        if numbers
        else 1
    )

    return f"ACT-{next_number:04d}"


def action_is_overdue_global(action):

    if str(
        action.get(
            "Status",
            "",
        )
    ).lower() == "completed":
        return False

    due_date = action.get(
        "Due Date",
        "",
    )

    if not due_date:
        return False

    try:
        due = pd.to_datetime(
            due_date
        ).date()

        return due < datetime.now().date()

    except Exception:
        return False


def action_kpis(actions):

    total = len(actions)

    open_count = sum(
        1
        for action in actions
        if str(
            action.get(
                "Status",
                "",
            )
        ).lower() == "open"
    )

    in_progress = sum(
        1
        for action in actions
        if str(
            action.get(
                "Status",
                "",
            )
        ).lower() == "in progress"
    )

    completed = sum(
        1
        for action in actions
        if str(
            action.get(
                "Status",
                "",
            )
        ).lower() == "completed"
    )

    overdue = sum(
        1
        for action in actions
        if action_is_overdue_global(
            action
        )
    )

    return {
        "total": total,
        "open": open_count,
        "in_progress": in_progress,
        "overdue": overdue,
        "completed": completed,
    }


# ============================================================
# OPERATIONAL SNAPSHOTS
# ============================================================

def save_operational_snapshot(
    module,
    records,
    metrics,
):

    if not supabase_enabled():
        st.session_state[
            f"snapshot_{module}"
        ] = {
            "module": module,
            "records": records,
            "metrics": metrics,
            "updated_at": (
                datetime.now().isoformat()
            ),
        }
        return

    payload = {
        "module": module,
        "records": records,
        "metrics": metrics,
        "updated_at": (
            datetime.now().isoformat()
        ),
    }

    supabase_request(
        "POST",
        "operational_snapshots",
        params={
            "on_conflict": "module"
        },
        payload=payload,
    )


def load_operational_snapshots():

    if supabase_enabled():

        try:
            rows = supabase_request(
                "GET",
                "operational_snapshots",
                params={
                    "select": "*",
                    "order": "updated_at.desc",
                },
            )

            return {
                row.get("module"): row
                for row in rows
            }

        except Exception as e:
            st.error(
                f"Operational database error: {e}"
            )

            return {}

    result = {}

    for key, value in st.session_state.items():

        if key.startswith(
            "snapshot_"
        ):
            result[
                key.replace(
                    "snapshot_",
                    "",
                )
            ] = value

    return result


# ============================================================
# WHATSAPP MESSAGE DATABASE
# ============================================================

def save_whatsapp_message(
    message,
):

    if not supabase_enabled():

        if (
            "whatsapp_messages"
            not in st.session_state
        ):
            st.session_state[
                "whatsapp_messages"
            ] = []

        st.session_state[
            "whatsapp_messages"
        ].append(message)

        return [message]

    return supabase_request(
        "POST",
        "whatsapp_messages",
        payload=message,
    )


def load_whatsapp_messages():

    if not supabase_enabled():

        return st.session_state.get(
            "whatsapp_messages",
            [],
        )

    return supabase_request(
        "GET",
        "whatsapp_messages",
        params={
            "select": "*",
            "order": "message_time.desc",
        },
    )


# ============================================================
# AI INTELLIGENCE CONTEXT
# ============================================================

def build_intelligence_context():

    snapshots = (
        load_operational_snapshots()
    )

    actions = load_actions()

    context = {
        "fleet_size": 21,
        "operational_snapshots": {},
        "action_tracker": actions[:100],
    }

    for module, snapshot in snapshots.items():

        context[
            "operational_snapshots"
        ][module] = {
            "metrics": snapshot.get(
                "metrics",
                {},
            ),
            "records": snapshot.get(
                "records",
                [],
            )[:100],
            "updated_at": snapshot.get(
                "updated_at",
                "",
            ),
        }

    return context
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

            admin_username = st.secrets.get(
                "ADMIN_USERNAME",
                "admin"
            )

            admin_password = st.secrets.get(
                "ADMIN_PASSWORD",
                ""
            )

            if (
                username.strip() == admin_username
                and password == admin_password
            ):

                st.session_state.logged_in = True
                st.session_state.role = role
                st.rerun()

            else:

                st.error(
                    "Username atau password tidak benar."
                )

        st.stop()


# ============================================================
# LOAD PERSISTENT OPERATIONAL DATA
# ============================================================

if "action_records" not in st.session_state:
    st.session_state["action_records"] = []

if supabase_enabled():

    try:

        st.session_state[
            "action_records"
        ] = load_actions_from_db()

    except Exception as persistence_error:

        st.session_state[
            "persistence_error"
        ] = str(
            persistence_error
        )


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
        index=ROLES.index(
            st.session_state.role
        )
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
    f"Operational Intelligence Platform • "
    f"{st.session_state.role}"
)

st.divider()


# ============================================================
# DASHBOARD
# ============================================================

if menu == "Dashboard":

    st.header(
        "📊 Operations Command Dashboard"
    )

    st.caption(
        "Marine Operations Intelligence Centre • "
        "Fleet status, voyage exceptions and operational priorities."
    )

    # =====================================================
    # DASHBOARD DATA
    # =====================================================

    fleet_count = len(FLEET)

    active_vessels = sum(
        1
        for row in VESSEL_DATA
        if row.get("Status") == "Active"
    )

    snapshots = load_operational_snapshots()

    voyage_metrics = (
        snapshots.get(
            "Voyage Operations",
            {}
        ).get(
            "metrics",
            {}
        )
    )

    hsse_metrics = (
        snapshots.get(
            "HSSE / DPA",
            {}
        ).get(
            "metrics",
            {}
        )
    )

    pms_metrics = (
        snapshots.get(
            "PMS / Maintenance",
            {}
        ).get(
            "metrics",
            {}
        )
    )

    defect_metrics = (
        snapshots.get(
            "Defects",
            {}
        ).get(
            "metrics",
            {}
        )
    )

    certificate_metrics = (
        snapshots.get(
            "Certificates",
            {}
        ).get(
            "metrics",
            {}
        )
    )

    bunker_metrics = (
        snapshots.get(
            "Bunker",
            {}
        ).get(
            "metrics",
            {}
        )
    )

    cargo_metrics = (
        snapshots.get(
            "Cargo",
            {}
        ).get(
            "metrics",
            {}
        )
    )

    audit_metrics = (
        snapshots.get(
            "Audit & Findings",
            {}
        ).get(
            "metrics",
            {}
        )
    )

    voyage_records = voyage_metrics.get(
        "records",
        st.session_state.get(
            "voyage_records",
            0
        )
    )

    delayed_exception = voyage_metrics.get(
        "delayed",
        st.session_state.get(
            "delayed_exception",
            0
        )
    )

    attention_required = voyage_metrics.get(
        "attention",
        st.session_state.get(
            "attention_required",
            0
        )
    )

    open_defects = defect_metrics.get(
        "open",
        st.session_state.get(
            "open_defects",
            0
        )
    )

    certificate_records = certificate_metrics.get(
        "records",
        st.session_state.get(
            "certificate_records",
            0
        )
    )

    pms_records = pms_metrics.get(
        "records",
        st.session_state.get(
            "pms_records",
            0
        )
    )

    hsse_findings = hsse_metrics.get(
        "open_findings",
        st.session_state.get(
            "hsse_findings",
            0
        )
    )

    dashboard_actions = (
        load_actions_from_db()
        if supabase_enabled()
        else st.session_state.get(
            "action_records",
            []
        )
    )

    action_counts = action_kpis(
        dashboard_actions
    )

    pending_actions = (
    action_counts["open"]
    + action_counts["in_progress"]
)

    overdue_actions = action_counts[
        "overdue"
    ]

    # =====================================================
    # COMMAND STATUS
    # =====================================================

    st.markdown(
        "### 🚨 Command Status"
    )

    col1, col2, col3, col4 = st.columns(
        4
    )

    with col1:

        st.metric(
            "Fleet",
            fleet_count
        )

    with col2:

        st.metric(
            "Active Vessels",
            active_vessels
        )

    with col3:

        st.metric(
            "Voyage Attention",
            attention_required
        )

    with col4:

        critical_alerts = (
            delayed_exception
            + open_defects
            + hsse_findings
            + pending_actions
        )

        st.metric(
            "Critical Alerts",
            critical_alerts
        )

    # =====================================================
    # OPERATIONAL INTELLIGENCE
    # =====================================================

    st.markdown(
        "### 🧠 Operational Intelligence"
    )

    if critical_alerts == 0:

        st.success(
            "OPERATIONAL STATUS: OPERATIONAL"
        )

        st.write(
            "Tidak terdapat critical operational alert "
            "berdasarkan data yang tersedia."
        )

    elif critical_alerts > 0:

        st.warning(
            "OPERATIONAL STATUS: ATTENTION REQUIRED"
        )

        st.write(
            f"Terdapat {critical_alerts} operational "
            "item yang membutuhkan perhatian."
        )

    # =====================================================
    # INTELLIGENCE OVERVIEW
    # =====================================================

    st.markdown(
        "### 📋 Fleet & Operational Intelligence Overview"
    )

    dashboard_df = pd.DataFrame(
        {
            "Indicator": [
                "Fleet",
                "Active Vessel",
                "Voyage Records",
                "Delayed / Exception",
                "Attention Required",
                "Open Defects",
                "Certificate Records",
                "PMS Records",
                "HSSE Findings",
                "Pending Actions",
                "Overdue Actions",
                "Bunker Reports",
                "Cargo Records",
                "Audit Open Findings",
            ],

            "Value": [
                fleet_count,
                active_vessels,
                voyage_records,
                delayed_exception,
                attention_required,
                open_defects,
                certificate_records,
                pms_records,
                hsse_findings,
                pending_actions,
                overdue_actions,
                bunker_metrics.get(
                    "records",
                    0
                ),
                cargo_metrics.get(
                    "records",
                    0
                ),
                audit_metrics.get(
                    "open",
                    0
                ),
            ],
        }
    )

    # =====================================================
    # STATUS LOGIC
    # =====================================================

    status_list = []

    for indicator, value in zip(
        dashboard_df["Indicator"],
        dashboard_df["Value"]
    ):

        if indicator in [
            "Fleet",
            "Active Vessel",
        ]:

            status = "ACTIVE"

        elif indicator == "Voyage Records":

            status = (
                "AVAILABLE"
                if value > 0
                else "DATA GAP"
            )

        elif indicator in [
            "Delayed / Exception",
            "Attention Required",
            "Open Defects",
            "HSSE Findings",
            "Pending Actions",
            "Overdue Actions",
            "Audit Open Findings",
        ]:

            status = (
                "ATTENTION"
                if value > 0
                else "NORMAL"
            )

        else:

            status = (
                "AVAILABLE"
                if value > 0
                else "DATA GAP"
            )

        status_list.append(
            status
        )

    dashboard_df[
        "Status"
    ] = status_list

    st.dataframe(
        dashboard_df,
        use_container_width=True,
        hide_index=True
    )

    # =====================================================
    # OPERATIONAL PRIORITY
    # =====================================================

    st.markdown(
        "### 🎯 Operational Priority"
    )

    if attention_required > 0:

        st.warning(
            f"VOYAGE PRIORITY: "
            f"{attention_required} voyage record(s) "
            "require operational attention."
        )

    elif delayed_exception > 0:

        st.warning(
            f"VOYAGE EXCEPTION: "
            f"{delayed_exception} delayed / "
            "exception record(s) detected."
        )

    elif open_defects > 0:

        st.warning(
            f"DEFECT PRIORITY: "
            f"{open_defects} open defect(s) detected."
        )

    elif hsse_findings > 0:

        st.warning(
            f"HSSE PRIORITY: "
            f"{hsse_findings} HSSE finding(s) detected."
        )

    elif pending_actions > 0:

        st.warning(
            f"ACTION PRIORITY: "
            f"{pending_actions} pending action(s) detected."
        )

    else:

        st.info(
            "Tidak terdapat operational priority "
            "berdasarkan data yang tersedia."
        )

    # =====================================================
    # INTELLIGENCE DATA COVERAGE
    # =====================================================

    st.markdown(
        "### 🔎 Intelligence Data Coverage"
    )

    operational_domains = [
    voyage_records,
    open_defects,
    certificate_records,
    pms_records,
    hsse_findings,
    pending_actions,
]

    available_domains = sum(
        1
        for value in operational_domains
        if value > 0
    )

    st.write(
        f"Operational data domains available: "
        f"{available_domains}/6"
    )

    if available_domains < 6:

        st.info(
            "Dashboard Intelligence hanya menggunakan "
            "data operasional yang tersedia. "
            "Jika suatu domain belum memiliki data, "
            "sistem menandainya sebagai DATA GAP "
            "dan tidak membuat asumsi."
        )

    else:

        st.success(
            "Operational intelligence data coverage "
            "tersedia pada seluruh domain utama."
        )

    # =====================================================
    # DATA GOVERNANCE
    # =====================================================

    st.caption(
        "MARINE OPERATIONS INTELLIGENCE CENTRE • "
        "Fleet • HSSE • PMS • Voyage • Risk • AI Copilot"
    )
    # ============================================================
# FLEET 21
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
        FLEET,
        key="fleet21_vessel",
    )

    vessel_rows = VESSELS_DF[
        VESSELS_DF["Vessel"] == selected_vessel
    ]

    if vessel_rows.empty:

        st.warning(
            "Data kapal belum tersedia."
        )

    else:

        vessel = vessel_rows.iloc[0]

        def fleet_value(column_name):

            if column_name not in VESSELS_DF.columns:
                return "N/A"

            value = vessel[column_name]

            if pd.isna(value):
                return "N/A"

            value = str(value).strip()

            if value == "":
                return "N/A"

            if value.lower() in [
                "data belum tersedia",
                "tidak ada data",
                "belum dinilai",
                "n/a",
                "na",
            ]:
                return "N/A"

            return value

        vessel_status = fleet_value("Status")
        vessel_voyage = fleet_value("Voyage")
        vessel_defect = fleet_value("Defect")
        vessel_pms = fleet_value("PMS")
        vessel_risk = fleet_value("Risk")

        st.subheader(
            f"Vessel Intelligence — {selected_vessel}"
        )

        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:
            st.metric(
                "Status",
                vessel_status,
            )

        with c2:
            st.metric(
                "Voyage",
                vessel_voyage,
            )

        with c3:
            st.metric(
                "Defect",
                vessel_defect,
            )

        with c4:
            st.metric(
                "PMS",
                vessel_pms,
            )

        with c5:
            st.metric(
                "Risk",
                vessel_risk,
            )

        voyage_text = vessel_voyage.lower()
        defect_text = vessel_defect.lower()
        pms_text = vessel_pms.lower()
        risk_text = vessel_risk.lower()

        attention_items = []

        if any(
            keyword in voyage_text
            for keyword in [
                "delay",
                "delayed",
                "late",
                "exception",
                "hold",
                "cancel",
            ]
        ):
            attention_items.append(
                "Voyage membutuhkan perhatian."
            )

        if (
            vessel_defect != "N/A"
            and any(
                keyword in defect_text
                for keyword in [
                    "open",
                    "critical",
                    "high",
                    "defect",
                    "overdue",
                ]
            )
        ):
            attention_items.append(
                "Terdapat informasi defect "
                "yang perlu ditinjau."
            )

        if (
            vessel_pms != "N/A"
            and any(
                keyword in pms_text
                for keyword in [
                    "overdue",
                    "due",
                    "critical",
                    "high",
                ]
            )
        ):
            attention_items.append(
                "Terdapat perhatian pada PMS."
            )

        if any(
            keyword in risk_text
            for keyword in [
                "critical",
                "high",
                "medium",
                "attention",
            ]
        ):
            attention_items.append(
                f"Risk tercatat sebagai: {vessel_risk}."
            )

        st.markdown(
            "### Operational Assessment"
        )

        if attention_items:

            for item in attention_items:
                st.warning(item)

        elif (
            vessel_voyage == "N/A"
            and vessel_defect == "N/A"
            and vessel_pms == "N/A"
            and vessel_risk == "N/A"
        ):

            st.info(
                "Data operasional kapal belum cukup "
                "untuk menentukan risk assessment. "
                "Status kapal tersedia, tetapi Voyage, "
                "Defect, PMS dan Risk masih DATA GAP."
            )

        else:

            st.success(
                "Tidak ditemukan operational exception "
                "berdasarkan data yang tersedia."
            )

        st.caption(
            "Assessment hanya menggunakan data yang "
            "tersedia pada Fleet 21 dan tidak membuat "
            "asumsi terhadap data yang belum tersedia."
        )


# ============================================================
# CREW 200
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
        st.metric(
            "Expiring Certificates",
            "Data Gap"
        )

    st.info(
        "Modul Crew Intelligence akan dikembangkan dengan "
        "matrix competence, certificate validity, rank, "
        "vessel assignment dan fatigue monitoring."
    )


# ============================================================
# VOYAGE OPERATIONS
# ============================================================

elif menu == "Voyage Operations":

    st.header(
        "⚓ Voyage Operations Intelligence"
    )

    st.caption(
        "Voyage monitoring, delay detection, "
        "exception identification and operational "
        "priority assessment."
    )

    uploaded_voyage = st.file_uploader(
        "Upload Voyage Data (CSV)",
        type=["csv"],
        key="voyage_upload",
    )

    voyage_df = pd.DataFrame()

    if uploaded_voyage is None:

        snapshots = (
            load_operational_snapshots()
        )

        saved_voyage = snapshots.get(
            "Voyage Operations",
            {}
        )

        saved_records = saved_voyage.get(
            "records",
            []
        )

        if (
            isinstance(saved_records, list)
            and saved_records
        ):

            voyage_df = pd.DataFrame(
                saved_records
            )

            st.success(
                "Voyage data terakhir berhasil "
                "dimuat dari database Supabase."
            )

        else:

            st.info(
                "Upload Voyage Data (CSV) untuk "
                "menjalankan Voyage Operations Intelligence."
            )

    else:

        try:

            voyage_df = pd.read_csv(
                uploaded_voyage
            )

            st.session_state[
                "voyage_data"
            ] = voyage_df.copy()

        except Exception as e:

            st.error(
                f"Gagal membaca file Voyage/CSV: {e}"
            )

            voyage_df = pd.DataFrame()

    if not voyage_df.empty:

        required_columns = [
            "vessel",
            "voyage",
            "origin",
            "destination",
            "ETD",
            "ETA",
            "status",
            "remarks",
        ]

        for column in required_columns:

            if column not in voyage_df.columns:
                voyage_df[column] = ""

        voyage_df = voyage_df[
            required_columns
        ]

        voyage_df["status"] = (
            voyage_df["status"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        voyage_df["remarks"] = (
            voyage_df["remarks"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        status_text = (
            voyage_df["status"]
            .str.lower()
        )

        remarks_text = (
            voyage_df["remarks"]
            .str.lower()
        )

        delayed_mask = (
            status_text.str.contains(
                r"delay|delayed|late|exception|hold",
                regex=True,
                na=False,
            )
        )

        attention_mask = (
            delayed_mask
            |
            remarks_text.str.contains(
                r"delay|delayed|risk|hold|cancel|weather|abnormal|exception",
                regex=True,
                na=False,
            )
        )

        delayed_count = int(
            delayed_mask.sum()
        )

        attention_count = int(
            attention_mask.sum()
        )

        st.session_state[
            "voyage_records"
        ] = len(voyage_df)

        st.session_state[
            "delayed_exception"
        ] = delayed_count

        st.session_state[
            "attention_required"
        ] = attention_count

        # Save permanent snapshot to Supabase.
        try:

            save_operational_snapshot(
                "Voyage Operations",
                voyage_df.to_dict(
                    orient="records"
                ),
                {
                    "records": len(
                        voyage_df
                    ),
                    "delayed": (
                        delayed_count
                    ),
                    "attention": (
                        attention_count
                    ),
                },
            )

        except Exception as e:

            st.error(
                "Voyage database save error: "
                f"{e}"
            )

        st.markdown(
            "### 📊 Voyage Intelligence"
        )

        col1, col2, col3 = st.columns(
            3
        )

        with col1:

            st.metric(
                "Voyage Records",
                len(voyage_df),
            )

        with col2:

            st.metric(
                "Delayed / Exception",
                delayed_count,
            )

        with col3:

            st.metric(
                "Attention Required",
                attention_count,
            )

        st.markdown(
            "### 📋 Voyage Records"
        )

        st.dataframe(
            voyage_df,
            use_container_width=True,
            hide_index=True,
        )

        if delayed_count > 0:

            st.markdown(
                "### ⚠️ Delayed / Exception"
            )

            st.dataframe(
                voyage_df[
                    delayed_mask
                ],
                use_container_width=True,
                hide_index=True,
            )

        if attention_count > 0:

            st.markdown(
                "### 🚨 Attention Required"
            )

            st.dataframe(
                voyage_df[
                    attention_mask
                ],
                use_container_width=True,
                hide_index=True,
            )

        st.markdown(
            "### 🧠 Voyage Operations Analysis"
        )

        if st.button(
            "ANALYZE VOYAGE",
            type="primary",
            key="analyze_voyage",
        ):

            voyage_context = (
                voyage_df.to_csv(
                    index=False
                )
            )

            voyage_prompt = f"""
USER REQUEST:
Analyze supplied Voyage Operations data
for marine fleet operations.

VOYAGE DATA:
{voyage_context}

VOYAGE INTELLIGENCE RULES:

1. Analyze ONLY the supplied voyage data.

2. NEVER invent:
- vessel status
- voyage number
- origin
- destination
- ETD
- ETA
- delay
- weather condition
- port condition
- vessel condition
- voyage progress

3. Identify delay or operational exception
only when explicitly supported by the supplied data.

4. If required information is missing, state:
DATA BELUM TERSEDIA.

5. Do not assume ETA, ETD or voyage progress.

6. Clearly separate the assessment into:

FACTS

DATA GAPS

VOYAGE RISK

OPERATIONAL EXCEPTIONS

PRIORITY ACTIONS

7. Prioritize:
- safety
- operational continuity
- voyage execution
- compliance

8. Do not make assumptions beyond supplied data.

9. For every identified exception, use only
evidence available in the supplied dataset.
"""

            try:

                with st.spinner(
                    "Gemini sedang menganalisis "
                    "Voyage Operations..."
                ):

                    voyage_answer = (
                        ask_gemini_marine_copilot(
                            voyage_prompt,
                            st.session_state.get(
                                "role",
                                "Marine Superintendent",
                            ),
                        )
                    )

                st.markdown(
                    "### 🧠 Voyage Intelligence Assessment"
                )

                st.markdown(
                    voyage_answer
                )

            except Exception as e:

                error_text = str(e)

                if (
                    "429" in error_text
                    or
                    "RESOURCE_EXHAUSTED"
                    in error_text
                ):

                    st.warning(
                        "Data Voyage berhasil dimuat, "
                        "tetapi Gemini sedang mencapai "
                        "batas quota."
                    )

                elif (
                    "503" in error_text
                    or
                    "UNAVAILABLE"
                    in error_text
                ):

                    st.warning(
                        "Data Voyage berhasil dimuat, "
                        "tetapi Gemini sedang mengalami "
                        "high demand."
                    )

                else:

                    st.error(
                        "Gagal melakukan analisis "
                        f"Voyage: {e}"
                    )


# ============================================================
# HSSE / DPA
# ============================================================

elif menu == "HSSE / DPA":

    st.header(
        "🛡️ HSSE / DPA Intelligence"
    )

    st.caption(
        "HSSE Intelligence menganalisis Incident, "
        "Near Miss, Finding dan Safety Observation "
        "yang tersedia."
    )

    uploaded_hsse = st.file_uploader(
        "Upload HSSE / DPA Data (CSV)",
        type=["csv"],
        key="hsse_upload",
    )

    hsse_df = pd.DataFrame()

    if uploaded_hsse is None:

        snapshots = (
            load_operational_snapshots()
        )

        saved_hsse = snapshots.get(
            "HSSE / DPA",
            {}
        )

        saved_records = saved_hsse.get(
            "records",
            []
        )

        if (
            isinstance(saved_records, list)
            and saved_records
        ):

            hsse_df = pd.DataFrame(
                saved_records
            )

            st.success(
                "HSSE data terakhir berhasil "
                "dimuat dari database Supabase."
            )

        else:

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

            st.warning(
                "DATA BELUM TERSEDIA — "
                "belum ada HSSE / DPA data."
            )

            st.info(
                """
Format CSV yang disarankan:

vessel,event_date,event_type,severity,status,remarks

event_type:
Incident / Near Miss / Finding / Safety Observation

severity:
Critical / High / Medium / Low

status:
Open / Closed / Under Investigation
                """
            )

    else:

        try:

            hsse_df = pd.read_csv(
                uploaded_hsse
            )

        except Exception as e:

            st.error(
                f"Gagal membaca file HSSE / CSV: {e}"
            )

    if not hsse_df.empty:

        open_findings_count = 0
        incident_count = 0
        near_miss_count = 0
        critical_count = 0

        if "status" in hsse_df.columns:

            status_text = (
                hsse_df["status"]
                .astype(str)
                .str.strip()
                .str.lower()
            )

            open_findings_count = int(
                status_text.isin(
                    [
                        "open",
                        "under investigation",
                        "in progress",
                    ]
                ).sum()
            )

        if "event_type" in hsse_df.columns:

            event_text = (
                hsse_df["event_type"]
                .astype(str)
                .str.strip()
                .str.lower()
            )

            incident_count = int(
                (
                    event_text
                    == "incident"
                ).sum()
            )

            near_miss_count = int(
                (
                    event_text
                    == "near miss"
                ).sum()
            )

        if "severity" in hsse_df.columns:

            severity_text = (
                hsse_df["severity"]
                .astype(str)
                .str.strip()
                .str.lower()
            )

            critical_count = int(
                (
                    severity_text
                    == "critical"
                ).sum()
            )

        st.session_state[
            "hsse_findings"
        ] = open_findings_count

        try:

            save_operational_snapshot(
                "HSSE / DPA",
                hsse_df.to_dict(
                    orient="records"
                ),
                {
                    "records": len(
                        hsse_df
                    ),
                    "incidents": (
                        incident_count
                    ),
                    "near_miss": (
                        near_miss_count
                    ),
                    "open_findings": (
                        open_findings_count
                    ),
                    "critical": (
                        critical_count
                    ),
                },
            )

        except Exception as e:

            st.error(
                "HSSE database save error: "
                f"{e}"
            )

        st.markdown(
            "### 📊 HSSE Summary"
        )

        c1, c2, c3, c4 = st.columns(
            4
        )

        with c1:

            st.metric(
                "HSSE Records",
                len(hsse_df)
            )

        with c2:

            st.metric(
                "Incidents",
                incident_count
            )

        with c3:

            st.metric(
                "Near Miss",
                near_miss_count
            )

        with c4:

            st.metric(
                "Open Findings",
                open_findings_count
            )

        if critical_count > 0:

            st.warning(
                f"{critical_count} Critical HSSE "
                "record(s) terdeteksi."
            )

        st.subheader(
            "HSSE / DPA Records"
        )

        st.dataframe(
            hsse_df,
            use_container_width=True,
            hide_index=True,
        )

        st.subheader(
            "HSSE Intelligence"
        )

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
- NEVER invent incidents, near misses,
  findings, dates, severity, vessel condition
  or corrective actions.
- If required information is missing, state:
  DATA BELUM TERSEDIA.
- Identify critical safety risks only when
  the supplied data supports the assessment.
- Identify open findings only from supplied status.
- Prioritize safety and regulatory compliance.

Clearly separate:

FACTS

DATA GAPS

HSSE RISK

PRIORITY ACTIONS

ESCALATION REQUIRED
"""

            try:

                with st.spinner(
                    "Gemini sedang "
                    "menganalisis HSSE..."
                ):

                    hsse_answer = (
                        ask_gemini_marine_copilot(
                            hsse_prompt,
                            st.session_state.get(
                                "role",
                                "Marine Superintendent",
                            ),
                        )
                    )

                st.markdown(
                    "### HSSE / DPA "
                    "Intelligence Assessment"
                )

                st.markdown(
                    hsse_answer
                )

            except Exception as e:

                st.error(
                    "Gagal menganalisis "
                    f"HSSE: {e}"
                )
                # ============================================================
# PMS / MAINTENANCE
# ============================================================

elif menu == "PMS / Maintenance":

    st.header("🔧 PMS / Maintenance Intelligence")

    st.caption(
        "PMS Intelligence menganalisis data maintenance yang tersedia. "
        "Sistem tidak membuat atau mengasumsikan data maintenance."
    )

    uploaded_pms = st.file_uploader(
        "Upload PMS / Maintenance Data (CSV)",
        type=["csv"],
        key="pms_upload",
    )

    pms_df = pd.DataFrame()

    if uploaded_pms is not None:

        try:
            pms_df = pd.read_csv(uploaded_pms)

        except Exception as e:
            st.error(
                f"Gagal membaca PMS data: {e}"
            )

    else:

        saved_pms = load_operational_snapshots().get(
            "PMS / Maintenance",
            {}
        )

        saved_records = saved_pms.get(
            "records",
            []
        )

        if isinstance(saved_records, list) and saved_records:

            pms_df = pd.DataFrame(saved_records)

            st.success(
                "PMS data terakhir berhasil "
                "dimuat dari database Supabase."
            )

    if pms_df.empty:

        st.metric(
            "Maintenance Records",
            "0"
        )

        st.warning(
            "DATA BELUM TERSEDIA — "
            "belum ada PMS / Maintenance data."
        )

        st.info(
            """
Format CSV:

vessel,maintenance_task,due_date,status,priority,remarks

Status:
Planned / Due / Overdue / Completed

Priority:
Critical / High / Medium / Low
            """
        )

    else:

        required_pms_columns = [
            "vessel",
            "maintenance_task",
            "due_date",
            "status",
            "priority",
            "remarks",
        ]

        missing_columns = [
            column
            for column in required_pms_columns
            if column not in pms_df.columns
        ]

        if missing_columns:

            st.error(
                "Kolom PMS wajib belum lengkap: "
                + ", ".join(missing_columns)
            )

        else:

            analysis_pms = pms_df.copy()

            analysis_pms["due_date"] = pd.to_datetime(
                analysis_pms["due_date"],
                errors="coerce",
            )

            status_text = (
                analysis_pms["status"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.lower()
            )

            priority_text = (
                analysis_pms["priority"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.lower()
            )

            today = pd.Timestamp(
                datetime.now().date()
            )

            overdue_mask = (
                (
                    status_text == "overdue"
                )
                |
                (
                    analysis_pms["due_date"].notna()
                    & (
                        analysis_pms["due_date"]
                        < today
                    )
                    & (
                        status_text != "completed"
                    )
                )
            )

            due_mask = (
                status_text == "due"
            )

            critical_mask = (
                priority_text == "critical"
            ) & (
                status_text != "completed"
            )

            high_mask = (
                priority_text == "high"
            ) & (
                status_text != "completed"
            )

            overdue_count = int(
                overdue_mask.sum()
            )

            due_count = int(
                due_mask.sum()
            )

            critical_count = int(
                critical_mask.sum()
            )

            high_count = int(
                high_mask.sum()
            )

            st.session_state[
                "pms_records"
            ] = len(analysis_pms)

            try:

                save_operational_snapshot(
                    "PMS / Maintenance",
                    analysis_pms.to_dict(
                        orient="records"
                    ),
                    {
                        "records": len(
                            analysis_pms
                        ),
                        "overdue": overdue_count,
                        "due": due_count,
                        "critical": critical_count,
                        "high": high_count,
                    },
                )

            except Exception as e:

                st.error(
                    "PMS database save error: "
                    f"{e}"
                )

            st.markdown(
                "### 📊 PMS Summary"
            )

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.metric(
                    "Maintenance Records",
                    len(analysis_pms),
                )

            with c2:
                st.metric(
                    "Overdue",
                    overdue_count,
                )

            with c3:
                st.metric(
                    "Due",
                    due_count,
                )

            with c4:
                st.metric(
                    "Critical",
                    critical_count,
                )

            st.subheader(
                "PMS / Maintenance Records"
            )

            st.dataframe(
                analysis_pms,
                use_container_width=True,
                hide_index=True,
            )

            st.markdown(
                "### ⚠️ Maintenance Risk"
            )

            risk_df = analysis_pms[
                overdue_mask
                | critical_mask
                | high_mask
            ]

            if risk_df.empty:

                st.success(
                    "Tidak terdapat maintenance "
                    "risk prioritas berdasarkan "
                    "data yang tersedia."
                )

            else:

                st.dataframe(
                    risk_df,
                    use_container_width=True,
                    hide_index=True,
                )

            st.markdown(
                "### 🎯 Priority Actions"
            )

            if overdue_count > 0:

                st.warning(
                    f"{overdue_count} maintenance "
                    "task overdue membutuhkan "
                    "follow-up."
                )

            elif critical_count > 0:

                st.warning(
                    f"{critical_count} Critical "
                    "maintenance task membutuhkan "
                    "perhatian."
                )

            elif due_count > 0:

                st.info(
                    f"{due_count} maintenance task "
                    "berstatus Due."
                )

            else:

                st.success(
                    "Tidak terdapat PMS priority "
                    "action berdasarkan data "
                    "yang tersedia."
                )

            st.markdown(
                "### 🧠 PMS Intelligence"
            )

            if st.button(
                "ANALYZE PMS",
                type="primary",
                key="analyze_pms",
            ):

                pms_context = json.dumps(
                    analysis_pms.to_dict(
                        orient="records"
                    ),
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )

                pms_prompt = f"""
Analyze ONLY the supplied PMS / Maintenance data.

PMS DATA:
{pms_context}

RULES:
- NEVER invent maintenance records.
- NEVER invent running hours.
- NEVER invent equipment condition.
- NEVER invent completion evidence.
- If information is missing, state:
  DATA BELUM TERSEDIA.

Return ALL sections:

FACTS

DATA GAPS

MAINTENANCE RISK

PRIORITY ACTIONS
"""

                with st.spinner(
                    "Gemini sedang "
                    "menganalisis PMS..."
                ):

                    pms_answer = (
                        ask_gemini_marine_copilot(
                            pms_prompt,
                            st.session_state.get(
                                "role",
                                "Marine Superintendent",
                            ),
                        )
                    )

                st.markdown(
                    "### PMS Maintenance "
                    "Intelligence Analysis"
                )

                st.markdown(pms_answer)


# ============================================================
# DEFECTS
# ============================================================

elif menu == "Defects":

    st.header("⚠️ Defect Intelligence")

    st.caption(
        "Defect Intelligence menganalisis defect "
        "berdasarkan data yang tersedia."
    )

    uploaded_defects = st.file_uploader(
        "Upload Defect Data (CSV)",
        type=["csv"],
        key="defects_upload",
    )

    defect_df = pd.DataFrame()

    if uploaded_defects is not None:

        try:
            defect_df = pd.read_csv(
                uploaded_defects
            )

        except Exception as e:

            st.error(
                f"Gagal membaca Defect data: {e}"
            )

    else:

        saved_defects = (
            load_operational_snapshots()
            .get(
                "Defects",
                {}
            )
        )

        saved_records = saved_defects.get(
            "records",
            []
        )

        if (
            isinstance(saved_records, list)
            and saved_records
        ):

            defect_df = pd.DataFrame(
                saved_records
            )

            st.success(
                "Defect data terakhir berhasil "
                "dimuat dari database Supabase."
            )

    if defect_df.empty:

        st.metric(
            "Defect Records",
            "0"
        )

        st.warning(
            "DATA BELUM TERSEDIA — "
            "belum ada defect data."
        )

        st.info(
            """
Format CSV:

vessel,defect,severity,reported,due_date,status,responsible

Severity:
Critical / High / Medium / Low

Status:
Open / In Progress / Closed
            """
        )

    else:

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
            column
            for column in required_columns
            if column not in defect_df.columns
        ]

        if missing_columns:

            st.error(
                "Kolom Defect wajib belum lengkap: "
                + ", ".join(missing_columns)
            )

        else:

            analysis_df = defect_df.copy()

            analysis_df["due_date"] = (
                pd.to_datetime(
                    analysis_df["due_date"],
                    errors="coerce",
                )
            )

            status_text = (
                analysis_df["status"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.lower()
            )

            severity_text = (
                analysis_df["severity"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.lower()
            )

            today = pd.Timestamp(
                datetime.now().date()
            )

            open_mask = status_text.isin(
                [
                    "open",
                    "in progress",
                ]
            )

            overdue_mask = (
                analysis_df["due_date"].notna()
                & (
                    analysis_df["due_date"]
                    < today
                )
                & (
                    status_text != "closed"
                )
            )

            critical_mask = (
                severity_text == "critical"
            ) & (
                status_text != "closed"
            )

            high_mask = (
                severity_text == "high"
            ) & (
                status_text != "closed"
            )

            open_count = int(
                open_mask.sum()
            )

            overdue_count = int(
                overdue_mask.sum()
            )

            critical_count = int(
                critical_mask.sum()
            )

            high_count = int(
                high_mask.sum()
            )

            st.session_state[
                "open_defects"
            ] = open_count

            try:

                save_operational_snapshot(
                    "Defects",
                    analysis_df.to_dict(
                        orient="records"
                    ),
                    {
                        "records": len(
                            analysis_df
                        ),
                        "open": open_count,
                        "overdue": overdue_count,
                        "critical": critical_count,
                        "high": high_count,
                    },
                )

            except Exception as e:

                st.error(
                    "Defect database save error: "
                    f"{e}"
                )

            st.markdown(
                "### 📊 Defect Summary"
            )

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.metric(
                    "Total Defects",
                    len(analysis_df),
                )

            with c2:
                st.metric(
                    "Open / In Progress",
                    open_count,
                )

            with c3:
                st.metric(
                    "Overdue",
                    overdue_count,
                )

            with c4:
                st.metric(
                    "Critical",
                    critical_count,
                )

            st.subheader(
                "Defect Records"
            )

            st.dataframe(
                analysis_df,
                use_container_width=True,
                hide_index=True,
            )

            st.markdown(
                "### 🔴 Critical Defects"
            )

            critical_df = analysis_df[
                critical_mask
            ]

            if critical_df.empty:

                st.info(
                    "Tidak ada Critical Defect aktif."
                )

            else:

                st.dataframe(
                    critical_df,
                    use_container_width=True,
                    hide_index=True,
                )

            st.markdown(
                "### ⏰ Overdue Defects"
            )

            overdue_df = analysis_df[
                overdue_mask
            ]

            if overdue_df.empty:

                st.info(
                    "Tidak ada Overdue Defect aktif."
                )

            else:

                st.dataframe(
                    overdue_df,
                    use_container_width=True,
                    hide_index=True,
                )

            st.markdown(
                "### Defect Intelligence Assessment"
            )

            st.markdown(
                f"""
**FACTS**

- Total defect records: **{len(analysis_df)}**
- Open / In Progress: **{open_count}**
- Overdue active defects: **{overdue_count}**
- Critical active defects: **{critical_count}**
- High severity active defects: **{high_count}**

**DATA GAPS**

Informasi teknis yang tidak terdapat pada
dataset tidak akan diasumsikan oleh sistem.

**PRIORITY ACTIONS**

Prioritaskan Critical dan Overdue Defects
berdasarkan data yang tersedia.
"""
            )


# ============================================================
# CERTIFICATES
# ============================================================

elif menu == "Certificates":

    st.header(
        "📜 Certificate Intelligence"
    )

    st.caption(
        "Certificate Intelligence menganalisis "
        "expiry dan compliance berdasarkan "
        "data yang tersedia."
    )

    uploaded_certificates = st.file_uploader(
        "Upload Certificate Data (CSV)",
        type=["csv"],
        key="certificates_upload",
    )

    certificates_df = pd.DataFrame()

    if uploaded_certificates is not None:

        try:

            certificates_df = pd.read_csv(
                uploaded_certificates
            )

        except Exception as e:

            st.error(
                "Gagal membaca Certificate "
                f"data: {e}"
            )

    else:

        saved_certificates = (
            load_operational_snapshots()
            .get(
                "Certificates",
                {}
            )
        )

        saved_records = (
            saved_certificates.get(
                "records",
                []
            )
        )

        if (
            isinstance(saved_records, list)
            and saved_records
        ):

            certificates_df = pd.DataFrame(
                saved_records
            )

            st.success(
                "Certificate data terakhir "
                "berhasil dimuat dari "
                "database Supabase."
            )

    if certificates_df.empty:

        st.metric(
            "Certificate Records",
            "0"
        )

        st.warning(
            "DATA BELUM TERSEDIA — "
            "belum ada certificate data."
        )

        st.info(
            """
Format CSV:

vessel,certificate,certificate_type,issue_date,expiry_date,status,remarks

certificate_type:
Statutory / Class / Flag / Operational

status:
Valid / Expired / Suspended
            """
        )

    else:

        required_certificate_columns = [
            "vessel",
            "certificate",
            "certificate_type",
            "issue_date",
            "expiry_date",
            "status",
            "remarks",
        ]

        missing_columns = [
            column
            for column
            in required_certificate_columns
            if column
            not in certificates_df.columns
        ]

        if missing_columns:

            st.error(
                "Kolom Certificate wajib "
                "belum lengkap: "
                + ", ".join(
                    missing_columns
                )
            )

        else:

            analysis_cert = (
                certificates_df.copy()
            )

            analysis_cert[
                "expiry_date"
            ] = pd.to_datetime(
                analysis_cert["expiry_date"],
                errors="coerce",
            )

            today = pd.Timestamp.today().normalize()

            analysis_cert[
                "days_to_expiry"
            ] = (
                analysis_cert["expiry_date"]
                - today
            ).dt.days

            expired_mask = (
                analysis_cert[
                    "days_to_expiry"
                ] < 0
            )

            expiring_mask = (
                analysis_cert[
                    "days_to_expiry"
                ].between(
                    0,
                    30,
                    inclusive="both",
                )
            )

            expired_count = int(
                expired_mask.sum()
            )

            expiring_count = int(
                expiring_mask.sum()
            )

            st.session_state[
                "certificate_records"
            ] = len(
                analysis_cert
            )

            try:

                save_operational_snapshot(
                    "Certificates",
                    analysis_cert.to_dict(
                        orient="records"
                    ),
                    {
                        "records": len(
                            analysis_cert
                        ),
                        "expired": (
                            expired_count
                        ),
                        "expiring_30d": (
                            expiring_count
                        ),
                    },
                )

            except Exception as e:

                st.error(
                    "Certificate database "
                    f"save error: {e}"
                )

            st.markdown(
                "### 📊 Certificate Summary"
            )

            c1, c2, c3 = st.columns(3)

            with c1:

                st.metric(
                    "Certificate Records",
                    len(analysis_cert),
                )

            with c2:

                st.metric(
                    "Expired",
                    expired_count,
                )

            with c3:

                st.metric(
                    "Expiring ≤ 30 Days",
                    expiring_count,
                )

            st.subheader(
                "Certificate Records"
            )

            st.dataframe(
                analysis_cert,
                use_container_width=True,
                hide_index=True,
            )

            if expired_count > 0:

                st.markdown(
                    "### 🔴 Expired Certificates"
                )

                st.dataframe(
                    analysis_cert[
                        expired_mask
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

            if expiring_count > 0:

                st.markdown(
                    "### 🟠 Certificates "
                    "Expiring ≤ 30 Days"
                )

                st.dataframe(
                    analysis_cert[
                        expiring_mask
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

            if st.button(
                "ANALYZE CERTIFICATES",
                type="primary",
                key="analyze_certificates",
            ):

                certificate_context = (
                    json.dumps(
                        analysis_cert.to_dict(
                            orient="records"
                        ),
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                    )
                )

                certificate_prompt = f"""
Analyze ONLY the supplied vessel
certificate data.

CERTIFICATE DATA:
{certificate_context}

RULES:
- NEVER invent certificates.
- NEVER invent expiry dates.
- Identify expired certificates only
  from supplied data.
- Identify certificates expiring within
  30 days only from supplied data.
- If required information is missing:
  DATA BELUM TERSEDIA.

Return:

FACTS

EXPIRY RISK

COMPLIANCE RISK

DATA GAPS

PRIORITY ACTIONS
"""

                with st.spinner(
                    "Gemini sedang menganalisis "
                    "Certificates..."
                ):

                    certificate_answer = (
                        ask_gemini_marine_copilot(
                            certificate_prompt,
                            st.session_state.get(
                                "role",
                                "Marine Superintendent",
                            ),
                        )
                    )

                st.markdown(
                    "### Certificate "
                    "Intelligence Assessment"
                )

                st.markdown(
                    certificate_answer
                )
                # ============================================================
# BUNKER
# ============================================================

elif menu == "Bunker":

    st.header("⛽ Bunker Intelligence")

    st.caption(
        "Bunker Intelligence menggunakan data aktual yang tersedia. "
        "Sistem tidak mengarang quantity, ROB atau consumption."
    )

    uploaded_bunker = st.file_uploader(
        "Upload Bunker Data (CSV)",
        type=["csv"],
        key="bunker_upload",
    )

    bunker_df = pd.DataFrame()

    if uploaded_bunker is not None:

        try:
            bunker_df = pd.read_csv(
                uploaded_bunker
            )

        except Exception as e:
            st.error(
                f"Gagal membaca Bunker data: {e}"
            )

    else:

        saved_bunker = (
            load_operational_snapshots()
            .get(
                "Bunker",
                {}
            )
        )

        saved_records = saved_bunker.get(
            "records",
            []
        )

        if (
            isinstance(saved_records, list)
            and saved_records
        ):

            bunker_df = pd.DataFrame(
                saved_records
            )

            st.success(
                "Bunker data terakhir berhasil "
                "dimuat dari database Supabase."
            )

    if bunker_df.empty:

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric(
                "Vessels",
                21
            )

        with c2:
            st.metric(
                "Bunker Reports",
                0
            )

        with c3:
            st.metric(
                "Consumption Alerts",
                0
            )

        st.warning(
            "DATA BELUM TERSEDIA — "
            "belum ada Bunker data."
        )

        st.info(
            """
Format CSV:

vessel,date,fuel_type,quantity_mt,rob_mt,consumption_mt_day,remarks

fuel_type:
MGO / HFO / VLSFO
            """
        )

    else:

        alert_count = 0

        if "remarks" in bunker_df.columns:

            alert_mask = (
                bunker_df["remarks"]
                .fillna("")
                .astype(str)
                .str.contains(
                    r"alert|low|high consumption|abnormal|shortage",
                    case=False,
                    regex=True,
                    na=False,
                )
            )

            alert_count = int(
                alert_mask.sum()
            )

        elif (
            "consumption_mt_day"
            in bunker_df.columns
        ):

            consumption = pd.to_numeric(
                bunker_df[
                    "consumption_mt_day"
                ],
                errors="coerce",
            )

            if consumption.notna().any():

                average_consumption = (
                    consumption.mean()
                )

                alert_count = int(
                    (
                        consumption
                        > average_consumption * 1.20
                    ).sum()
                )

        try:

            save_operational_snapshot(
                "Bunker",
                bunker_df.to_dict(
                    orient="records"
                ),
                {
                    "records": len(
                        bunker_df
                    ),
                    "alerts": alert_count,
                },
            )

        except Exception as e:

            st.error(
                "Bunker database save error: "
                f"{e}"
            )

        st.markdown(
            "### 📊 Bunker Summary"
        )

        c1, c2 = st.columns(2)

        with c1:

            st.metric(
                "Bunker Reports",
                len(bunker_df)
            )

        with c2:

            st.metric(
                "Consumption Alerts",
                alert_count
            )

        st.subheader(
            "Bunker Records"
        )

        st.dataframe(
            bunker_df,
            use_container_width=True,
            hide_index=True,
        )

        if alert_count > 0:

            st.warning(
                f"{alert_count} bunker record "
                "memerlukan operational review."
            )

        st.markdown(
            "### 🧠 Bunker Intelligence"
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
Analyze ONLY the supplied Bunker data.

BUNKER DATA:
{bunker_context}

RULES:
- NEVER invent fuel quantity.
- NEVER invent ROB.
- NEVER invent consumption.
- NEVER invent bunker delivery.
- NEVER invent bunker price.
- NEVER invent fuel shortage.
- Identify abnormal consumption ONLY when the supplied data supports it.
- Use only evidence contained in BUNKER DATA.
- If information is missing, write exactly:
  DATA BELUM TERSEDIA.
- Do not stop after FACTS.
- You MUST return ALL five sections below.
- Every section heading MUST appear in the final answer.
- If a section has no supported issue, write:
  Tidak ada temuan berdasarkan data yang tersedia.
- Be concise and operational.

Return EXACTLY in this structure:

## FACTS
Summarize the bunker facts supported by the dataset.

## DATA GAPS
List unavailable or incomplete bunker information.
If none can be identified, write:
DATA BELUM TERSEDIA.

## BUNKER RISK
Identify bunker operational risks supported by the supplied data.
If no risk is supported, write:
Tidak ada temuan berdasarkan data yang tersedia.

## CONSUMPTION ALERTS
List vessels with abnormal or high consumption ONLY when supported by the data.
If none, write:
Tidak ada temuan berdasarkan data yang tersedia.

## PRIORITY ACTIONS
Give practical follow-up actions based ONLY on the supplied data.
If no action is required, write:
Tidak ada tindakan prioritas berdasarkan data yang tersedia.
"""

            with st.spinner(
                "Gemini sedang menganalisis "
                "Bunker..."
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


# ============================================================
# CARGO
# ============================================================

elif menu == "Cargo":

    st.header(
        "📦 Cargo Operations Intelligence"
    )

    st.caption(
        "Cargo Intelligence menggunakan data cargo "
        "yang tersedia dan tidak membuat asumsi "
        "terhadap quantity, delay atau condition."
    )

    uploaded_cargo = st.file_uploader(
        "Upload Cargo Data (CSV)",
        type=["csv"],
        key="cargo_upload",
    )

    cargo_df = pd.DataFrame()

    if uploaded_cargo is not None:

        try:

            cargo_df = pd.read_csv(
                uploaded_cargo
            )

        except Exception as e:

            st.error(
                f"Gagal membaca Cargo data: {e}"
            )

    else:

        saved_cargo = (
            load_operational_snapshots()
            .get(
                "Cargo",
                {}
            )
        )

        saved_records = saved_cargo.get(
            "records",
            []
        )

        if (
            isinstance(saved_records, list)
            and saved_records
        ):

            cargo_df = pd.DataFrame(
                saved_records
            )

            st.success(
                "Cargo data terakhir berhasil "
                "dimuat dari database Supabase."
            )

    if cargo_df.empty:

        st.warning(
            "DATA BELUM TERSEDIA — "
            "belum ada Cargo data."
        )

        st.info(
            """
Format CSV:

vessel,cargo_date,cargo_type,quantity_mt,origin,destination,status,remarks
            """
        )

    else:

        total_cargo = len(
            cargo_df
        )

        delayed_cargo = 0
        attention_cargo = 0

        if "status" in cargo_df.columns:

            delayed_mask = (
                cargo_df["status"]
                .fillna("")
                .astype(str)
                .str.contains(
                    r"delayed|delay|hold",
                    case=False,
                    regex=True,
                    na=False,
                )
            )

            delayed_cargo = int(
                delayed_mask.sum()
            )

        if "remarks" in cargo_df.columns:

            attention_mask = (
                cargo_df["remarks"]
                .fillna("")
                .astype(str)
                .str.contains(
                    r"delay|delayed|shortage|damage|risk|abnormal|hold",
                    case=False,
                    regex=True,
                    na=False,
                )
            )

            attention_cargo = int(
                attention_mask.sum()
            )

        try:

            save_operational_snapshot(
                "Cargo",
                cargo_df.to_dict(
                    orient="records"
                ),
                {
                    "records": total_cargo,
                    "delayed": delayed_cargo,
                    "attention": attention_cargo,
                },
            )

        except Exception as e:

            st.error(
                "Cargo database save error: "
                f"{e}"
            )

        st.session_state[
            "cargo_records"
        ] = total_cargo

        st.markdown(
            "### 📊 Cargo Summary"
        )

        c1, c2, c3 = st.columns(
            3
        )

        with c1:

            st.metric(
                "Cargo Records",
                total_cargo
            )

        with c2:

            st.metric(
                "Delayed Cargo",
                delayed_cargo
            )

        with c3:

            st.metric(
                "Attention Required",
                attention_cargo
            )

        st.subheader(
            "📋 Cargo Records"
        )

        st.dataframe(
            cargo_df,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown(
            "### 🧠 Cargo Intelligence"
        )

        if st.button(
            "ANALYZE CARGO",
            type="primary",
            key="analyze_cargo",
        ):

            cargo_context = json.dumps(
                cargo_df.to_dict(
                    orient="records"
                ),
                ensure_ascii=False,
                indent=2,
                default=str,
            )

            cargo_prompt = f"""
Analyze ONLY the supplied Cargo data.

CARGO DATA:
{cargo_context}

RULES:

- NEVER invent cargo quantity.
- NEVER invent cargo type.
- NEVER invent cargo condition.
- NEVER invent delay.
- NEVER invent damage.
- NEVER invent shortage.
- NEVER invent ETA / ETD.
- If required information is missing:
  DATA BELUM TERSEDIA.

Return:

FACTS

DATA GAPS

CARGO RISK

OPERATIONAL EXCEPTIONS

PRIORITY ACTIONS
"""

            with st.spinner(
                "Gemini sedang "
                "menganalisis Cargo..."
            ):

                cargo_answer = (
                    ask_gemini_marine_copilot(
                        cargo_prompt,
                        st.session_state.get(
                            "role",
                            "Marine Superintendent",
                        ),
                    )
                )

            st.markdown(
                "### Cargo Intelligence Assessment"
            )

            st.markdown(
                cargo_answer
            )


# ============================================================
# AUDIT & FINDINGS
# ============================================================

elif menu == "Audit & Findings":

    st.header(
        "🔍 Audit & Findings Intelligence"
    )

    st.caption(
        "Audit, inspection, observation, "
        "non-conformity dan corrective action monitoring."
    )

    uploaded_audit = st.file_uploader(
        "Upload Audit & Findings Data (CSV)",
        type=["csv"],
        key="audit_upload",
    )

    audit_df = pd.DataFrame()

    if uploaded_audit is not None:

        try:

            audit_df = pd.read_csv(
                uploaded_audit
            )

        except Exception as e:

            st.error(
                "Gagal membaca Audit & Findings "
                f"data: {e}"
            )

    else:

        saved_audit = (
            load_operational_snapshots()
            .get(
                "Audit & Findings",
                {}
            )
        )

        saved_records = saved_audit.get(
            "records",
            []
        )

        if (
            isinstance(saved_records, list)
            and saved_records
        ):

            audit_df = pd.DataFrame(
                saved_records
            )

            st.success(
                "Audit data terakhir berhasil "
                "dimuat dari database Supabase."
            )

    if audit_df.empty:

        st.warning(
            "DATA BELUM TERSEDIA — "
            "belum ada Audit & Findings data."
        )

        st.info(
            """
Format CSV:

finding_id,vessel,audit_type,finding,severity,status,due_date,responsible,remarks

Severity:
Critical / High / Medium / Low

Status:
Open / In Progress / Closed
            """
        )

    else:

        required_audit_columns = [
            "finding_id",
            "vessel",
            "audit_type",
            "finding",
            "severity",
            "status",
            "due_date",
            "responsible",
            "remarks",
        ]

        for column in required_audit_columns:

            if column not in audit_df.columns:
                audit_df[column] = ""

        status_text = (
            audit_df["status"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

        severity_text = (
            audit_df["severity"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

        open_mask = status_text.isin(
            [
                "open",
                "in progress",
            ]
        )

        critical_mask = (
            severity_text == "critical"
        ) & open_mask

        high_mask = (
            severity_text == "high"
        ) & open_mask

        open_count = int(
            open_mask.sum()
        )

        critical_count = int(
            critical_mask.sum()
        )

        high_count = int(
            high_mask.sum()
        )

        try:

            save_operational_snapshot(
                "Audit & Findings",
                audit_df.to_dict(
                    orient="records"
                ),
                {
                    "records": len(
                        audit_df
                    ),
                    "open": open_count,
                    "critical": critical_count,
                    "high": high_count,
                },
            )

        except Exception as e:

            st.error(
                "Audit database save error: "
                f"{e}"
            )

        st.markdown(
            "### 📊 Audit Summary"
        )

        c1, c2, c3, c4 = st.columns(
            4
        )

        with c1:

            st.metric(
                "Audit / Findings Records",
                len(audit_df)
            )

        with c2:

            st.metric(
                "Open Findings",
                open_count
            )

        with c3:

            st.metric(
                "Critical",
                critical_count
            )

        with c4:

            st.metric(
                "High",
                high_count
            )

        st.subheader(
            "Audit & Finding Records"
        )

        st.dataframe(
            audit_df,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown(
            "### ➕ Create Action From Finding"
        )

        finding_options = []

        for index, row in audit_df.iterrows():

            finding_id = str(
                row.get(
                    "finding_id",
                    "",
                )
            ).strip()

            finding = str(
                row.get(
                    "finding",
                    "",
                )
            ).strip()

            label = (
                f"{finding_id} — {finding}"
                if finding_id
                else f"Finding {index + 1} — {finding}"
            )

            finding_options.append(
                (
                    label,
                    index,
                )
            )

        selected_finding_label = (
            st.selectbox(
                "Select Finding",
                [
                    item[0]
                    for item in finding_options
                ],
                key="audit_selected_finding",
            )
        )

        selected_finding_index = next(
            item[1]
            for item in finding_options
            if item[0]
            == selected_finding_label
        )

        selected_finding = (
            audit_df.loc[
                selected_finding_index
            ]
        )

        if st.button(
            "CREATE ACTION FROM FINDING",
            type="primary",
            key="audit_create_action",
        ):

            current_actions = load_actions()

            audit_action = {
                "Action ID": (
                    next_action_id(
                        current_actions
                    )
                ),
                "Vessel": str(
                    selected_finding.get(
                        "vessel",
                        "All Fleet",
                    )
                ),
                "Source": (
                    "Audit & Findings"
                ),
                "Description": str(
                    selected_finding.get(
                        "finding",
                        "",
                    )
                ),
                "Priority": (
                    str(
                        selected_finding.get(
                            "severity",
                            "Medium",
                        )
                    ).title()
                ),
                "Responsible": str(
                    selected_finding.get(
                        "responsible",
                        "",
                    )
                ),
                "Due Date": str(
                    selected_finding.get(
                        "due_date",
                        "",
                    )
                )[:10],
                "Status": "Open",
                "Remarks": (
                    "Created from Audit Finding "
                    + str(
                        selected_finding.get(
                            "finding_id",
                            "",
                        )
                    )
                ),
                "Created": (
                    datetime.now()
                    .isoformat()
                ),
                "Updated": (
                    datetime.now()
                    .isoformat()
                ),
                "Completed": "",
                "Created By": "admin",
                "Role": (
                    st.session_state.get(
                        "role",
                        "Marine Superintendent",
                    )
                ),
            }

            try:

                create_action_persistent(
                    audit_action
                )

                st.success(
                    f"{audit_action['Action ID']} "
                    "berhasil dibuat di "
                    "Action Tracker."
                )

            except Exception as e:

                st.error(
                    "Gagal membuat Action dari "
                    f"Finding: {e}"
                )


# ============================================================
# ACTION TRACKER
# ============================================================

elif menu == "Action Tracker":

    st.header(
        "✅ Action Tracker"
    )

    st.caption(
        "Persistent operational action monitoring "
        "untuk Fleet, HSSE, PMS, Defects, "
        "Certificates, Audit dan operations."
    )

    # ========================================================
    # LOAD ACTIONS
    # ========================================================

    try:

        actions = load_actions()

    except Exception as e:

        st.error(
            "Gagal membaca Action Tracker: "
            f"{e}"
        )

        actions = []

    if supabase_enabled():

        st.success(
            "🟢 Persistent Database: CONNECTED"
        )

    else:

        st.warning(
            "🟡 Persistent Database belum aktif. "
            "Data hanya tersimpan pada session Streamlit."
        )

    # ========================================================
    # CREATE NEW ACTION
    # ========================================================

    st.subheader(
        "➕ Create New Action"
    )

    action_priorities = [
        "Critical",
        "High",
        "Medium",
        "Low",
    ]

    action_statuses = [
        "Open",
        "In Progress",
        "Completed",
    ]

    action_sources = [
        "Voyage",
        "HSSE",
        "PMS",
        "Defects",
        "Certificates",
        "Bunker",
        "Cargo",
        "Audit & Findings",
        "WhatsApp",
        "Management",
        "Other",
    ]

    with st.form(
        "create_action_form",
        clear_on_submit=False,
    ):

        c1, c2, c3 = st.columns(
            3
        )

        with c1:

            new_vessel = st.selectbox(
                "Vessel",
                ["All Fleet"] + FLEET,
            )

        with c2:

            new_priority = st.selectbox(
                "Priority",
                action_priorities,
                index=2,
            )

        with c3:

            new_source = st.selectbox(
                "Source",
                action_sources,
            )

        c4, c5, c6 = st.columns(
            3
        )

        with c4:

            new_responsible = (
                st.text_input(
                    "Responsible / PIC"
                )
            )

        with c5:

            new_status = st.selectbox(
                "Status",
                action_statuses,
            )

        with c6:

            new_due_date = (
                st.date_input(
                    "Due Date"
                )
            )

        new_description = st.text_area(
            "Action Description"
        )

        new_remarks = st.text_area(
            "Remarks"
        )

        create_action_button = (
            st.form_submit_button(
                "CREATE ACTION",
                type="primary",
            )
        )

    if create_action_button:

        if not new_description.strip():

            st.warning(
                "Action Description wajib diisi."
            )

        else:

            new_action = {
                "Action ID": (
                    next_action_id(
                        actions
                    )
                ),
                "Vessel": new_vessel,
                "Source": new_source,
                "Description": (
                    new_description.strip()
                ),
                "Priority": new_priority,
                "Responsible": (
                    new_responsible.strip()
                ),
                "Due Date": (
                    new_due_date.strftime(
                        "%Y-%m-%d"
                    )
                ),
                "Status": new_status,
                "Remarks": (
                    new_remarks.strip()
                ),
                "Created": (
                    datetime.now()
                    .isoformat()
                ),
                "Updated": (
                    datetime.now()
                    .isoformat()
                ),
                "Completed": "",
                "Created By": "admin",
                "Role": (
                    st.session_state.get(
                        "role",
                        "Marine Superintendent",
                    )
                ),
            }

            try:

                create_action_persistent(
                    new_action
                )

                st.success(
                    f"{new_action['Action ID']} "
                    "berhasil disimpan."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    "Action gagal disimpan: "
                    f"{e}"
                )

    # ========================================================
    # ACTION KPI
    # ========================================================

    try:

        actions = load_actions()

    except Exception:

        actions = []

    counts = action_kpis(
        actions
    )

    pending_actions_count = (
        counts["open"]
        + counts["in_progress"]
    )

    st.session_state[
        "pending_actions"
    ] = pending_actions_count

    st.session_state[
        "overdue_actions"
    ] = counts["overdue"]

    st.divider()

    st.subheader(
        "📊 Action Tracker KPI"
    )

    k1, k2, k3, k4, k5 = (
        st.columns(5)
    )

    with k1:

        st.metric(
            "TOTAL",
            counts["total"]
        )

    with k2:

        st.metric(
            "OPEN",
            counts["open"]
        )

    with k3:

        st.metric(
            "IN PROGRESS",
            counts["in_progress"]
        )

    with k4:

        st.metric(
            "OVERDUE",
            counts["overdue"]
        )

    with k5:

        st.metric(
            "COMPLETED",
            counts["completed"]
        )

    # ========================================================
    # ACTION MONITORING
    # ========================================================

    st.divider()

    st.subheader(
        "🔎 Action Monitoring"
    )

    f1, f2, f3 = st.columns(
        3
    )

    with f1:

        filter_status = st.selectbox(
            "Filter Status",
            ["All"] + action_statuses,
            key="action_filter_status",
        )

    with f2:

        filter_priority = (
            st.selectbox(
                "Filter Priority",
                ["All"] + action_priorities,
                key="action_filter_priority",
            )
        )

    with f3:

        vessel_filter_options = sorted(
            {
                str(
                    action.get(
                        "Vessel",
                        "",
                    )
                )
                for action in actions
                if action.get(
                    "Vessel",
                    ""
                )
            }
        )

        filter_vessel = st.selectbox(
            "Filter Vessel",
            ["All"]
            + vessel_filter_options,
            key="action_filter_vessel",
        )

    filtered_actions = []

    for action in actions:

        if (
            filter_status != "All"
            and action.get(
                "Status"
            ) != filter_status
        ):
            continue

        if (
            filter_priority != "All"
            and action.get(
                "Priority"
            ) != filter_priority
        ):
            continue

        if (
            filter_vessel != "All"
            and action.get(
                "Vessel"
            ) != filter_vessel
        ):
            continue

        filtered_actions.append(
            action
        )

    if filtered_actions:

        display_rows = []

        for action in filtered_actions:

            display_rows.append(
                {
                    "Action ID": (
                        action.get(
                            "Action ID",
                            "",
                        )
                    ),
                    "Vessel": (
                        action.get(
                            "Vessel",
                            "",
                        )
                    ),
                    "Source": (
                        action.get(
                            "Source",
                            "",
                        )
                    ),
                    "Description": (
                        action.get(
                            "Description",
                            "",
                        )
                    ),
                    "Priority": (
                        action.get(
                            "Priority",
                            "",
                        )
                    ),
                    "Responsible": (
                        action.get(
                            "Responsible",
                            "",
                        )
                    ),
                    "Due Date": (
                        action.get(
                            "Due Date",
                            "",
                        )
                    ),
                    "Status": (
                        action.get(
                            "Status",
                            "",
                        )
                    ),
                    "Overdue": (
                        "YES"
                        if action_is_overdue_global(
                            action
                        )
                        else "NO"
                    ),
                }
            )

        st.dataframe(
            pd.DataFrame(
                display_rows
            ),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "DATA BELUM TERSEDIA — "
            "belum ada action yang sesuai filter."
        )

    # ========================================================
    # UPDATE / DELETE
    # ========================================================

    if actions:

        st.divider()

        st.subheader(
            "✏️ Update / Delete Action"
        )

        action_ids = [
            action.get(
                "Action ID",
                ""
            )
            for action in actions
        ]

        selected_action_id = (
            st.selectbox(
                "Select Action",
                action_ids,
                key="selected_action_id",
            )
        )

        selected_action = next(
            (
                action
                for action in actions
                if action.get(
                    "Action ID"
                )
                == selected_action_id
            ),
            None,
        )

        if selected_action:

            u1, u2, u3 = st.columns(
                3
            )

            with u1:

                current_status = (
                    selected_action.get(
                        "Status",
                        "Open",
                    )
                )

                status_index = (
                    action_statuses.index(
                        current_status
                    )
                    if current_status
                    in action_statuses
                    else 0
                )

                update_status = (
                    st.selectbox(
                        "Update Status",
                        action_statuses,
                        index=status_index,
                        key=(
                            "update_action_status"
                        ),
                    )
                )

            with u2:

                current_priority = (
                    selected_action.get(
                        "Priority",
                        "Medium",
                    )
                )

                priority_index = (
                    action_priorities.index(
                        current_priority
                    )
                    if current_priority
                    in action_priorities
                    else 2
                )

                update_priority = (
                    st.selectbox(
                        "Update Priority",
                        action_priorities,
                        index=priority_index,
                        key=(
                            "update_action_priority"
                        ),
                    )
                )

            with u3:

                try:

                    current_due = (
                        datetime.strptime(
                            str(
                                selected_action.get(
                                    "Due Date",
                                    "",
                                )
                            )[:10],
                            "%Y-%m-%d",
                        ).date()
                    )

                except Exception:

                    current_due = (
                        datetime.now().date()
                    )

                update_due_date = (
                    st.date_input(
                        "Update Due Date",
                        value=current_due,
                        key=(
                            "update_action_due_date"
                        ),
                    )
                )

            update_responsible = (
                st.text_input(
                    "Update Responsible / PIC",
                    value=(
                        selected_action.get(
                            "Responsible",
                            "",
                        )
                    ),
                    key=(
                        "update_action_responsible"
                    ),
                )
            )

            update_description = (
                st.text_area(
                    "Update Description",
                    value=(
                        selected_action.get(
                            "Description",
                            "",
                        )
                    ),
                    key=(
                        "update_action_description"
                    ),
                )
            )

            update_remarks = (
                st.text_area(
                    "Update Remarks",
                    value=(
                        selected_action.get(
                            "Remarks",
                            "",
                        )
                    ),
                    key=(
                        "update_action_remarks"
                    ),
                )
            )

            b1, b2 = st.columns(
                2
            )

            with b1:

                update_button = st.button(
                    "UPDATE ACTION",
                    use_container_width=True,
                    key=(
                        "update_action_button"
                    ),
                )

            with b2:

                delete_button = st.button(
                    "DELETE ACTION",
                    use_container_width=True,
                    key=(
                        "delete_action_button"
                    ),
                )

            if update_button:

                updated_action = (
                    selected_action.copy()
                )

                updated_action[
                    "Status"
                ] = update_status

                updated_action[
                    "Priority"
                ] = update_priority

                updated_action[
                    "Due Date"
                ] = (
                    update_due_date.strftime(
                        "%Y-%m-%d"
                    )
                )

                updated_action[
                    "Responsible"
                ] = (
                    update_responsible.strip()
                )

                updated_action[
                    "Description"
                ] = (
                    update_description.strip()
                )

                updated_action[
                    "Remarks"
                ] = (
                    update_remarks.strip()
                )

                updated_action[
                    "Updated"
                ] = (
                    datetime.now()
                    .isoformat()
                )

                if (
                    update_status
                    == "Completed"
                ):

                    updated_action[
                        "Completed"
                    ] = (
                        datetime.now()
                        .isoformat()
                    )

                else:

                    updated_action[
                        "Completed"
                    ] = ""

                try:

                    update_action_persistent(
                        selected_action_id,
                        updated_action,
                    )

                    st.success(
                        f"{selected_action_id} "
                        "berhasil diperbarui."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        "Action gagal "
                        f"diperbarui: {e}"
                    )

            if delete_button:

                try:

                    delete_action_persistent(
                        selected_action_id
                    )

                    st.success(
                        f"{selected_action_id} "
                        "berhasil dihapus."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        "Action gagal "
                        f"dihapus: {e}"
                    )

    # ========================================================
    # EXPORT
    # ========================================================

    if actions:

        st.divider()

        st.subheader(
            "📥 Export Action Tracker"
        )

        export_df = pd.DataFrame(
            actions
        )

        csv_data = (
            export_df.to_csv(
                index=False
            ).encode(
                "utf-8"
            )
        )

        st.download_button(
            label=(
                "DOWNLOAD ACTION TRACKER CSV"
            ),
            data=csv_data,
            file_name=(
                "marine_action_tracker.csv"
            ),
            mime="text/csv",
            use_container_width=True,
            key=(
                "download_action_tracker_csv"
            ),
        )

    # ========================================================
    # OPERATIONAL PRIORITY
    # ========================================================

    st.divider()

    st.subheader(
        "🚨 Operational Priority"
    )

    if counts["overdue"] > 0:

        st.error(
            f"⚠️ {counts['overdue']} "
            "action overdue dan membutuhkan "
            "follow-up."
        )

    elif counts["open"] > 0:

        st.warning(
            f"⚠️ {counts['open']} "
            "action masih berstatus Open."
        )

    elif counts[
        "in_progress"
    ] > 0:

        st.info(
            f"🔄 {counts['in_progress']} "
            "action sedang dalam proses."
        )

    elif counts["total"] > 0:

        st.success(
            "✅ Seluruh action telah selesai."
        )

    else:

        st.info(
            "DATA BELUM TERSEDIA — "
            "belum ada operational action."
        )
        # ============================================================
# AI MARINE COPILOT
# ============================================================

elif menu == "AI Marine Copilot":

    st.header(
        "🤖 AI Marine Operations Copilot"
    )

    st.caption(
        f"Decision support untuk "
        f"{st.session_state.role}"
    )

    st.info(
        """
AI Marine Copilot menggunakan data operasional
yang benar-benar tersedia dari Marine Operations
Intelligence Centre.

AI tidak diperbolehkan mengarang status kapal,
Voyage, HSSE, PMS, Defect, Certificate, Bunker,
Cargo, Audit Finding atau Action Tracker.
        """
    )

    prompt = st.text_area(
        "Pertanyaan / Instruksi",
        placeholder=(
            "Contoh: Buat Fleet Risk Assessment "
            "berdasarkan data operasional yang tersedia "
            "dan jelaskan prioritas serta data gap."
        ),
        height=150,
        key="ai_copilot_prompt",
    )

    if st.button(
        "ASK AI",
        type="primary",
        key="ask_ai_copilot",
    ):

        if not prompt.strip():

            st.warning(
                "Masukkan pertanyaan terlebih dahulu."
            )

        else:

            try:

                intelligence_context = (
                    build_intelligence_context()
                )

                context_json = json.dumps(
                    intelligence_context,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )

                fleet_prompt = f"""
USER REQUEST:

{prompt.strip()}


FULL OPERATIONAL INTELLIGENCE DATA:

{context_json}


MARINE OPERATIONS INTELLIGENCE RULES:

1. Analyze ONLY supplied operational data.

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
- audit finding
- action status
- WhatsApp message
- operational risk

3. If required information is missing,
state clearly:

DATA BELUM TERSEDIA.

4. Do not create risk ranking when there
is not enough factual information.

5. Separate response into:

FLEET SUMMARY

RISK ASSESSMENT

TOP PRIORITIES

DATA GAPS

RECOMMENDED ACTIONS

6. For safety-critical matters,
recommend appropriate escalation.

7. Prioritize:
- Safety
- Compliance
- Operational continuity

8. Never present assumptions as facts.
"""

                with st.spinner(
                    "Gemini sedang menganalisis "
                    "Marine Operations Intelligence..."
                ):

                    answer = (
                        ask_gemini_marine_copilot(
                            fleet_prompt,
                            st.session_state.role,
                        )
                    )

                st.markdown(
                    "### 🧠 Marine Operations "
                    "Intelligence Assessment"
                )

                st.markdown(
                    answer
                )

                st.session_state[
                    "ai_history"
                ].append(
                    {
                        "question": (
                            prompt.strip()
                        ),
                        "answer": answer,
                        "time": (
                            datetime.now()
                            .isoformat()
                        ),
                    }
                )

            except Exception as e:

                st.error(
                    "Gemini gagal memproses "
                    f"Marine Operations Intelligence: {e}"
                )

    if st.session_state.get(
        "ai_history"
    ):

        with st.expander(
            "AI Analysis History"
        ):

            for item in reversed(
                st.session_state[
                    "ai_history"
                ][-10:]
            ):

                st.markdown(
                    f"**Question:** "
                    f"{item.get('question', '')}"
                )

                st.markdown(
                    item.get(
                        "answer",
                        ""
                    )
                )

                st.caption(
                    item.get(
                        "time",
                        ""
                    )
                )

                st.divider()


# ============================================================
# EXECUTIVE REPORTS
# ============================================================

elif menu == "Executive Reports":

    st.header(
        "📑 Executive Reports"
    )

    st.subheader(
        "Daily Marine Operations Brief"
    )

    report_date = (
        datetime.now()
        .strftime(
            "%d %B %Y %H:%M"
        )
    )

    snapshots = (
        load_operational_snapshots()
    )

    try:

        report_actions = (
            load_actions()
        )

    except Exception:

        report_actions = []

    action_counts = (
        action_kpis(
            report_actions
        )
    )

    pending_actions = (
        action_counts["open"]
        + action_counts["in_progress"]
    )

    critical_actions = sum(
        1
        for action in report_actions
        if (
            str(
                action.get(
                    "Priority",
                    ""
                )
            ).lower()
            == "critical"
            and str(
                action.get(
                    "Status",
                    ""
                )
            ).lower()
            != "completed"
        )
    )

    report = {

        "Report Date":
            report_date,

        "Fleet":
            len(FLEET),

        "Active Vessels":
            len(FLEET),

        "Voyage Records":
            snapshots.get(
                "Voyage Operations",
                {},
            ).get(
                "metrics",
                {},
            ).get(
                "records",
                0,
            ),

        "Delayed / Exception":
            snapshots.get(
                "Voyage Operations",
                {},
            ).get(
                "metrics",
                {},
            ).get(
                "delayed",
                0,
            ),

        "Voyage Attention":
            snapshots.get(
                "Voyage Operations",
                {},
            ).get(
                "metrics",
                {},
            ).get(
                "attention",
                0,
            ),

        "Open Defects":
            snapshots.get(
                "Defects",
                {},
            ).get(
                "metrics",
                {},
            ).get(
                "open",
                0,
            ),

        "HSSE Open Findings":
            snapshots.get(
                "HSSE / DPA",
                {},
            ).get(
                "metrics",
                {},
            ).get(
                "open_findings",
                0,
            ),

        "Certificate Records":
            snapshots.get(
                "Certificates",
                {},
            ).get(
                "metrics",
                {},
            ).get(
                "records",
                0,
            ),

        "PMS Records":
            snapshots.get(
                "PMS / Maintenance",
                {},
            ).get(
                "metrics",
                {},
            ).get(
                "records",
                0,
            ),

        "Bunker Reports":
            snapshots.get(
                "Bunker",
                {},
            ).get(
                "metrics",
                {},
            ).get(
                "records",
                0,
            ),

        "Cargo Records":
            snapshots.get(
                "Cargo",
                {},
            ).get(
                "metrics",
                {},
            ).get(
                "records",
                0,
            ),

        "Audit Open Findings":
            snapshots.get(
                "Audit & Findings",
                {},
            ).get(
                "metrics",
                {},
            ).get(
                "open",
                0,
            ),

        "Pending Actions":
            pending_actions,

        "Overdue Actions":
            action_counts[
                "overdue"
            ],

        "Critical Actions":
            critical_actions,
    }

    st.markdown(
        "### 📊 Executive Data"
    )

    st.json(
        report
    )

    st.subheader(
        "🚨 Management Attention"
    )

    priorities = []

    if (
        report[
            "Overdue Actions"
        ] > 0
    ):

        priorities.append(
            f"{report['Overdue Actions']} "
            "overdue action(s)"
        )

    if (
        report[
            "Critical Actions"
        ] > 0
    ):

        priorities.append(
            f"{report['Critical Actions']} "
            "critical action(s)"
        )

    if (
        report[
            "Delayed / Exception"
        ] > 0
    ):

        priorities.append(
            f"{report['Delayed / Exception']} "
            "voyage exception(s)"
        )

    if (
        report[
            "Open Defects"
        ] > 0
    ):

        priorities.append(
            f"{report['Open Defects']} "
            "open defect(s)"
        )

    if (
        report[
            "HSSE Open Findings"
        ] > 0
    ):

        priorities.append(
            f"{report['HSSE Open Findings']} "
            "open HSSE finding(s)"
        )

    if (
        report[
            "Audit Open Findings"
        ] > 0
    ):

        priorities.append(
            f"{report['Audit Open Findings']} "
            "open audit finding(s)"
        )

    if priorities:

        for item in priorities:

            st.warning(
                item
            )

    else:

        st.success(
            "Tidak ada Management Attention "
            "item berdasarkan data yang tersedia."
        )

    if st.button(
        "GENERATE AI DAILY SITREP",
        type="primary",
        key="generate_daily_sitrep",
    ):

        try:

            sitrep_context = (
                build_intelligence_context()
            )

            sitrep_json = json.dumps(
                sitrep_context,
                ensure_ascii=False,
                indent=2,
                default=str,
            )

            sitrep_prompt = f"""
Create a Daily Marine Operations SITREP
based ONLY on supplied operational data.

FULL OPERATIONAL INTELLIGENCE DATA:

{sitrep_json}

RULES:

- Never invent operational facts.
- If information is unavailable:
  DATA BELUM TERSEDIA.
- Prioritize safety, compliance and
  operational continuity.

Return:

EXECUTIVE SUMMARY

CRITICAL / HIGH RISKS

ACTIONS REQUIRING DECISION

DATA GAPS

RECOMMENDED FOLLOW-UP
"""

            with st.spinner(
                "Generating AI Daily SITREP..."
            ):

                answer = (
                    ask_gemini_marine_copilot(
                        sitrep_prompt,
                        st.session_state.get(
                            "role",
                            "Marine Superintendent",
                        ),
                    )
                )

            st.markdown(
                "### 🤖 AI Daily SITREP"
            )

            st.markdown(
                answer
            )

        except Exception as e:

            st.error(
                "Gagal membuat Daily SITREP: "
                f"{e}"
            )


# ============================================================
# WHATSAPP OPERATIONS
# ============================================================

elif menu == "WhatsApp Operations":

    st.header(
        "📱 WhatsApp Operations Intelligence"
    )

    st.caption(
        "Operational message intake, "
        "risk classification dan Action Tracker integration."
    )

    st.info(
        "Live incoming WhatsApp Group membutuhkan "
        "Meta WhatsApp Cloud API + webhook/backend. "
        "Manual operational intake di bawah ini "
        "sudah dapat disimpan ke Supabase."
    )

    # ========================================================
    # MANUAL MESSAGE INTAKE
    # ========================================================

    st.subheader(
        "➕ Manual Operational Message Intake"
    )

    with st.form(
        "whatsapp_intake_form",
        clear_on_submit=True,
    ):

        w1, w2 = st.columns(
            2
        )

        with w1:

            wa_vessel = st.selectbox(
                "Vessel",
                [
                    "Unknown / Fleet"
                ] + FLEET,
                key="wa_vessel",
            )

            wa_sender = (
                st.text_input(
                    "Sender",
                    key="wa_sender",
                )
            )

        with w2:

            wa_risk = st.selectbox(
                "Risk",
                [
                    "Normal",
                    "Low",
                    "Medium",
                    "High",
                    "Critical",
                ],
                key="wa_risk",
            )

            wa_status = st.selectbox(
                "Status",
                [
                    "New",
                    "Reviewed",
                    "Action Created",
                    "Closed",
                ],
                key="wa_status",
            )

        wa_message = st.text_area(
            "Operational Message",
            placeholder=(
                "Paste pesan WhatsApp "
                "operasional di sini..."
            ),
            key="wa_message",
        )

        save_wa = (
            st.form_submit_button(
                "SAVE OPERATIONAL MESSAGE",
                use_container_width=True,
            )
        )

    if save_wa:

        if not wa_message.strip():

            st.warning(
                "Operational Message wajib diisi."
            )

        else:

            message_record = {

                "message_id":
                    "WA-"
                    + uuid.uuid4().hex[:12]
                    .upper(),

                "message_time":
                    datetime.now()
                    .isoformat(),

                "vessel":
                    wa_vessel,

                "sender":
                    wa_sender.strip(),

                "message":
                    wa_message.strip(),

                "risk":
                    wa_risk,

                "status":
                    wa_status,
            }

            try:

                save_whatsapp_message(
                    message_record
                )

                st.success(
                    "Operational WhatsApp message "
                    "berhasil disimpan."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    "Gagal menyimpan WhatsApp "
                    f"message: {e}"
                )

    # ========================================================
    # MESSAGE LOG
    # ========================================================

    try:

        messages = (
            load_whatsapp_messages()
        )

    except Exception as e:

        st.error(
            "Gagal membaca WhatsApp "
            f"message: {e}"
        )

        messages = []

    if messages:

        st.subheader(
            "📋 Operational Message Log"
        )

        wa_df = pd.DataFrame(
            messages
        )

        st.dataframe(
            wa_df,
            use_container_width=True,
            hide_index=True,
        )

        message_indexes = list(
            range(
                len(messages)
            )
        )

        selected_index = (
            st.selectbox(
                "Select Message for Action",
                message_indexes,
                format_func=lambda i: (
                    str(
                        messages[i].get(
                            "message",
                            "",
                        )
                    )[:100]
                ),
                key="wa_action_select",
            )
        )

        selected_message = (
            messages[
                selected_index
            ]
        )

        if st.button(
            "CREATE ACTION FROM WHATSAPP",
            type="primary",
            key="create_action_from_whatsapp",
        ):

            try:

            action_rows = load_actions()

            # ==========================================================
            # WHATSAPP DUPLICATE PROTECTION
            # Satu WhatsApp message hanya boleh membuat satu Action
            # ==========================================================

            wa_message_id = str(
                selected_message.get(
                    "message_id",
                    "",
                )
            ).strip()

            wa_message_text = str(
                selected_message.get(
                    "message",
                    "",
                )
            ).strip()

            wa_vessel = str(
                selected_message.get(
                    "vessel",
                    "Unknown / Fleet",
                )
            ).strip()

            existing_action = None

            for existing_row in action_rows:

                existing_source = str(
                    existing_row.get(
                        "Source",
                        existing_row.get(
                            "source",
                            "",
                        ),
                    )
                ).strip()

                existing_description = str(
                    existing_row.get(
                        "Description",
                        existing_row.get(
                            "description",
                            "",
                        ),
                    )
                ).strip()

                existing_vessel = str(
                    existing_row.get(
                        "Vessel",
                        existing_row.get(
                            "vessel",
                            "",
                        ),
                    )
                ).strip()

                existing_remarks = str(
                    existing_row.get(
                        "Remarks",
                        existing_row.get(
                            "remarks",
                            "",
                        ),
                    )
                ).strip()

                message_id_match = (
                    bool(wa_message_id)
                    and wa_message_id in existing_remarks
                )

                legacy_message_match = (
                    existing_source.lower() == "whatsapp"
                    and existing_description == wa_message_text
                    and existing_vessel == wa_vessel
                )

                if message_id_match or legacy_message_match:
                    existing_action = existing_row
                    break

            if existing_action is not None:

                existing_action_id = str(
                    existing_action.get(
                        "Action ID",
                        existing_action.get(
                            "action_id",
                            "Existing Action",
                        ),
                    )
                )

                st.warning(
                    f"WhatsApp message ini sudah memiliki "
                    f"Action Tracker: {existing_action_id}. "
                    "Duplikasi tidak dibuat."
                )

            else:

                wa_priority = str(
                    selected_message.get(
                        "risk",
                        "Medium",
                    )
                ).title()

                if wa_priority not in [
                    "Critical",
                    "High",
                    "Medium",
                    "Low",
                ]:
                    wa_priority = "Medium"

                wa_action = {

                    "Action ID":
                        next_action_id(
                            action_rows
                        ),

                    "Vessel":
                        wa_vessel,

                    "Source":
                        "WhatsApp",

                    "Description":
                        wa_message_text,

                    "Priority":
                        wa_priority,

                    "Responsible":
                        "Marine Superintendent",

                    "Due Date":
                        (
                            datetime.now()
                            .date()
                            .isoformat()
                        ),

                    "Status":
                        "Open",

                    "Remarks":
                        (
                            "WhatsApp Message ID: "
                            + wa_message_id
                            + " | WhatsApp sender: "
                            + str(
                                selected_message.get(
                                    "sender",
                                    "",
                                )
                            )
                        ),

                    "Created":
                        datetime.now()
                        .isoformat(),

                    "Updated":
                        datetime.now()
                        .isoformat(),

                    "Completed":
                        "",

                    "Created By":
                        "admin",

                    "Role":
                        st.session_state.get(
                            "role",
                            "Marine Superintendent",
                        ),
                }

                create_action_persistent(
                    wa_action
                )

                st.success(
                    f"{wa_action['Action ID']} "
                    "berhasil dibuat dari "
                    "WhatsApp message."
                )

                st.rerun()
            

            except Exception as e:

                st.error(
                    "Gagal membuat Action dari "
                    f"WhatsApp: {e}"
                )

    else:

        st.info(
            "DATA BELUM TERSEDIA — "
            "belum ada operational message."
        )


# ============================================================
# SYSTEM
# ============================================================

elif menu == "System":

    st.header(
        "⚙️ System Control Centre"
    )

    st.subheader(
        "System Status"
    )

    c1, c2, c3 = st.columns(
        3
    )

    with c1:

        st.success(
            "Application Online"
        )

    with c2:

        st.success(
            "Fleet Database Online"
        )

    with c3:

        if get_gemini_client() is not None:

            st.success(
                "AI Framework Ready"
            )

        else:

            st.warning(
                "AI Key Not Configured"
            )

    st.divider()

    st.subheader(
        "Persistent Database"
    )

    if supabase_enabled():

        st.success(
            "🟢 Supabase Database: CONNECTED"
        )

        try:

            database_actions = (
                load_actions_from_db()
            )

            database_snapshots = (
                load_operational_snapshots()
            )

            database_messages = (
                load_whatsapp_messages()
            )

            d1, d2, d3 = st.columns(
                3
            )

            with d1:

                st.metric(
                    "Actions",
                    len(
                        database_actions
                    )
                )

            with d2:

                st.metric(
                    "Operational Modules",
                    len(
                        database_snapshots
                    )
                )

            with d3:

                st.metric(
                    "WhatsApp Messages",
                    len(
                        database_messages
                    )
                )

            st.success(
                "Supabase read test: SUCCESS"
            )

        except Exception as e:

            st.error(
                "Supabase configured tetapi "
                "database read test gagal: "
                f"{e}"
            )

    else:

        st.error(
            "🔴 Persistent Database: "
            "NOT CONFIGURED"
        )

        st.info(
            "Tambahkan SUPABASE_URL dan "
            "SUPABASE_SECRET_KEY di "
            "Streamlit Secrets."
        )

    st.divider()

    st.subheader(
        "Operational Data Coverage"
    )

    system_snapshots = (
        load_operational_snapshots()
    )

    system_modules = [
        "Voyage Operations",
        "HSSE / DPA",
        "PMS / Maintenance",
        "Defects",
        "Certificates",
        "Bunker",
        "Cargo",
        "Audit & Findings",
    ]

    coverage_rows = []

    for module_name in system_modules:

        snapshot = (
            system_snapshots.get(
                module_name,
                {}
            )
        )

        metrics = snapshot.get(
            "metrics",
            {}
        )

        records = metrics.get(
            "records",
            0,
        )

        coverage_rows.append(
            {
                "Module":
                    module_name,

                "Records":
                    records,

                "Status":
                    (
                        "AVAILABLE"
                        if records > 0
                        else "DATA GAP"
                    ),
            }
        )

    st.dataframe(
        pd.DataFrame(
            coverage_rows
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.subheader(
        "Architecture"
    )

    st.markdown(
        """
**Marine Operations Intelligence Centre**

**Application Layer**  
→ Streamlit

**Persistent Data Layer**  
→ Supabase PostgreSQL + REST API

**Intelligence Layer**  
→ AI Marine Operations Copilot

**Operational Domains**  
→ Fleet  
→ Voyage  
→ HSSE / DPA  
→ PMS / Maintenance  
→ Defects  
→ Certificates  
→ Bunker  
→ Cargo  
→ Audit & Findings  
→ Action Tracker

**Communication Layer**  
→ WhatsApp Operations Intelligence

**Executive Layer**  
→ Dashboard Intelligence  
→ Daily SITREP  
→ Executive Reports
        """
    )

    st.divider()

    st.subheader(
        "Deployment Information"
    )

    st.write(
        "Version: "
        "Marine Operations Intelligence Centre "
        "Supabase Stage 1–5"
    )

    st.write(
        "Fleet: 21 vessels"
    )

    st.write(
        "Crew master: 200"
    )

    st.write(
        "Current role: "
        f"{st.session_state.get('role', 'Marine Superintendent')}"
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "MARINE OPERATIONS INTELLIGENCE CENTRE • "
    "Fleet • HSSE • PMS • Voyage • Risk • AI Copilot"
)
