import os
import re
import sqlite3
import secrets
from datetime import datetime
from urllib.parse import urlencode

import pandas as pd
import streamlit as st
from pypdf import PdfReader
from docx import Document
from db import has_active_plan
from payments import show_paywall

from ai_service import generate_plan


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Task Manager",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DB_PATH = "taskmanager.db"


# ============================================================
# STYLING
# ============================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

    .stApp {
        background: #FAF5FF !important;
        color: #1E1B4B !important;
        font-family: 'DM Sans', sans-serif;
    }

    h1, h2, h3, h4, label, p {
        font-family: 'Space Grotesk', sans-serif !important;
        color: #1E1B4B !important;
    }

    .hero {
        padding: 2rem;
        border-radius: 20px;
        background: linear-gradient(135deg, #7C3AED 0%, #EC4899 100%);
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 25px rgba(124, 58, 237, 0.15);
    }

    .hero h1, .hero p {
        color: white !important;
    }

    /* Clean Light Expanders with locked white background and no hover color changes */
    [data-testid="stExpander"], 
    [data-testid="stExpander"] details,
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary:hover,
    [data-testid="stExpander"] summary:active,
    [data-testid="stExpander"] summary:focus {
        background-color: #FFFFFF !important;
        color: #1E1B4B !important;
    }

    [data-testid="stExpander"] {
        border: 1.5px solid #000000 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(147, 51, 234, 0.03);
        margin-bottom: 1rem;
        padding: 0.5rem 1rem;
    }

    [data-testid="stExpander"] summary {
        display: flex !important;
        align-items: center !important;
        gap: 0.75rem !important;
    }

    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary span {
        margin: 0 !important;
        color: #1E1B4B !important;
    }

    .muted {
        color: #6B21A8;
        font-size: .94rem;
    }

    /* White Input Boxes & Select Boxes with Black Outlines */
    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stNumberInput"] input,
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1.5px solid #000000 !important;
        border-radius: 8px !important;
        caret-color: #000000 !important;
    }

    /* Disabled Inputs - White Background & Black Border */
    div[data-testid="stTextInput"] input:disabled {
        background-color: #ffffff !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        border: 1.5px solid #000000 !important;
    }

    /* File Uploader Container Override with clean white background and zero dark outlines */
    [data-testid="stFileUploader"] {
        background-color: #FFFFFF !important;
        border: 1.5px solid #000000 !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }

    [data-testid="stFileUploader"] section {
        background-color: #FFFFFF !important;
        border: 1px dashed #000000 !important;
        border-radius: 8px !important;
    }

    [data-testid="stFileUploader"] section * {
        color: #1E1B4B !important;
    }

    [data-testid="stFileUploader"] button {
        background-color: #FAF5FF !important;
        color: #1E1B4B !important;
        border: 1.5px solid #000000 !important;
        border-radius: 8px !important;
    }

    [data-testid="stFileUploader"] button:hover {
        background-color: #F3E8FF !important;
        color: #1E1B4B !important;
        border: 1.5px solid #7C3AED !important;
    }

    /* Force uploaded file pill / tag items to have a white background and black text */
    [data-testid="stFileUploader"] [data-baseweb="tag"],
    [data-testid="stFileUploader"] [data-testid="stUploadedFile"],
    div[data-baseweb="tag"] {
        background-color: #FFFFFF !important;
        border: 1.5px solid #000000 !important;
        border-radius: 8px !important;
        color: #000000 !important;
    }

    [data-testid="stFileUploader"] [data-baseweb="tag"] *,
    [data-testid="stFileUploader"] [data-testid="stUploadedFile"] *,
    div[data-baseweb="tag"] * {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    div[data-testid="stTextInput"] input::placeholder,
    div[data-testid="stTextArea"] textarea::placeholder {
        color: #666666 !important;
        opacity: 1 !important;
    }

    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stTextArea"] textarea:focus,
    div[data-testid="stNumberInput"] input:focus,
    div[data-baseweb="select"] > div:focus-within {
        border: 2px solid #7C3AED !important;
        box-shadow: 0 0 0 1px #7C3AED !important;
    }

    /* Action Buttons - Vibrant Gradient */
    div.stButton > button,
    div.stFormSubmitButton > button,
    div[data-testid="stDownloadButton"] button {
        background: linear-gradient(135deg, #EC4899 0%, #8B5CF6 100%) !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        min-height: 2.5rem;
        border: none !important;
        box-shadow: 0 4px 12px rgba(236, 72, 153, 0.2) !important;
    }

    div.stButton > button:hover, 
    div.stButton > button:active, 
    div.stButton > button:focus,
    div.stFormSubmitButton > button:hover,
    div.stFormSubmitButton > button:active,
    div.stFormSubmitButton > button:focus {
        background: linear-gradient(135deg, #EC4899 0%, #8B5CF6 100%) !important;
        color: white !important;
        opacity: 0.95 !important;
        transform: translateY(-1px) !important;
        border: none !important;
        box-shadow: 0 6px 16px rgba(139, 92, 246, 0.3) !important;
    }

    [data-testid="stMetric"] {
        background: white;
        padding: 1rem;
        border: 1.5px solid #000000;
        border-radius: 12px;
    }

    #MainMenu, footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATABASE SETUP & HELPERS
# ============================================================

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                invite_code TEXT UNIQUE NOT NULL,
                owner_email TEXT NOT NULL,
                document_text TEXT DEFAULT '',
                tasks_generated INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                joined_at TEXT NOT NULL,
                UNIQUE(project_id, email),
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                assignee_email TEXT DEFAULT '',
                status TEXT DEFAULT 'To do',
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
            """
        )

        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(projects)").fetchall()
        }

        if "document_text" not in columns:
            conn.execute("ALTER TABLE projects ADD COLUMN document_text TEXT DEFAULT ''")

        if "tasks_generated" not in columns:
            conn.execute("ALTER TABLE projects ADD COLUMN tasks_generated INTEGER DEFAULT 0")


init_db()


def get_user(email):
    with get_db() as conn:
        return conn.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()


def register_user(name, email):
    with get_db() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO users (email, name, created_at)
            VALUES (?, ?, ?)
            """,
            (email.lower().strip(), name.strip(), datetime.utcnow().isoformat())
        )


def get_project(project_id):
    with get_db() as conn:
        return conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()


def delete_project(project_id):
    with get_db() as conn:
        conn.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))
        conn.execute("DELETE FROM members WHERE project_id = ?", (project_id,))
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))


