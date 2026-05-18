import sqlite3
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, g, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "cleancity_super_secret_2025"
DATABASE = 'garbage.db'
UPLOAD_COMPLAINTS = 'static/uploads/complaints'
UPLOAD_CLEANED = 'static/uploads/cleaned'


for folder in [UPLOAD_COMPLAINTS, UPLOAD_CLEANED]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        
        # Teams Table
        db.execute('''CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, area TEXT, contact TEXT, team_code TEXT UNIQUE)''')
        
        # Complaints Table
        db.execute('''CREATE TABLE IF NOT EXISTS complaints (  
            id INTEGER PRIMARY KEY AUTOINCREMENT,  
            area TEXT, problem TEXT, priority TEXT, date TEXT,  
            status TEXT, image_path TEXT, map_link TEXT,  
            assigned_team_id INTEGER, cleaned_image_path TEXT,  
            cleaned_date TEXT, admin_remark TEXT,  
            FOREIGN KEY(assigned_team_id) REFERENCES teams(id))''')
        
        # Reviews Table 
        db.execute('''CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER,
            rating INTEGER,
            comment TEXT,
            reviewer_name TEXT,
            date TEXT,
            is_approved INTEGER DEFAULT 1,
            FOREIGN KEY(complaint_id) REFERENCES complaints(id))''')
        
        # Seeding Teams
        cursor = db.execute('SELECT count(*) FROM teams')  
        if cursor.fetchone()[0] == 0:  
            teams_data = [
                ('Muradpur Team', 'Muradpur', '01700000001', 'muradpur123'),
                ('Bayezid Team', 'Bayezid', '01700000002', 'bayezid123'),
                ('Agrabad Team', 'Agrabad', '01700000003', 'agrabad123'),
                ('Panchlaish Team', 'Panchlaish', '01700000004', 'panchlaish123'),
                ('Halishahar Team', 'Halishahar', '01700000005', 'halishahar123'),
                ('Patenga Team', 'Patenga', '01700000006', 'patenga123'),
                ('Bakalia Team', 'Bakalia', '01700000007', 'bakalia123'),
                ('Chawkbazar Team', 'Chawkbazar', '01700000008', 'chawkbazar123'),
                ('Andarkilla Team', 'Andarkilla', '01700000009', 'andarkilla123'),
                ('Kotwali Team', 'Kotwali', '01700000010', 'kotwali123'),
                ('Pahartali Team', 'Pahartali', '01700000011', 'pahartali123'),
                ('Sadarghat Team', 'Sadarghat', '01700000012', 'sadarghat123'),
                ('Kalurghat Team', 'Kalurghat', '01700000013', 'kalurghat123'),
                ('Khulshi Team', 'Khulshi', '01700000014', 'khulshi123'),
                ('Nasirabad Team', 'Nasirabad', '01700000015', 'nasirabad123'),
                ('Bahaddarhat Team', 'Bahaddarhat', '01700000016', 'bahaddarhat123'),
                ('Faujdarhat Team', 'Faujdarhat', '01700000017', 'faujdarhat123'),
                ('Dampara Team', 'Dampara', '01700000018', 'dampara123'),
                ('Raozan Team', 'Raozan', '01700000019', 'raozan123'),
                ('Oxygen Team', 'Oxygen', '01700000020', 'oxygen123')
            ]  
            db.executemany('INSERT INTO teams (name, area, contact, team_code) VALUES (?, ?, ?, ?)', teams_data)
            db.commit()

