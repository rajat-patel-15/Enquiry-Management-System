"""
=============================================================================
Project Title: Enquiry Management System
Description:   A simple, clean web application to capture, track, and update 
               client enquiries using Python Flask, SQLite, and Bootstrap 5.
Developer:     Rajat Patel (B.Tech CSE Intern, Vivekananda Global University)
Tenure:        6-Week Summer Internship Project
=============================================================================
"""

import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

# Initialize the Flask application
app = Flask(__name__)

# Secret key is required by Flask to handle session flash messages
app.secret_key = "internship_enquiry_system_secret_key"

# Database filename
DATABASE_NAME = "enquiries.db"


# ---------------------------------------------------------------------------
# DATABASE HELPER FUNCTIONS
# ---------------------------------------------------------------------------

# Function to get a connection to the SQLite database
def get_db_connection():
    # Connect to the local SQLite database file
    conn = sqlite3.connect(DATABASE_NAME)
    
    # Setting row_factory = sqlite3.Row allows accessing columns by name 
    # Example: row['name'] instead of index row[1]
    conn.row_factory = sqlite3.Row
    return conn


# Function to automatically create table and insert initial sample data on first run
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Step 1: Create the 'enquiries' table if it does not already exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            course_or_service TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            date_created TEXT NOT NULL
        )
    """)
    conn.commit()

    # Step 2: Check if table is empty. If yes, insert 5 realistic sample records
    cursor.execute("SELECT COUNT(*) FROM enquiries")
    row_count = cursor.fetchone()[0]

    if row_count == 0:
        sample_records = [
            (
                "Advocate Balachandran",
                "balachandran.law@gmail.com",
                "9400155031",
                "Web Development",
                "Need a legal case management portal with document upload facility.",
                "Contacted",
                "12-Jul-2026 10:30 AM"
            ),
            (
                "Surya Credit Cooperative Society",
                "admin@suryacoop.org.in",
                "9810244719",
                "School ERP",
                "Inquiry regarding member loan ledger portal and SMS alert gateway integration.",
                "Pending",
                "15-Jul-2026 02:15 PM"
            ),
            (
                "Dr. Rajesh Sharma",
                "dr.sharma@orthocare.in",
                "9910543210",
                "Web Development",
                "Looking for a patient appointment booking website with online payment.",
                "Pending",
                "18-Jul-2026 11:45 AM"
            ),
            (
                "Apex Diagnostic Laboratories",
                "info@apexdiagnostics.com",
                "9871120045",
                "Digital Marketing",
                "Need Google Ads campaign and local SEO to increase lab walk-in tests.",
                "Contacted",
                "20-Jul-2026 04:20 PM"
            ),
            (
                "Kaveri Logistics & Freight",
                "dispatch@kaverilogistics.com",
                "9818765432",
                "Custom Software",
                "Fleet tracking and vehicle fuel expense management system required.",
                "Closed",
                "22-Jul-2026 09:10 AM"
            ),
            (
                "Metro Dental Clinic",
                "info@metrodental.com",
                "9811224488",
                "Custom Software",
                "Looking for a custom patient booking and SMS reminder module.",
                "Contacted",
                "23-Jul-2026 11:30 AM"
            )
        ]

        # Insert all sample records into the database
        cursor.executemany("""
            INSERT INTO enquiries (name, email, phone, course_or_service, message, status, date_created)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, sample_records)
        conn.commit()
        print(">> Database initialized with sample enquiry records.")

    conn.close()


# ---------------------------------------------------------------------------
# APPLICATION ROUTES / CONTROLLERS
# ---------------------------------------------------------------------------

