import streamlit as st
import pandas as pd
import pickle
import sqlite3
import bcrypt
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# -----------------------------

# -----------------------------
# Modern Blue UI Styling
# -----------------------------

st.markdown("""
<style>

    /* Main Background */
    .stApp {
        background: #f0f5ff;
        color: #1e293b;
    }

    /* Main Content Area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* Headings */
    h1, h2, h3 {
        color: #123b70 !important;
        font-weight: 700;
    }

    /* Paragraphs and Labels */
    p, label, span {
        color: #334155;
    }

    /* Buttons */
    div.stButton > button {
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 22px;
        font-weight: 600;
        transition: 0.2s ease;
    }

    div.stButton > button:hover {
        background: #1e40af;
        color: white;
        border: none;
        transform: translateY(-1px);
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background: white;
        padding: 20px;
        border-radius: 14px;
        border: 1px solid #dbeafe;
        box-shadow: 0 3px 12px rgba(37, 99, 235, 0.07);
    }

    /* Data Tables */
    div[data-testid="stDataFrame"] {
        border: 1px solid #dbeafe;
        border-radius: 12px;
        overflow: hidden;
    }

    /* Input Fields */
    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea {
        border-radius: 8px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #e5efff;
        border-right: 1px solid #dbeafe;
    }

    /* Horizontal Divider */
    hr {
        border-color: #dbeafe;
    }

</style>
""", unsafe_allow_html=True)


# -----------------------------
# Database Setup
# -----------------------------

conn = sqlite3.connect(
    "prediction_history.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT,
        assignment_name TEXT,
        attendance INTEGER,
        submission_rate INTEGER,
        days_remaining INTEGER,
        prediction TEXT,
        risk_level TEXT,
        created_at TEXT
    )
""")

conn.commit()
# -----------------------------
# Teacher Login Database
# -----------------------------

cursor.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
""")

conn.commit()
# Add role column to teachers table

cursor.execute("PRAGMA table_info(teachers)")
teacher_columns = [row[1] for row in cursor.fetchall()]

if "role" not in teacher_columns:
    cursor.execute(
        "ALTER TABLE teachers ADD COLUMN role TEXT DEFAULT 'Teacher'"
    )
    conn.commit()
    # Make harsh_admin an Admin
cursor.execute(
    "UPDATE teachers SET role = 'Admin' WHERE username = ?",
    ("harsh_admin",)
)
conn.commit()
    # Make harsh_admin an Admin

# Add teacher username to prediction records

cursor.execute("PRAGMA table_info(predictions)")
columns = [row[1] for row in cursor.fetchall()]

if "teacher_username" not in columns:
    cursor.execute(
        "ALTER TABLE predictions ADD COLUMN teacher_username TEXT"
    )
    conn.commit()


# -----------------------------
# Load trained model
# -----------------------------

with open("assignment_model.pkl", "rb") as file:
    model = pickle.load(file)


# -----------------------------
# Page configuration
# -----------------------------

st.set_page_config(
    page_title="Student Assignment Predictor",
    page_icon="🎓",
    layout="wide"
)


# -----------------------------
# Title
# -----------------------------

# -----------------------------
# Teacher Login System
# -----------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "teacher_username" not in st.session_state:
    st.session_state.teacher_username = ""

if "teacher_role" not in st.session_state:
    st.session_state.teacher_role = "Teacher"

if not st.session_state.logged_in:

    st.title("🎓 Teacher Login")

    login_tab, register_tab = st.tabs(
        ["Login", "Create Account"]
    )

    with login_tab:

        username = st.text_input("Username", key="login_user")
        password = st.text_input(
            "Password",
            type="password",
            key="login_pass"
        )

        if st.button("Login"):

            cursor.execute(
                "SELECT password, role FROM teachers WHERE username = ?",
                (username,)
            )

            teacher = cursor.fetchone()

            if teacher and bcrypt.checkpw(
                password.encode("utf-8"),
                teacher[0].encode("utf-8")
            ):
                st.session_state.logged_in = True
                st.session_state.teacher_username = username
                st.session_state.teacher_role = teacher[1]
                st.success("Login successful!")
                st.rerun()

            else:
                st.error("Invalid username or password.")

        with register_tab:

            new_username = st.text_input(
               "Create Username",
               key="register_user"
           )

        new_password = st.text_input(
            "Create Password",
            type="password",
            key="register_pass"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            key="confirm_pass"
        )

        if st.button("Create Teacher Account"):

            if not new_username.strip() or not new_password:
                st.error("Please enter username and password.")

            elif new_password != confirm_password:
                st.error("Passwords do not match.")

            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters.")

            else:
                hashed_password = bcrypt.hashpw(
                    new_password.encode("utf-8"),
                    bcrypt.gensalt()
                ).decode("utf-8")

                try:
                   cursor.execute(
                     "INSERT INTO teachers (username, password, role) VALUES (?, ?, ?)",
                     (new_username.strip(), hashed_password, "Teacher")
                   )
                   conn.commit()
                   st.success("Account created! You can now log in.")

                except sqlite3.IntegrityError:
                  st.error("Username already exists.")

        st.stop()