def get_member_count(project_id):
    with get_db() as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM members WHERE project_id = ?", (project_id,)).fetchone()
        return row["n"]


def get_projects_for_user(email):
    with get_db() as conn:
        return conn.execute(
            """
            SELECT DISTINCT p.*
            FROM projects p
            JOIN members m ON m.project_id = p.id
            WHERE lower(m.email) = lower(?)
            ORDER BY p.created_at DESC
            """,
            (email,),
        ).fetchall()


def get_members(project_id):
    with get_db() as conn:
        return conn.execute("SELECT name, email, joined_at FROM members WHERE project_id = ? ORDER BY joined_at", (project_id,)).fetchall()


def get_tasks(project_id):
    with get_db() as conn:
        return conn.execute("SELECT * FROM tasks WHERE project_id = ? ORDER BY id", (project_id,)).fetchall()


def add_member(project_id, name, email):
    with get_db() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO members (project_id, name, email, joined_at)
            VALUES (?, ?, ?, ?)
            """,
            (project_id, name.strip(), email.lower().strip(), datetime.utcnow().isoformat()),
        )


# ============================================================
# DOCUMENT EXTRACTION & AI SUGGESTIONS
# ============================================================

def extract_single_document(uploaded_file):
    filename = uploaded_file.name.lower()
    try:
        if filename.endswith(".txt"):
            return uploaded_file.getvalue().decode("utf-8", errors="ignore")
        if filename.endswith(".pdf"):
            reader = PdfReader(uploaded_file)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        if filename.endswith(".docx"):
            doc = Document(uploaded_file)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    paragraphs.append(" | ".join(cell.text for cell in row.cells))
            return "\n".join(paragraphs)
        return ""
    except Exception as exc:
        return f"[Error reading {uploaded_file.name}: {exc}]"


def extract_documents(uploaded_files):
    texts = []
    for f in uploaded_files:
        text = extract_single_document(f)
        if text.strip():
            texts.append(f"--- File: {f.name} ---\n" + text)
    return "\n\n".join(texts)


def suggest_tasks(document_text):
    if not document_text.strip():
        return [
            ("Understand the assignment", "Review the brief and agree on the expected outcome."),
            ("Plan the project", "Define milestones, responsibilities, and deadlines."),
            ("Complete the main work", "Work together on the main project deliverable."),
            ("Review and submit", "Proofread the final deliverable and prepare submission."),
        ]
    lines = []
    for raw_line in document_text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        line = re.sub(r"^[\-\*\u2022\d\.\)\s]+", "", line)
        if 12 <= len(line) <= 140:
            lines.append(line)
    keywords = ("must", "should", "submit", "create", "design", "analyse", "analyze", "research", "implement", "develop", "evaluate", "presentation", "report", "deadline", "requirement", "deliverable", "objective", "task", "build", "test", "document")
    chosen = []
    seen = set()
    for line in lines:
        normalized = line.lower()
        if normalized in seen:
            continue
        if any(word in normalized for word in keywords):
            chosen.append(line)
            seen.add(normalized)
        if len(chosen) >= 8:
            break
    if not chosen:
        chosen = lines[:6]
    tasks = [("Review: " + line[:100], "Suggested from the assignment brief. Confirm scope with team.") for line in chosen]
    if not tasks:
        tasks = [
            ("Review assignment brief", "Agree on requirements and final deliverable."),
            ("Divide the work", "Assign responsibilities and set internal deadlines."),
            ("Prepare final submission", "Combine, check, and submit work."),
        ]
    return tasks


def generate_project_tasks(document_text, project_id):
    members = get_members(project_id)
    member_names = [member["name"] for member in members]

    result = generate_plan(
        brief=document_text,
        rubric="",
        comments="",
        members=member_names
    )

    return result

# ============================================================
# APP FLOW & UI
# ============================================================

st.markdown(
    """
    <div class="hero">
        <h1>Task Manager</h1>
        <p>Turn group assignments into clear tasks, shared ownership, and progress.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "name" not in st.session_state:
    st.session_state["name"] = ""