# Route 1: Public Contact / Inquiry Form (Home Page)
@app.route('/', methods=['GET', 'POST'])
def index():
    # Check if the user submitted the form via POST request
    if request.method == 'POST':
        # Collect values entered by the user in the HTML form
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        course_or_service = request.form.get('course_or_service', '').strip()
        message = request.form.get('message', '').strip()

        # Basic validation: ensure all fields have input
        if not name or not email or not phone or not course_or_service or not message:
            flash("Please fill in all the required fields.", "danger")
            return redirect(url_for('index'))

        # Get current date and 12-hour formatted time (e.g., '23-Jul-2026 11:30 AM')
        current_time = datetime.now().strftime("%d-%b-%Y %I:%M %p")

        # Insert the new enquiry into SQLite database with default status 'Pending'
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO enquiries (name, email, phone, course_or_service, message, status, date_created)
            VALUES (?, ?, ?, ?, ?, 'Pending', ?)
        """, (name, email, phone, course_or_service, message, current_time))
        conn.commit()
        conn.close()

        # Display a success alert on the page after redirecting
        flash(f"Thank you, {name}! Your enquiry has been received. Our team will contact you soon.", "success")
        return redirect(url_for('index'))

    # If it's a normal GET request, just display the empty form page
    return render_template('index.html')


# Route 2: Admin Dashboard - View All Enquiries and Statistics
@app.route('/admin')
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Fetch counts for the statistic cards at the top
    total_enquiries = cursor.execute("SELECT COUNT(*) FROM enquiries").fetchone()[0]
    pending_count = cursor.execute("SELECT COUNT(*) FROM enquiries WHERE status = 'Pending'").fetchone()[0]
    contacted_count = cursor.execute("SELECT COUNT(*) FROM enquiries WHERE status = 'Contacted'").fetchone()[0]
    closed_count = cursor.execute("SELECT COUNT(*) FROM enquiries WHERE status = 'Closed'").fetchone()[0]

    # 2. Check if a status filter is passed in the URL (e.g., /admin?status=Pending)
    status_filter = request.args.get('status', 'All')

    # 3. Query the enquiries list sorted newest first (highest ID first)
    if status_filter in ['Pending', 'Contacted', 'Closed']:
        cursor.execute("""
            SELECT * FROM enquiries 
            WHERE status = ? 
            ORDER BY id DESC
        """, (status_filter,))
    else:
        # Show all enquiries
        status_filter = 'All'
        cursor.execute("SELECT * FROM enquiries ORDER BY id DESC")

    all_enquiries = cursor.fetchall()
    conn.close()

    # Pass the data to dashboard.html template
    return render_template(
        'dashboard.html',
        enquiries=all_enquiries,
        total=total_enquiries,
        pending=pending_count,
        contacted=contacted_count,
        closed=closed_count,
        current_filter=status_filter
    )


# Route 3: Edit Status Page - Change status of an enquiry
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_enquiry(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if user submitted the update form
    if request.method == 'POST':
        new_status = request.form.get('status')

        # Update the status column in SQLite for this specific ID
        cursor.execute("""
            UPDATE enquiries 
            SET status = ? 
            WHERE id = ?
        """, (new_status, id))
        conn.commit()
        conn.close()

        flash(f"Status for Enquiry #{id} was updated to '{new_status}' successfully!", "success")
        return redirect(url_for('admin_dashboard'))

    # If GET request: fetch the specific record to display its details in the edit form
    cursor.execute("SELECT * FROM enquiries WHERE id = ?", (id,))
    enquiry = cursor.fetchone()
    conn.close()

    # If the record doesn't exist, redirect back to dashboard
    if enquiry is None:
        flash(f"Enquiry #{id} not found.", "warning")
        return redirect(url_for('admin_dashboard'))

    return render_template('edit.html', enquiry=enquiry)


# Route 4: Delete Enquiry - Remove a record from database
@app.route('/delete/<int:id>')
def delete_enquiry(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Delete the record with the given ID
    cursor.execute("DELETE FROM enquiries WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash(f"Enquiry #{id} has been permanently deleted.", "info")
    return redirect(url_for('admin_dashboard'))


# ---------------------------------------------------------------------------
# APPLICATION ENTRY POINT
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    # Initialize the database table and dummy records
    init_db()

    # Run local development server
    # debug=True automatically reloads code changes and shows helpful error pages
    app.run(debug=True, port=5000)