# -----------------------------
# Admin Dashboard
# -----------------------------

if st.session_state.teacher_role == "Admin":

    st.header("🛠️ Admin Dashboard")

    total_teachers = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM teachers",
        conn
    ).iloc[0]["total"]

    total_predictions = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM predictions",
        conn
    ).iloc[0]["total"]

    col1, col2 = st.columns(2)

    with col1:
        st.metric("👨‍🏫 Total Teachers", int(total_teachers))

    with col2:
        st.metric("📊 Total Predictions", int(total_predictions))

    st.subheader("👨‍🏫 Registered Teachers")

    teachers_df = pd.read_sql_query(
        """
        SELECT id, username, role
        FROM teachers
        ORDER BY id DESC
        """,
        conn
    )

    st.dataframe(
        teachers_df,
        use_container_width=True
    )

    st.divider()
# -----------------------------
# Admin Dashboard
# -----------------------------

if st.session_state.teacher_role == "Admin":

    st.header("🛠️ Admin Dashboard")

    total_teachers = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM teachers", conn
    ).iloc[0]["total"]

    total_predictions = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM predictions", conn
    ).iloc[0]["total"]

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Teachers", int(total_teachers))

    with col2:
        st.metric("Total Predictions", int(total_predictions))

    st.subheader("Registered Teachers")

    teachers_df = pd.read_sql_query(
        "SELECT id, username, role FROM teachers ORDER BY id DESC",
        conn
    )

    st.dataframe(teachers_df, use_container_width=True)

    st.divider()    
st.title("🎓 Student Assignment Completion Predictor")
st.markdown(
    f"### 👋 Welcome, {st.session_state.teacher_username}!"
)

st.write(
    "An AI-based system that helps teachers identify "
    "students who may be at risk of missing an assignment deadline."
)

st.divider()
col1, col2 = st.columns([5, 1])

with col2:
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.rerun()


# -----------------------------
# Student Information
# -----------------------------

st.header("📝 Student Information")

col1, col2 = st.columns(2)

with col1:
    student_name = st.text_input(
        "Student Name",
        placeholder="Enter student name"
    )

with col2:
    assignment_name = st.text_input(
        "Assignment Name",
        placeholder="Enter assignment name"
    )


# -----------------------------
# Prediction Inputs
# -----------------------------

st.subheader("📊 Academic Information")

col1, col2, col3 = st.columns(3)

with col1:
    attendance = st.number_input(
        "Attendance (%)",
        min_value=0,
        max_value=100,
        value=80
    )

with col2:
    submission_rate = st.number_input(
        "Previous Submission Rate (%)",
        min_value=0,
        max_value=100,
        value=75
    )

with col3:
    days_remaining = st.number_input(
        "Days Remaining",
        min_value=0,
        max_value=30,
        value=5
    )


# -----------------------------
# Prediction
# -----------------------------