if "email" not in st.session_state:
    st.session_state["email"] = ""
if "project_id" not in st.session_state:
    st.session_state["project_id"] = None

if not st.session_state["email"] and st.query_params.get("email"):
    returning = get_user(st.query_params["email"])
    if returning:
        st.session_state["name"] = returning["name"]
        st.session_state["email"] = returning["email"]


# --- SIGN IN / CREATE ACCOUNT AUTHENTICATION SCREEN ---
if not st.session_state["name"] or not st.session_state["email"]:
    st.markdown("### Welcome to Task Manager")
    
    auth_tab1, auth_tab2 = st.tabs(["Sign In", "Create New Account"])

    with auth_tab1:
        with st.form("signin_form"):
            st.markdown("**Your Email**")
            signin_email = st.text_input("Email", placeholder="Enter your email", label_visibility="collapsed")
            signin_submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)

        if signin_submitted:
            signin_email = signin_email.strip().lower()
            if not signin_email or "@" not in signin_email:
                st.error("Please enter a valid email address.")
            else:
                user = get_user(signin_email)
                if user:
                    st.session_state["name"] = user["name"]
                    st.session_state["email"] = user["email"]
                    st.success(f"Welcome back, {user['name']}!")
                    st.rerun()
                else:
                    st.error("No account found with this email. Please create a new account.")

    with auth_tab2:
        with st.form("signup_form"):
            st.markdown("**Your Name**")
            signup_name = st.text_input("Name", placeholder="Enter your name", label_visibility="collapsed")
            
            st.markdown("**Your Email**")
            signup_email = st.text_input("Email", placeholder="Enter your email", label_visibility="collapsed")
            
            signup_submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)

        if signup_submitted:
            signup_name = signup_name.strip()
            signup_email = signup_email.strip().lower()
            if not signup_name:
                st.error("Please enter your name.")
            elif not signup_email or "@" not in signup_email:
                st.error("Please enter a valid email address.")
            else:
                register_user(signup_name, signup_email)
                st.session_state["name"] = signup_name
                st.session_state["email"] = signup_email
                st.success("Account created successfully!")
                st.rerun()

    st.stop()

