from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Create the SQLAlchemy object
db = SQLAlchemy()

# Define models as classes
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.LargeBinary)  # Store binary password hash
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(128))
    token_expiry = db.Column(db.DateTime)
    
    # Relationship with other tables
    trips = db.relationship('Trip', backref='user', lazy=True, cascade='all, delete-orphan')
    stops = db.relationship('Stop', backref='user', lazy=True, cascade='all, delete-orphan')

class Trip(db.Model):
    __tablename__ = 'trips'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    destination = db.Column(db.String(120), nullable=False)
    arrival_date = db.Column(db.String(10), nullable=False)
    departure_date = db.Column(db.String(10), nullable=False)
    
    # Relationship with stops
    stops = db.relationship('Stop', backref='trip', lazy=True, cascade='all, delete-orphan')

class Stop(db.Model):
    __tablename__ = 'stops'
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(120), nullable=False)
    time = db.Column(db.String(10), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    destination = db.Column(db.String(120), nullable=False)
    route = db.Column(db.Text, nullable=False)

    # Relationship with route steps
    route_steps = db.relationship('RouteStep', backref='stop', lazy=True, cascade='all, delete-orphan')

class RouteStep(db.Model):
    __tablename__ = 'route_steps'
    id = db.Column(db.Integer, primary_key=True)
    stop_id = db.Column(db.Integer, db.ForeignKey('stops.id'), nullable=False)
    step_order = db.Column(db.Integer, nullable=False)
    step_text = db.Column(db.Text, nullable=False)