if st.button(
    "🔍 Predict Assignment Status",
    width="stretch"
):

    # Check student information
    if student_name.strip() == "":
        st.warning("Please enter the student's name.")

    elif assignment_name.strip() == "":
        st.warning("Please enter the assignment name.")

    else:

        # Prepare input data
        input_data = pd.DataFrame(
            [[
                attendance,
                submission_rate,
                days_remaining
            ]],
            columns=[
                "Attendance",
                "Previous_Submission_Rate",
                "Days_Remaining"
            ]
        )

        # Make prediction
        prediction = model.predict(input_data)[0]
                # Save prediction in database

        risk_level = "LOW" if prediction == "On-Time" else "HIGH"
        
        cursor.execute("""
            INSERT INTO predictions (
                student_name,
                assignment_name,
                attendance,
                submission_rate,
                days_remaining,
                prediction,
                risk_level,
                created_at,
                teacher_username
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student_name,
            assignment_name,
            attendance,
            submission_rate,
            days_remaining,
            prediction,
            risk_level,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            st.session_state.teacher_username
        ))

        conn.commit()

        

        # Display student information
        st.divider()

        st.header("📋 Prediction Report")

        st.write(
            f"**Student:** {student_name}"
        )

        st.write(
            f"**Assignment:** {assignment_name}"
        )


        # -----------------------------
        # Prediction result
        # -----------------------------

        if prediction == "On-Time":

            st.success(
                "🟢 Prediction: ON-TIME"
            )
            st.metric(
    "Risk Level",
    "LOW"
)

            st.write(
                "The student is likely to complete "
                "the assignment within the deadline."
            )

        else:

            st.error(
                "🔴 Prediction: AT-RISK"
            )
            st.metric(
    "Risk Level",
    "HIGH"
)

            st.warning(
                "The student may miss the assignment deadline."
            )

            st.info(
                "💡 Recommendation: Send an early academic reminder."
            )


# -----------------------------
# About the project
# -----------------------------

st.divider()

st.header("🤖 About the AI Model")

st.write(
    """
    This project uses a Decision Tree Classifier to predict
    whether a student is likely to complete an assignment
    on time or become at risk.

    The model uses three important factors:

    • Attendance
    • Previous Submission Rate
    • Days Remaining
    """
)


# -----------------------------
# Project workflow
# -----------------------------

st.header("⚙️ How It Works")

st.write(
    """
    1. Teacher enters the student's information.
    2. The system collects attendance, submission history,
       and remaining days.
    3. The Decision Tree ML model analyzes the data.
    4. The system predicts On-Time or At-Risk.
    5. Teachers can provide an early reminder to students
       predicted to be At-Risk.
    """
)

# -----------------------------
# Prediction History Dashboard
# -----------------------------

st.divider()

st.header("📚 Prediction History")

search_name = st.text_input("🔍 Search Student by Name")

search_assignment = st.text_input("🔍 Search by Assignment Name")


history_df = pd.read_sql_query(
    """
    SELECT * FROM predictions
    WHERE student_name LIKE ?
    AND assignment_name LIKE ?
    AND teacher_username = ?
    ORDER BY id DESC
    """,
    conn,
    params=(
        f"%{search_name}%",
        f"%{search_assignment}%",
        st.session_state.teacher_username
    )
)


if not history_df.empty:

    total = len(history_df)
    on_time = len(history_df[history_df["prediction"] == "On-Time"])
    at_risk = len(history_df[history_df["prediction"] == "At-Risk"])

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Predictions", total)
    col2.metric("On-Time Students", on_time)
    col3.metric("At-Risk Students", at_risk)
    st.subheader("📊 Prediction Overview")

    chart_data = pd.DataFrame({
      "Status": ["On-Time", "At-Risk"],
      "Students": [on_time, at_risk]
    })

    st.bar_chart(
       chart_data.set_index("Status")
    )
    st.subheader("🚨 At-Risk Students Alert")

    at_risk_students = history_df[
      history_df["risk_level"] == "HIGH"
    ]

    if not at_risk_students.empty:

        st.warning(
          f"{len(at_risk_students)} prediction record(s) need attention!"
        )

        st.subheader("📩 Send Assignment Reminder")

        for index, student in at_risk_students.iterrows():

            st.write(
              f"**Student:** {student['student_name']} | "
              f"**Assignment:** {student['assignment_name']}"
            )

            reminder_message = (
             f"Hello {student['student_name']}, "
             f"your assignment '{student['assignment_name']}' "
             f"is due in {student['days_remaining']} day(s). "
             "Please complete it before the deadline."
            )

            st.text_area(
              "Reminder Message (Copy and Send)",
              value=reminder_message,
              key=f"reminder_{student['id']}"
            )

        st.dataframe(
          at_risk_students[
            ["student_name", "assignment_name", "days_remaining", "risk_level"]
          ],
          width="stretch",
          hide_index=True
        )

    else:
      st.success("No At-Risk students found!")
    st.subheader("All Prediction Records")
        # -----------------------------
    # Student Performance Report
    # -----------------------------

    st.divider()

    st.subheader("👨‍🎓 Student Performance Report")

    report_student = st.selectbox(
        "Select Student",
        sorted(history_df["student_name"].dropna().unique())
    )

    student_report = history_df[
        history_df["student_name"] == report_student
    ]

    report_total = len(student_report)

    report_on_time = len(
        student_report[student_report["prediction"] == "On-Time"]
    )

    report_at_risk = len(
        student_report[student_report["prediction"] == "At-Risk"]
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Assignments", report_total)
    col2.metric("On-Time", report_on_time)
    col3.metric("At-Risk", report_at_risk)

    st.write("**Assignment-wise Performance**")

    st.dataframe(
        student_report[
            ["assignment_name", "attendance", "submission_rate",
             "days_remaining", "prediction", "risk_level"]
        ],
        width="stretch",
        hide_index=True
    )

    st.dataframe(
        history_df,
        width="stretch",
        hide_index=True
    )
        # Download Student PDF Report

    pdf_buffer = BytesIO()

    pdf = canvas.Canvas(pdf_buffer, pagesize=letter)

    pdf.setTitle("Student Performance Report")

    pdf.drawString(50, 750, "STUDENT PERFORMANCE REPORT")
    pdf.drawString(50, 710, f"Student Name: {report_student}")
    pdf.drawString(50, 680, f"Total Assignments: {report_total}")
    pdf.drawString(50, 650, f"On-Time: {report_on_time}")
    pdf.drawString(50, 620, f"At-Risk: {report_at_risk}")

    pdf.drawString(50, 570, "Assignment Details:")

    y = 540

    for index, row in student_report.iterrows():

        pdf.drawString(
            50,
            y,
            f"{row['assignment_name']} - {row['prediction']}"
        )

        y -= 25

        if y < 50:
            pdf.showPage()
            y = 750

    pdf.save()

    pdf_buffer.seek(0)

    st.download_button(
        label="📄 Download Student PDF Report",
        data=pdf_buffer,
        file_name=f"{report_student}_performance_report.pdf",
        mime="application/pdf"
    )

    csv_data = history_df.to_csv(index=False)

    st.download_button(
        label="📥 Download Prediction History",
        data=csv_data,
        file_name="prediction_history.csv",
        mime="text/csv"
    )   

    