name = st.session_state["name"]
email = st.session_state["email"]

if not has_active_plan(email):
    show_paywall(email)
    st.stop()

# --- MAIN WORKSPACE ---
st.header("Workspace")

col_create, col_join = st.columns(2)

with col_create:
    with st.expander("Create a new project", expanded=True):
        with st.form("create_project_form"):
            st.markdown("**Project Name**")
            project_name = st.text_input("Project name", placeholder="Enter project name", label_visibility="collapsed")
            create_submitted = st.form_submit_button("Create project", type="primary")

        if create_submitted:
            if not project_name.strip():
                st.error("Please enter a project name.")
            else:
                invite_code = secrets.token_urlsafe(6).replace("-", "").replace("_", "")[:8].upper()
                with get_db() as conn:
                    cursor = conn.execute(
                        "INSERT INTO projects (name, invite_code, owner_email, document_text, tasks_generated, created_at) VALUES (?, ?, ?, '', 0, ?)",
                        (project_name.strip(), invite_code, email, datetime.utcnow().isoformat())
                    )
                    project_id = cursor.lastrowid
                add_member(project_id, name, email)
                st.session_state["project_id"] = project_id
                st.success("Project created.")
                st.rerun()

with col_join:
    with st.expander("Join existing project", expanded=False):
        with st.form("join_project_form"):
            st.markdown("**Invite Code**")
            invite_code_input = st.text_input("Invite code", placeholder="Enter invite code", label_visibility="collapsed")
            join_submitted = st.form_submit_button("Join project", type="primary")

        if join_submitted:
            if not invite_code_input.strip():
                st.error("Enter an invite code.")
            else:
                with get_db() as conn:
                    project = conn.execute("SELECT * FROM projects WHERE invite_code = ?", (invite_code_input.strip().upper(),)).fetchone()
                if not project:
                    st.error("That invite code wasn't found.")
                else:
                    add_member(project["id"], name, email)
                    st.session_state["project_id"] = project["id"]
                    st.success(f"You joined {project['name']}.")
                    st.rerun()

st.divider()

user_projects = get_projects_for_user(email)

if not user_projects:
    st.info("Create or join a project above to get started.")
