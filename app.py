from flask import Flask, render_template, request, redirect, url_for, jsonify, abort, session, g
from markupsafe import escape
import sqlite3
import os
import json
from datetime import datetime, timedelta
from functools import wraps
import re
import bcrypt

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session management

def init_db():
    create_db = not os.path.exists(DB_NAME)
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key support
    c = conn.cursor()
    
    if create_db:
        # Create users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        
        # Create trips table with foreign key to users
        c.execute('''
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                destination TEXT NOT NULL,
                arrival_date TEXT NOT NULL,
                departure_date TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Create stops table with foreign keys to both trips and users
        c.execute('''
            CREATE TABLE IF NOT EXISTS stops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                time TEXT NOT NULL,
                date TEXT NOT NULL,
                destination TEXT NOT NULL,
                route TEXT NOT NULL,
                FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Create route_steps table with foreign key to stops
        c.execute('''
            CREATE TABLE IF NOT EXISTS route_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stop_id INTEGER NOT NULL,
                step_order INTEGER NOT NULL,
                step_text TEXT NOT NULL,
                FOREIGN KEY (stop_id) REFERENCES stops(id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
    conn.close()

# Database configuration
DB_NAME = 'voya.db'
init_db()  # Initialize database with proper schema

# Ensure SQLite connections have foreign key support enabled
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Clear any existing session data
            session.clear()
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def authenticated_user_redirect():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return None

@app.before_request
def before_request():
    # Add security headers to prevent caching of sensitive pages
    if request.endpoint in ['login', 'register', 'dashboard']:
        g.response_headers = {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    
    # Prevent access to auth pages if already logged in
    if request.endpoint in ['login', 'register'] and 'user_id' in session:
        return redirect(url_for('dashboard'))

@app.after_request
def after_request(response):
    # Add security headers from before_request
    if hasattr(g, 'response_headers'):
        for key, value in g.response_headers.items():
            response.headers[key] = value
    return response

def is_valid_password(password):
    # At least 8 characters long
    # Contains at least one uppercase and one lowercase letter
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    return True

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect if already logged in
    redirect_response = authenticated_user_redirect()
    if redirect_response:
        return redirect_response
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return render_template('login.html', error='All fields are required')
            
        conn = get_db_connection()
        c = conn.cursor()
        # Use parameterized query to prevent SQL injection
        c.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user[1]):
            session.clear()  # Clear any existing session first
            session['user_id'] = user[0]
            session['username'] = username
            session.permanent = True  # Make session persistent
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Redirect if already logged in
    redirect_response = authenticated_user_redirect()
    if redirect_response:
        return redirect_response
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not password or not confirm_password:
            return render_template('register.html', error='All fields are required')
        
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')
        
        if not is_valid_password(password):
            return render_template('register.html', 
                                error='Password must be at least 8 characters long and contain uppercase and lowercase letters')
        
        conn = get_db_connection()
        c = conn.cursor()
        
        try:
            # Check if username exists using parameterized query
            c.execute("SELECT id FROM users WHERE username = ?", (username,))
            if c.fetchone():
                return render_template('register.html', error='Username already exists')
            
            # Hash password and create new user
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                     (username, hashed))
            conn.commit()
            
            # Set up secure session
            session.clear()
            session['user_id'] = c.lastrowid
            session['username'] = username
            session.permanent = True
            
            return redirect(url_for('dashboard'))
        except Exception as e:
            conn.rollback()
            return render_template('register.html', error='Registration failed')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    # Clear the entire session
    session.clear()
    return redirect(url_for('login'))

@app.route("/")
@login_required
def dashboard():
    conn = get_db_connection()
    c = conn.cursor()
bri    c.execute("SELECT id, user_id, destination, arrival_date, departure_date FROM trips WHERE user_id = ?", (session['user_id'],))
    trips = c.fetchall()
    trip_count = len(trips)
    conn.close()
    return render_template("dashboard.html", username=session['username'], trips=trips, trips_json=json.dumps(trips), trip_count=trip_count)


@app.route("/add", methods=["POST"])
@login_required
def add_trip():
    destination = request.form.get("destination")
    arrival = request.form.get("arrival")
    departure = request.form.get("departure")

    if destination and arrival and departure:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT INTO trips (user_id, destination, arrival_date, departure_date) VALUES (?, ?, ?, ?)",
                  (session['user_id'], destination, arrival, departure))
        conn.commit()
        conn.close()
    return redirect(url_for("dashboard"))


@app.route("/delete/<int:trip_id>")
@login_required
def delete_trip(trip_id):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        # Verify trip belongs to user
        c.execute("SELECT id FROM trips WHERE id = ? AND user_id = ?", (trip_id, session['user_id']))
        if not c.fetchone():
            return "Trip not found", 404

        # First get all stop IDs for this trip
        c.execute("SELECT id FROM stops WHERE trip_id = ?", (trip_id,))
        stop_ids = [row[0] for row in c.fetchall()]

        # Delete all route steps for these stops
        for stop_id in stop_ids:
            c.execute("DELETE FROM route_steps WHERE stop_id = ?", (stop_id,))

        # Delete all stops for this trip
        c.execute("DELETE FROM stops WHERE trip_id = ?", (trip_id,))

        # Finally delete the trip itself
        c.execute("DELETE FROM trips WHERE id = ?", (trip_id,))

        conn.commit()
    except Exception as e:
        conn.rollback()
        return "Error deleting trip", 500
    finally:
        conn.close()
    return redirect(url_for("dashboard"))


@app.route("/trip/<int:trip_id>", methods=["GET", "POST"])
@login_required
def itinerary(trip_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, destination, arrival_date, departure_date FROM trips WHERE id = ? AND user_id = ?", 
             (trip_id, session['user_id']))
    trip = c.fetchone()
    if not trip:
        conn.close()
        return "Trip not found", 404
    arrival = datetime.strptime(trip[2], "%Y-%m-%d")
    departure = datetime.strptime(trip[3], "%Y-%m-%d")
    num_days = (departure - arrival).days + 1
    days = [(arrival + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(num_days)]

    # Get selected day from query param, default to first day
    selected_day = request.args.get('day')
    if selected_day not in days:
        selected_day = days[0] if days else None

    # Day window logic
    try:
        window_start = int(request.args.get('window', 0))
    except ValueError:
        window_start = 0
    if selected_day:
        sel_idx = days.index(selected_day)
        if sel_idx < window_start:
            window_start = sel_idx
        elif sel_idx >= window_start + 4:
            window_start = max(0, sel_idx - 3)
    window_start = max(0, min(window_start, max(0, len(days)-4)))
    days_to_show = days[window_start:window_start+4]

    c.execute("""SELECT id, action, time, date, destination, route 
                 FROM stops 
                 WHERE trip_id = ? AND user_id = ? 
                 ORDER BY date, time, id""", 
             (trip_id, session['user_id']))
    stops = c.fetchall()
    stops_for_day = [s for s in stops if s[3] == selected_day] if selected_day else []
    # Fetch route steps for each stop
    stops_with_steps = []
    for s in stops_for_day:
        c.execute("SELECT step_text FROM route_steps WHERE stop_id = ? ORDER BY step_order", (s[0],))
        steps = [row[0] for row in c.fetchall()]
        stops_with_steps.append({
            "id": s[0],
            "time": s[2],
            "destination": s[4],
            "action": s[1],
            "route": s[5],
            "route_steps": steps
        })
    conn.close()
    return render_template(
        "itinerary.html",
        trip={"id": trip[0], "destination": trip[1],
              "arrival_date": trip[2], "departure_date": trip[3]},
        days=days,
        days_to_show=days_to_show,
        window_start=window_start,
        selected_day=selected_day,
        stops=stops_with_steps
    )


def get_valid_days_for_trip(trip_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT arrival_date, departure_date FROM trips WHERE id = ? AND user_id = ?", (trip_id, session['user_id']))
    trip = c.fetchone()
    conn.close()
    if not trip:
        return []
    arrival = datetime.strptime(trip[0], "%Y-%m-%d")
    departure = datetime.strptime(trip[1], "%Y-%m-%d")
    num_days = (departure - arrival).days + 1
    return [(arrival + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(num_days)]


@app.route("/trip/<int:trip_id>/add_stop", methods=["POST"])
@login_required
def add_stop_ajax(trip_id):
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        abort(403)
    data = request.get_json()
    action = data.get("action")
    time = data.get("time")
    destination = data.get("destination")
    route = data.get("route")
    selected_day = data.get("date")
    route_steps = data.get("route_steps", [])  # Get route steps array

    # Validate all fields including selected_day
    if not all([action, time, destination, route, selected_day]):
        return jsonify({"error": "All fields including date are required."}), 400

    # Validate selected_day is within trip's valid days
    valid_days = get_valid_days_for_trip(trip_id)
    if selected_day not in valid_days:
        return jsonify({"error": "Invalid date for this trip."}), 400

    conn = get_db_connection()
    c = conn.cursor()
    try:
        # Verify trip belongs to user
        c.execute("SELECT id FROM trips WHERE id = ? AND user_id = ?", (trip_id, session['user_id']))
        if not c.fetchone():
            return jsonify({"error": "Trip not found"}), 404

        # Insert main stop record
        c.execute("INSERT INTO stops (trip_id, user_id, action, time, date, destination, route) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (trip_id, session['user_id'], escape(action), escape(time), selected_day, escape(destination), escape(route)))
        stop_id = c.lastrowid

        # Insert route steps
        for idx, step in enumerate(route_steps):
            c.execute("INSERT INTO route_steps (stop_id, step_order, step_text) VALUES (?, ?, ?)",
                    (stop_id, idx, escape(step)))

        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
    return jsonify({"success": True})


@app.route("/edit_stop/<int:stop_id>", methods=["POST"])
@login_required
def edit_stop(stop_id):
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        abort(403)
    data = request.get_json()
    action = data.get("action")
    time = data.get("time")
    destination = data.get("destination")
    route = data.get("route")
    route_steps = data.get("route_steps", [])  # Get array of route steps

    if not all([action, time, destination, route]):
        return jsonify({"error": "All fields are required."}), 400

    conn = get_db_connection()
    c = conn.cursor()
    try:
        # Verify stop belongs to user
        c.execute("SELECT id FROM stops WHERE id = ? AND user_id = ?", (stop_id, session['user_id']))
        if not c.fetchone():
            return jsonify({"error": "Stop not found"}), 404

        # First delete all existing route steps for this stop
        c.execute("DELETE FROM route_steps WHERE stop_id = ?", (stop_id,))

        # Update the main stop record
        c.execute("UPDATE stops SET action=?, time=?, destination=?, route=? WHERE id=?",
                (escape(action), escape(time), escape(destination), escape(route), stop_id))

        # Insert new route steps
        for idx, step in enumerate(route_steps):
            c.execute("INSERT INTO route_steps (stop_id, step_order, step_text) VALUES (?, ?, ?)",
                    (stop_id, idx, escape(step)))

        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
    return jsonify({"success": True})


@app.route("/delete_stop/<int:stop_id>", methods=["POST"])
@login_required
def delete_stop(stop_id):
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        abort(403)
    conn = get_db_connection()
    c = conn.cursor()
    try:
        # Verify stop belongs to user
        c.execute("SELECT id FROM stops WHERE id = ? AND user_id = ?", (stop_id, session['user_id']))
        if not c.fetchone():
            return jsonify({"error": "Stop not found"}), 404

        # First delete the route steps (foreign key with ON DELETE CASCADE should handle this)
        c.execute("DELETE FROM route_steps WHERE stop_id = ?", (stop_id,))
        # Then delete the stop
        c.execute("DELETE FROM stops WHERE id = ?", (stop_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
    return jsonify({"success": True})


@app.route("/new", methods=["GET", "POST"])
@login_required
def new_trip():
    current_date = datetime.now().strftime("%Y-%m-%d")
    if request.method == "POST":
        destination = request.form.get("destination")
        arrival = request.form.get("arrival")
        departure = request.form.get("departure")
        if destination and arrival and departure:
            arrival_date = datetime.strptime(arrival, "%Y-%m-%d").date()
            departure_date = datetime.strptime(departure, "%Y-%m-%d").date()
            if departure_date < arrival_date:
                return render_template("itinerary.html", new_trip=True, error="Departure date cannot be before arrival date.", current_date=current_date, trip={"id": None})
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("INSERT INTO trips (user_id, destination, arrival_date, departure_date) VALUES (?, ?, ?, ?)",
                      (session['user_id'], destination, arrival, departure))
            trip_id = c.lastrowid
            conn.commit()
            conn.close()
            return redirect(url_for("itinerary", trip_id=trip_id))
        return render_template("itinerary.html", new_trip=True, error="All fields are required.", current_date=current_date, trip={"id": None})
    return render_template("itinerary.html", new_trip=True, current_date=current_date, trip={"id": None})


@app.route("/edit_trip/<int:trip_id>", methods=["POST"])
@login_required
def edit_trip(trip_id):
    data = request.get_json()
    destination = data.get("destination")
    arrival = data.get("arrival")
    departure = data.get("departure")
    if not (destination and arrival and departure):
        return jsonify({"error": "Missing fields"}), 400
    arrival_date = datetime.strptime(arrival, "%Y-%m-%d").date()
    departure_date = datetime.strptime(departure, "%Y-%m-%d").date()
    if departure_date < arrival_date:
        return jsonify({"error": "Departure date must be the same day or after arrival date."}), 400
    conn = get_db_connection()
    c = conn.cursor()
    # Verify trip belongs to user
    c.execute("SELECT id FROM trips WHERE id = ? AND user_id = ?", (trip_id, session['user_id']))
    if not c.fetchone():
        return jsonify({"error": "Trip not found"}), 404
    c.execute("UPDATE trips SET destination=?, arrival_date=?, departure_date=? WHERE id=?",
              (destination, arrival, departure, trip_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/trip/<int:trip_id>/stops")
@login_required
def trip_stops(trip_id):
    # Only allow AJAX/JS requests
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        abort(403)
    conn = get_db_connection()
    c = conn.cursor()
    # Verify trip belongs to user
    c.execute("SELECT id FROM trips WHERE id = ? AND user_id = ?", (trip_id, session['user_id']))
    if not c.fetchone():
        return jsonify({"error": "Trip not found"}), 404
    c.execute("""SELECT id, action, time, date, destination, route 
                 FROM stops 
                 WHERE trip_id = ? AND user_id = ? 
                 ORDER BY date, time, id""", 
             (trip_id, session['user_id']))
    stops = c.fetchall()
    stops_json = [
        {
            "id": s[0],
            "action": s[1],
            "time": s[2],
            "date": s[3],
            "destination": s[4],
            "route": s[5]
        } for s in stops
    ]
    conn.close()
    return jsonify(stops_json)


if __name__ == "__main__":
    app.run(debug=True)
