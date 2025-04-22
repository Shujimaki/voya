from flask import Flask, render_template, request, redirect, url_for, jsonify, abort, session, g
from datetime import datetime, timedelta
from functools import wraps
import re
import bcrypt
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_session import Session
from itsdangerous import URLSafeTimedSerializer
from email_validator import validate_email, EmailNotValidError
from dotenv import load_dotenv
import logging
import os
import json

from models import db, User, Trip, Stop, RouteStep

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())  # Fallback for local dev

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

logger.debug(f"Mail username configured: {app.config['MAIL_USERNAME']}")
if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
    logger.error("Email credentials not found in environment variables!")

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)

# Database configuration
DB_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:password@localhost/voya')
if DB_URL.startswith('postgres://'):
    DB_URL = DB_URL.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)
migrate = Migrate(app, db)

# Session configuration
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SESSION_SQLALCHEMY'] = db
Session(app)

# Create tables if they don't exist
with app.app_context():
    db.create_all()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
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
    if request.endpoint in ['login', 'register', 'dashboard']:
        g.response_headers = {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    if request.endpoint in ['login', 'register'] and 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    # Only apply rate limiting to form submissions
    if request.method == 'POST' and request.endpoint in ['login', 'register']:
        ip = request.remote_addr
        current_time = datetime.now()
        
        # Different rate limits for different actions
        time_window = 10  # minutes
        max_attempts = 10  # attempts
        
        # Clean up old attempts older than 1 hour to prevent DB bloat
        LoginAttempt.query.filter(
            LoginAttempt.timestamp < current_time - timedelta(hours=1)
        ).delete()
        db.session.commit()
        
        # Check attempts within time window
        attempts = LoginAttempt.query.filter_by(ip=ip).filter(
            LoginAttempt.timestamp > current_time - timedelta(minutes=time_window)
        ).all()
        
        if len(attempts) >= max_attempts:
            abort(429, description="Too many attempts. Please try again after a few minutes.")
        
        new_attempt = LoginAttempt(ip=ip, timestamp=current_time)
        db.session.add(new_attempt)
        db.session.commit()

# command to clean up expired records
@app.cli.command("cleanup-database")
def cleanup_database():
    """Clean up expired verification tokens and old login attempts."""
    current_time = datetime.now()
    
    # Delete old login attempts
    old_attempts = LoginAttempt.query.filter(
        LoginAttempt.timestamp < current_time - timedelta(hours=24)
    ).delete()
    
    # Delete unverified users with expired tokens
    expired_users = User.query.filter(
        User.email_verified == False,
        User.token_expiry < current_time
    ).delete()
    
    db.session.commit()
    print(f"Cleaned up {old_attempts} old login attempts and {expired_users} expired user records.")


# Define LoginAttempt model for rate limiting
class LoginAttempt(db.Model):
    __tablename__ = 'login_attempts'
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(45), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

@app.context_processor
def inject_user():
    return {'username': session.get('username', None)}

@app.context_processor
def inject_current_year():
    return {'now': datetime.now().strftime}

@app.after_request
def after_request(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    if hasattr(g, 'response_headers'):
        for key, value in g.response_headers.items():
            response.headers[key] = value
    if request.endpoint in ['logout']:
        response.headers['Clear-Site-Data'] = '"cache", "cookies", "storage"'
    return response

def is_valid_password(password):
    if len(password) < 8 or not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password):
        return False
    return True

def send_verification_email(email):
    try:
        token = serializer.dumps(email, salt='email-verification')
        verification_link = url_for('verify_email', token=token, _external=True)
        msg = Message('Verify your email address', recipients=[email])
        msg.body = f'''Please verify your email address by clicking the following link:
{verification_link}

This link will expire in 24 hours.
'''
        mail.send(msg)
        logger.debug(f"Verification email sent to {email}")
        return token
    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")
        raise

def is_valid_email(email):
    try:
        validation = validate_email(email, check_deliverability=True)
        return True, validation.normalized
    except EmailNotValidError as e:
        return False, str(e)

@app.route('/verify-email/<token>')
def verify_email(token):
    try:
        email = serializer.loads(token, salt='email-verification', max_age=86400)
        user = User.query.filter_by(email=email, verification_token=token).first()
        if not user:
            logger.error("Invalid or expired token")
            return render_template('email_verification_error.html')
        user.email_verified = True
        db.session.commit()
        return redirect(url_for('register', token=token))
    except Exception as e:
        logger.error(f"Email verification failed: {str(e)}")
        return render_template('email_verification_error.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    redirect_response = authenticated_user_redirect()
    if redirect_response:
        return redirect_response
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password = request.form.get('password')
        if not identifier or not password:
            return render_template('login.html', error='All fields are required')
        user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()
        if not user:
            return render_template('login.html', error='Invalid username or password')
        if not user.email_verified:
            return render_template('login.html', error='Please verify your email address first')
        try:
            if bcrypt.checkpw(password.encode('utf-8'), user.password):
                session.clear()
                session['user_id'] = user.id
                session['username'] = user.username
                session.permanent = True
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error='Invalid username or password')
        except ValueError as e:
            logger.error(f"Password check failed: {str(e)}")
            return render_template('login.html', error='Invalid password format')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    redirect_response = authenticated_user_redirect()
    if redirect_response:
        return redirect_response
        
    if request.method == 'POST':
        if 'verify_email' in request.form:
            email = request.form.get('email')
            logger.debug(f"Processing email verification for: {email}")
            is_valid, normalized_email = is_valid_email(email)
            if not is_valid:
                logger.debug(f"Invalid email: {normalized_email}")
                return render_template('register.html', error=normalized_email)
                
            # Check for existing users with this email
            existing_user = User.query.filter_by(email=normalized_email).first()
            
            # If user exists but isn't verified, and token is expired, delete it
            if existing_user and not existing_user.email_verified:
                if not existing_user.token_expiry or existing_user.token_expiry < datetime.now():
                    db.session.delete(existing_user)
                    db.session.commit()
                    existing_user = None
                    
            # If we still have an existing user, handle appropriately
            if existing_user:
                if existing_user.email_verified:
                    return render_template('register.html', error='Email already registered')
                else:
                    # Re-send verification for existing unverified user
                    try:
                        token = send_verification_email(normalized_email)
                        existing_user.verification_token = token
                        existing_user.token_expiry = datetime.now() + timedelta(days=1)
                        db.session.commit()
                        return render_template('verify_email_sent.html', email=normalized_email)
                    except Exception as e:
                        logger.error(f"Error in email verification: {str(e)}")
                        return render_template('register.html', error='Failed to send verification email')
            
            # Create a temporary user record with just email and token
            try:
                token = send_verification_email(normalized_email)
                expiry = datetime.now() + timedelta(days=1)
                temp_user = User(
                    email=normalized_email, 
                    verification_token=token, 
                    token_expiry=expiry,
                    username=None,  # Will be set during final registration
                    password=None   # Will be set during final registration
                )
                db.session.add(temp_user)
                db.session.commit()
                return render_template('verify_email_sent.html', email=normalized_email)
            except Exception as e:
                logger.error(f"Error in email verification: {str(e)}")
                db.session.rollback()
                return render_template('register.html', error='Failed to send verification email')
        else:
            # Handle final registration step
            username = request.form.get('username')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            token = request.form.get('token')
            
            if not token:
                return render_template('register.html', error='Missing verification token')
                
            # Find the user with this token
            user = User.query.filter_by(verification_token=token).first()
            if not user:
                return render_template('register.html', error='Invalid or expired verification token')
                
            # Token expired
            if user.token_expiry and user.token_expiry < datetime.now():
                db.session.delete(user)
                db.session.commit()
                return render_template('register.html', error='Verification token has expired. Please register again.')
                
            if not username or not password or not confirm_password:
                return render_template('register.html', token=token, error='All fields are required')
                
            if password != confirm_password:
                return render_template('register.html', token=token, error='Passwords do not match')
                
            if not is_valid_password(password):
                return render_template('register.html', token=token,
                                      error='Password must be at least 8 characters long and contain uppercase and lowercase letters')
                                      
            if User.query.filter_by(username=username).first():
                return render_template('register.html', token=token, error='Username already exists')
                
            try:
                hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                
                # Complete the user record
                user.username = username
                user.password = hashed
                user.email_verified = True
                user.verification_token = None
                user.token_expiry = None
                db.session.commit()
                
                logger.debug(f"Registration completed for user: {username}")
                
                session.clear()
                session['user_id'] = user.id
                session['username'] = username
                session.permanent = True
                return redirect(url_for('dashboard'))
            except Exception as e:
                logger.error(f"Error in registration completion: {str(e)}")
                db.session.rollback()
                return render_template('register.html', token=token, error='Registration failed')
    
    token = request.args.get('token')
    return render_template('register.html', token=token)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/")
@login_required
def dashboard():
    trips = Trip.query.filter_by(user_id=session['user_id']).all()
    formatted_trips = [[trip.id, trip.user_id, trip.destination, trip.arrival_date, trip.departure_date] for trip in trips]
    return render_template("dashboard.html",
                           username=session['username'],
                           trips=formatted_trips,
                           trips_json=json.dumps(formatted_trips),
                           trip_count=len(trips))

@app.route("/add", methods=["POST"])
@login_required
def add_trip():
    destination = request.form.get("destination")
    arrival = request.form.get("arrival")
    departure = request.form.get("departure")
    if destination and arrival and departure:
        new_trip = Trip(destination=destination,
                        arrival_date=arrival,
                        departure_date=departure,
                        user_id=session['user_id'])
        db.session.add(new_trip)
        db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/delete/<int:trip_id>")
@login_required
def delete_trip(trip_id):
    try:
        trip = Trip.query.filter_by(id=trip_id, user_id=session['user_id']).first()
        if not trip:
            return "Trip not found", 404
        db.session.delete(trip)
        db.session.commit()
        return redirect(url_for('dashboard'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting trip: {str(e)}")
        return "Error deleting trip", 500

@app.route("/trip/<int:trip_id>", methods=["GET", "POST"])
@login_required
def itinerary(trip_id):
    trip = Trip.query.filter_by(id=trip_id, user_id=session['user_id']).first()
    if not trip:
        return "Trip not found", 404
    arrival = datetime.strptime(trip.arrival_date, "%Y-%m-%d")
    departure = datetime.strptime(trip.departure_date, "%Y-%m-%d")
    num_days = (departure - arrival).days + 1
    days = [(arrival + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(num_days)]
    selected_day = request.args.get('day')
    if selected_day not in days:
        selected_day = days[0] if days else None
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
    stops_query = Stop.query.filter_by(trip_id=trip_id, user_id=session['user_id'])
    if selected_day:
        stops_query = stops_query.filter_by(date=selected_day)
    stops_query = stops_query.order_by(Stop.date, Stop.time, Stop.id)
    stops_with_steps = []
    for stop in stops_query.all():
        stops_with_steps.append({
            "id": stop.id,
            "time": stop.time,
            "destination": stop.destination,
            "action": stop.action,
            "route": stop.route,
            "route_steps": [step.step_text for step in sorted(stop.route_steps, key=lambda x: x.step_order)]
        })
    return render_template(
        "itinerary.html",
        trip=trip,
        days=days,
        days_to_show=days_to_show,
        window_start=window_start,
        selected_day=selected_day,
        stops=stops_with_steps
    )

def get_valid_days_for_trip(trip_id):
    trip = Trip.query.filter_by(id=trip_id, user_id=session['user_id']).first()
    if not trip:
        return []
    arrival = datetime.strptime(trip.arrival_date, "%Y-%m-%d")
    departure = datetime.strptime(trip.departure_date, "%Y-%m-%d")
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
    route_steps = data.get("route_steps", [])
    if not all([action, time, destination, route, selected_day]):
        return jsonify({"error": "All fields including date are required."}), 400
    valid_days = get_valid_days_for_trip(trip_id)
    if selected_day not in valid_days:
        return jsonify({"error": "Invalid date for this trip."}), 400
    trip = Trip.query.filter_by(id=trip_id, user_id=session['user_id']).first()
    if not trip:
        return jsonify({"error": "Trip not found"}), 404
    try:
        new_stop = Stop(
            trip_id=trip_id,
            user_id=session['user_id'],
            action=action,
            time=time,
            date=selected_day,
            destination=destination,
            route=route
        )
        db.session.add(new_stop)
        db.session.flush()
        for idx, step in enumerate(route_steps):
            new_step = RouteStep(
                stop_id=new_stop.id,
                step_order=idx,
                step_text=step
            )
            db.session.add(new_step)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

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
    route_steps = data.get("route_steps", [])
    if not all([action, time, destination, route]):
        return jsonify({"error": "All fields are required."}), 400
    stop = Stop.query.filter_by(id=stop_id, user_id=session['user_id']).first()
    if not stop:
        return jsonify({"error": "Stop not found"}), 404
    try:
        RouteStep.query.filter_by(stop_id=stop_id).delete()
        stop.action = action
        stop.time = time
        stop.destination = destination
        stop.route = route
        for idx, step in enumerate(route_steps):
            new_step = RouteStep(
                stop_id=stop_id,
                step_order=idx,
                step_text=step
            )
            db.session.add(new_step)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/delete_stop/<int:stop_id>", methods=["POST"])
@login_required
def delete_stop(stop_id):
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        abort(403)
    stop = Stop.query.filter_by(id=stop_id, user_id=session['user_id']).first()
    if not stop:
        return jsonify({"error": "Stop not found"}), 404
    try:
        db.session.delete(stop)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

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
            new_trip = Trip(
                user_id=session['user_id'],
                destination=destination,
                arrival_date=arrival,
                departure_date=departure
            )
            db.session.add(new_trip)
            db.session.commit()
            return redirect(url_for("itinerary", trip_id=new_trip.id))
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
    trip = Trip.query.filter_by(id=trip_id, user_id=session['user_id']).first()
    if not trip:
        return jsonify({"error": "Trip not found"}), 404
    try:
        trip.destination = destination
        trip.arrival_date = arrival
        trip.departure_date = departure
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/trip/<int:trip_id>/stops")
@login_required
def trip_stops(trip_id):
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        abort(403)
    trip = Trip.query.filter_by(id=trip_id, user_id=session['user_id']).first()
    if not trip:
        return jsonify({"error": "Trip not found"}), 404
    stops = Stop.query.filter_by(trip_id=trip_id, user_id=session['user_id']) \
                     .order_by(Stop.date, Stop.time, Stop.id) \
                     .all()
    stops_json = [
        {
            "id": stop.id,
            "action": stop.action,
            "time": stop.time,
            "date": stop.date,
            "destination": stop.destination,
            "route": stop.route
        } for stop in stops
    ]
    return jsonify(stops_json)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route('/ping')
def ping():
    return 'OK', 200

if __name__ == "__main__":
    app.run()