def ensure_tables():
    """Ensure new tables exist in existing databases"""
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_id INTEGER,
        rating INTEGER,
        comment TEXT,
        reviewer_name TEXT,
        date TEXT,
        is_approved INTEGER DEFAULT 1,
        FOREIGN KEY(complaint_id) REFERENCES complaints(id))''')
    db.commit()

# PUBLIC ROUTES
@app.route('/')
def index():
    db = get_db()
    solved_complaints = db.execute(
        "SELECT * FROM complaints WHERE status='Solved' ORDER BY id DESC LIMIT 6"
    ).fetchall()
    
    # Homepage ea user review dekha
    reviews = db.execute(
        "SELECT r.*, c.area FROM reviews r LEFT JOIN complaints c ON r.complaint_id = c.id WHERE r.is_approved = 1 ORDER BY r.id DESC LIMIT 3"
    ).fetchall()
    return render_template('index.html', solved_complaints=solved_complaints, reviews=reviews)

# WEEK 4: Complaint Submission
@app.route('/submit', methods=['POST'])
def submit_complaint():
    if request.method == 'POST':
        area = request.form.get('area')
        problem = request.form.get('problem')
        priority = request.form.get('priority')
        map_link = request.form.get('map_link')
        file = request.files.get('image')
        
        # Image handle
        filename = None  
        if file and file.filename != '':  
            # unic filename er jonno timestamp add
            ext = file.filename.rsplit('.', 1)[1].lower()  
            filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}")  
            file.save(os.path.join(UPLOAD_COMPLAINTS, filename))  
        
        # database save
        db = get_db()  
        cursor = db.execute('''INSERT INTO complaints (area, problem, priority, date, status, image_path, map_link)   
            VALUES (?, ?, ?, ?, ?, ?, ?)''',   
            (area, problem, priority, datetime.now().strftime("%Y-%m-%d %H:%M"), 'Pending', filename, map_link))
        db.commit()
        
        complaint_id = cursor.lastrowid
        flash(f"✅ Complaint submitted successfully! Your Tracking ID is #{complaint_id}", "success")
        return redirect(url_for('success_page', complaint_id=complaint_id))

# After complain submit
@app.route('/success/<int:complaint_id>')
def success_page(complaint_id):
    db = get_db()
    complaint = db.execute('SELECT * FROM complaints WHERE id = ?', (complaint_id,)).fetchone()
    if not complaint:
        flash("❌ Complaint not found!", "danger")
        return redirect(url_for('index'))
    return render_template('success.html', complaint=complaint)

# Track korar jonno
@app.route('/track', methods=['GET', 'POST'])
def track_complaint():
    complaint = None
    review = None
    if request.method == 'POST':
        complaint_id = request.form.get('complaint_id')
        db = get_db()
        complaint = db.execute('SELECT * FROM complaints WHERE id = ?', (complaint_id,)).fetchone()
        if complaint:
            # Check if already reviewed
            review = db.execute('SELECT * FROM reviews WHERE complaint_id = ?', (complaint_id,)).fetchone()
        else:
            flash("❌ No complaint found with that ID. Please check and try again.", "danger")
    return render_template('track.html', complaint=complaint, review=review)

# Review
@app.route('/submit_review', methods=['POST'])
def submit_review():
    complaint_id = request.form.get('complaint_id')
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    reviewer_name = request.form.get('reviewer_name', 'Anonymous')
    
    if not rating:
        flash("❌ Please select a rating!", "danger")
        return redirect(url_for('track_complaint'))
    
    db = get_db()
    # Check if review already exists
    existing = db.execute('SELECT * FROM reviews WHERE complaint_id = ?', (complaint_id,)).fetchone()
    if existing:
        flash("⚠️ You have already submitted a review for this complaint.", "warning")
    else:
        db.execute('''INSERT INTO reviews (complaint_id, rating, comment, reviewer_name, date, is_approved) 
            VALUES (?, ?, ?, ?, ?, 1)''',
            (complaint_id, int(rating), comment, reviewer_name, datetime.now().strftime("%Y-%m-%d %H:%M")))
        db.commit()
        flash("⭐ Thank you for your feedback! Your review helps improve our service.", "success")
    
    return redirect(url_for('track_complaint'))

# ADMIN ROUTES 
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('username') == "Bitbond" and request.form.get('password') == "bitbond123":
            session['admin_logged_in'] = True
            flash("✅ Welcome back, Admin!", "success")
            return redirect(url_for('admin_dashboard'))
        flash("❌ Invalid Admin Credentials!", "danger")
    return render_template('login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    
    # Stat calculations(total complaints,pending & solved count) for dashboard cards
    total = db.execute('SELECT COUNT(*) FROM complaints').fetchone()[0]
    pending = db.execute('SELECT COUNT(*) FROM complaints WHERE status="Pending"').fetchone()[0]
    in_progress = db.execute('SELECT COUNT(*) FROM complaints WHERE status="In Progress"').fetchone()[0]
    resolved = db.execute('SELECT COUNT(*) FROM complaints WHERE status="Resolved"').fetchone()[0]
    solved = db.execute('SELECT COUNT(*) FROM complaints WHERE status="Solved"').fetchone()[0]
    complaints = db.execute('SELECT * FROM complaints ORDER BY id DESC').fetchall()
    
    # Get all reviews for admin
    reviews = db.execute(
        "SELECT r.*, c.area, c.id as complaint_id FROM reviews r LEFT JOIN complaints c ON r.complaint_id = c.id ORDER BY r.id DESC"
    ).fetchall()
    return render_template('admin_dashboard.html', total=total, pending=pending, 
                         in_progress=in_progress, resolved=resolved, solved=solved, 
                         complaints=complaints, reviews=reviews)

# WEEK 6 : View Detail Route
@app.route('/admin/complaint/<int:id>')
def view_complaint(id):
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    #show complaint data
    complaint = db.execute('''SELECT c.*, t.name as team_name FROM complaints c
        LEFT JOIN teams t ON c.assigned_team_id = t.id
        WHERE c.id = ?''', (id,)).fetchone()
    teams = db.execute('SELECT * FROM teams').fetchall()
    # Get review if exists
    review = db.execute('SELECT * FROM reviews WHERE complaint_id = ?', (id,)).fetchone()
    return render_template('complaint_detail.html', complaint=complaint, teams=teams, review=review)

# WEEK 6 : Assign Team 
@app.route('/admin/assign_team', methods=['POST'])
def assign_team():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    db.execute('UPDATE complaints SET assigned_team_id = ?, status = "In Progress" WHERE id = ?',
        (request.form.get('team_id'), request.form.get('complaint_id')))
    db.commit()
    flash("✅ Team assigned successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# WEEK 7 : Solved
@app.route('/admin/approve/<int:id>')
def approve_complaint(id):
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    db.execute('UPDATE complaints SET status = "Solved" WHERE id = ?', (id,))
    db.commit()
    flash("✅ Complaint marked as Solved!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_complaint/<int:id>')
def delete_complaint(id):
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    # Delete related
    db.execute('DELETE FROM reviews WHERE complaint_id = ?', (id,))
    db.execute('DELETE FROM complaints WHERE id = ?', (id,))
    db.commit()
    flash("🗑️ Complaint deleted successfully!", "info")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_review/<int:id>')
def delete_review(id):
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db = get_db()
    db.execute('DELETE FROM reviews WHERE id = ?', (id,))
    db.commit()
    flash("🗑️ Review deleted successfully!", "info")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash("👋 Logged out successfully.", "info")
    return redirect(url_for('index'))

#  WORKER ROUTES 
@app.route('/worker/login', methods=['GET', 'POST'])
def worker_login():
    if request.method == 'POST':
        team_code = request.form.get('team_code')
        db = get_db()
        team = db.execute('SELECT * FROM teams WHERE team_code = ?', (team_code,)).fetchone()
        if team:
            session['worker_id'] = team['id']
            session['worker_name'] = team['name']
            flash(f"✅ Welcome, {team['name']}!", "success")
            return redirect(url_for('worker_portal'))
        flash("❌ Invalid Team Code!", "danger")
    return render_template('worker_login.html')

@app.route('/worker/portal')
def worker_portal():
    if not session.get('worker_id'): return redirect(url_for('worker_login'))
    db = get_db()
    tasks = db.execute("SELECT * FROM complaints WHERE assigned_team_id = ? AND status IN ('In Progress', 'Resolved') ORDER BY id DESC",
        (session['worker_id'],)).fetchall()
    return render_template('worker_portal.html', tasks=tasks)

@app.route('/worker/submit_work', methods=['POST'])
def submit_work():
    if not session.get('worker_id'): return redirect(url_for('worker_login'))
    complaint_id = request.form.get('complaint_id')
    file = request.files.get('cleaned_image')
    
    if file and file.filename != '':  
        ext = file.filename.rsplit('.', 1)[1].lower()  
        filename = secure_filename(f"clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}")  
        file.save(os.path.join(UPLOAD_CLEANED, filename))  
        
        db = get_db()  
        db.execute('UPDATE complaints SET status = "Resolved", cleaned_image_path = ?, cleaned_date = ? WHERE id = ?',   
                   (filename, datetime.now().strftime("%Y-%m-%d %H:%M"), complaint_id))  
        db.commit()  
        flash("✅ Proof of work submitted successfully! Waiting for admin approval.", "success")  
    return redirect(url_for('worker_portal'))

@app.route('/worker/logout')
def worker_logout():
    session.pop('worker_id', None)
    session.pop('worker_name', None)
    flash("👋 Logged out successfully.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    else:
        with app.app_context():
            ensure_tables()
    app.run(debug=True)