else:
    project_options = {p["name"]: p["id"] for p in user_projects}
    option_labels = list(project_options.keys())
    current_id = st.session_state.get("project_id")
    default_index = 0
    if current_id in project_options.values():
        default_index = list(project_options.values()).index(current_id)

    col_sel, col_del = st.columns([3, 1])
    with col_sel:
        selected_label = st.selectbox("Active project", option_labels, index=default_index, key="active_project_selector")
    with col_del:
        st.write("")
        st.write("")
        if st.button("Delete Project", type="secondary"):
            proj_id_to_del = project_options[selected_label]
            delete_project(proj_id_to_del)
            st.session_state["project_id"] = None
            st.success("Project deleted successfully.")
            st.rerun()

    selected_project_id = project_options[selected_label]
    st.session_state["project_id"] = selected_project_id

    project = get_project(selected_project_id)
    if project:
        member_count = get_member_count(selected_project_id)

        st.subheader(project["name"])
        st.caption(f"Invite Code: **{project['invite_code']}** · {member_count} member(s) joined")

        invite_url = "http://localhost:8501?" + urlencode({"invite": project["invite_code"]})
        st.markdown("**Shareable Invite Link (Click box to copy)**")
        
        st.components.v1.html(f"""
            <div onclick="copyLink()" style="
                background-color: #ffffff;
                color: #1E1B4B;
                border: 1.5px solid #000000;
                border-radius: 8px;
                padding: 10px 16px;
                font-family: 'Space Grotesk', sans-serif;
                font-size: 14px;
                cursor: pointer;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.02);
                transition: all 0.2s ease;
                margin-bottom: 1rem;
            " id="copyBox" onmouseover="this.style.borderColor='#7C3AED'" onmouseout="this.style.borderColor='#000000'">
                <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: 'Space Grotesk', sans-serif;">{invite_url}</span>
                <span style="font-size: 13px; color: #7C3AED; font-weight: 600; margin-left: 12px; font-family: 'Space Grotesk', sans-serif; white-space: nowrap;" id="copyStatus">📋 Copy</span>
            </div>
            <script>
                function copyLink() {{
                    navigator.clipboard.writeText("{invite_url}");
                    const status = document.getElementById("copyStatus");
                    status.innerText = "✅ Copied!";
                    setTimeout(() => {{
                        status.innerText = "📋 Copy";
                    }}, 2000);
                }}
            </script>
        """, height=52)

        st.markdown("#### Group Members")
        for member in get_members(selected_project_id):
            st.write(f"• **{member['name']}** ({member['email']})")

        st.divider()
        st.markdown("#### Assignment Briefs & Document Upload")
        
        uploaded_files = st.file_uploader("Upload assignment documents (TXT, PDF, DOCX)", type=["txt", "pdf", "docx"], accept_multiple_files=True, key=f"brief_upload_{selected_project_id}")

        if uploaded_files:
            if st.button("Save assignment documents", type="primary", key=f"save_doc_{selected_project_id}"):
                document_text = extract_documents(uploaded_files)
                if not document_text.strip():
                    st.warning("No readable text found in the files.")
                else:
                    st.session_state[f"document_{selected_project_id}"] = document_text
                    st.success("Assignment documents loaded.")
                    st.rerun()

        document_text = st.session_state.get(
            f"document_{selected_project_id}", ""
        )

        if document_text:
            st.success("Assignment documents loaded.")

            with st.expander("Preview document text"):
                st.text(document_text[:5000])

            if st.button(
                "Generate AI Task Suggestions",
                type="primary",
                key=f"gen_tasks_{selected_project_id}"
            ):
                existing_tasks = get_tasks(selected_project_id)

                if existing_tasks:
                    st.warning(
                        "This project already has tasks. Review the existing task board before generating more."
                    )
                else:
                    with st.spinner("AI is generating tasks..."):
                        try:
                            result = generate_project_tasks(
                                document_text,
                                selected_project_id
                            )

                            st.session_state[
                                f"ai_tasks_{selected_project_id}"
                            ] = result

                        except Exception as e:
                            st.error(f"AI generation failed: {e}")

        # Display AI-generated tasks for review
        ai_key = f"ai_tasks_{selected_project_id}"

        if ai_key in st.session_state:
            result = st.session_state[ai_key]
            tasks = result.get("tasks", [])

            st.subheader("Review AI Task Suggestions")

            for i, task in enumerate(tasks):
                with st.expander(f"{i + 1}. {task.get('title', 'Untitled task')}"):
                    st.write(task.get("description", ""))

                    st.write("**Marking criterion:**", task.get("criterion", ""))
                    st.write("**Suggested member:**", task.get("suggested_member", ""))
                    st.write("**Estimated effort:**", task.get("estimated_effort", ""))

                    if task.get("source_verified"):
                        st.success("Source quote verified")
                    else:
                        st.warning("Source quote could not be verified")

                    st.caption(task.get("source_quote", ""))

            if tasks and st.button(
                "Approve and Add Tasks",
                type="primary",
                key=f"approve_ai_{selected_project_id}"
            ):
                with get_db() as conn:
                    for task in tasks:
                        conn.execute(
                            """
                            INSERT INTO tasks
                            (project_id, title, description, status, created_at)
                            VALUES (?, ?, ?, 'To do', ?)
                            """,
                            (
                                selected_project_id,
                                task.get("title", "Untitled task"),
                                task.get("description", ""),
                                datetime.utcnow().isoformat()
                            )
                        )

                    conn.execute(
                        "UPDATE projects SET tasks_generated = 1 WHERE id = ?",
                        (selected_project_id,)
                    )

                del st.session_state[ai_key]
                st.success("Approved tasks added to the board!")
                st.rerun()
        
        st.divider()
        st.markdown("#### Collaborative Task Board")

        tasks = get_tasks(selected_project_id)
        total = len(tasks)
        done = sum(1 for t in tasks if t["status"] == "Done")
        in_progress = sum(1 for t in tasks if t["status"] == "In progress")

        m1, m2, m3 = st.columns(3)
        m1.metric("Total tasks", total)
        m2.metric("In progress", in_progress)
        m3.metric("Completed", done)

        if not tasks:
            st.info("No tasks yet. Upload briefs and click generate, or add tasks below.")
        else:
            for task in tasks:
                with st.container(border=True):
                    col_info, col_status, col_assignee = st.columns([3, 1, 1])

                    with col_info:
                        st.markdown(f"**{task['title']}**")
                        if task["description"]:
                            st.caption(task["description"])

                    with col_status:
                        new_status = st.selectbox("Status", ["To do", "In progress", "Done"], index=["To do", "In progress", "Done"].index(task["status"]) if task["status"] in ["To do", "In progress", "Done"] else 0, key=f"status_{task['id']}")
                        if new_status != task["status"]:
                            with get_db() as conn:
                                conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task["id"]))
                            st.rerun()

                    with col_assignee:
                        members = get_members(selected_project_id)
                        member_emails = [m["email"] for m in members]
                        member_names = {m["email"]: m["name"] for m in members}
                        current_assignee = task["assignee_email"]
                        assignee_options = ["Unassigned"] + member_emails
                        display_index = 0
                        if current_assignee in member_emails:
                            display_index = assignee_options.index(current_assignee)
                        selected_assign = st.selectbox("Assignee", assignee_options, format_func=lambda x: "Unassigned" if x == "Unassigned" else member_names.get(x, x), index=display_index if current_assignee in assignee_options else 0, key=f"assignee_{task['id']}")
                        new_assign_val = "" if selected_assign == "Unassigned" else selected_assign
                        if new_assign_val != current_assignee:
                            with get_db() as conn:
                                conn.execute("UPDATE tasks SET assignee_email = ? WHERE id = ?", (new_assign_val, task["id"]))
                            st.rerun()

        st.write("")
        with st.expander("Add Custom Task", expanded=False):
            with st.form(f"add_task_form_{selected_project_id}"):
                st.markdown("**Task Title**")
                custom_title = st.text_input("Task Title", placeholder="Brief task name", label_visibility="collapsed")
                
                st.markdown("**Task Description**")
                custom_desc = st.text_input("Task Description", placeholder="Details or deliverable notes", label_visibility="collapsed")
                
                add_task_submitted = st.form_submit_button("Add Task", type="primary")

            if add_task_submitted:
                if not custom_title.strip():
                    st.error("Please enter a task title.")
                else:
                    with get_db() as conn:
                        conn.execute(
                            "INSERT INTO tasks (project_id, title, description, status, created_at) VALUES (?, ?, ?, 'To do', ?)",
                            (selected_project_id, custom_title.strip(), custom_desc.strip(), datetime.utcnow().isoformat())
                        )
                    st.success("Task added.")
                    st.rerun()