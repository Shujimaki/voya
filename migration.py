# migration.py - Run this once to migrate your data
import sqlite3
import os
from flask import Flask
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create a minimal Flask app for migration purposes
app = Flask(__name__)

# Get database URLs
DB_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:password@localhost/voya')
# Convert postgres:// to postgresql:// for Heroku if needed
if DB_URL.startswith('postgres://'):
    DB_URL = DB_URL.replace('postgres://', 'postgresql://', 1)

# SQLite database path
SQLITE_DB = 'voya.db'

def migrate_data():
    print("Starting migration from SQLite to PostgreSQL...")
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row  # This lets us access columns by name
    sqlite_cursor = sqlite_conn.cursor()
    
    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(DB_URL)
    pg_cursor = pg_conn.cursor()
    
    try:
        # 1. Migrate users
        print("Migrating users...")
        sqlite_cursor.execute("SELECT * FROM users")
        users = sqlite_cursor.fetchall()
        
        for user in users:
            # Convert the SQLite row to a dictionary for easier access
            user_dict = dict(user)
            
            # Insert into PostgreSQL
            pg_cursor.execute(
                """
                INSERT INTO users 
                (id, username, email, password, email_verified, verification_token, token_expiry)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (
                    user_dict['id'], 
                    user_dict['username'], 
                    user_dict['email'],
                    user_dict['password'],  # This is already a bcrypt hash
                    bool(user_dict['email_verified']),
                    user_dict['verification_token'],
                    user_dict['token_expiry']
                )
            )
        
        # 2. Migrate trips
        print("Migrating trips...")
        sqlite_cursor.execute("SELECT * FROM trips")
        trips = sqlite_cursor.fetchall()
        
        for trip in trips:
            trip_dict = dict(trip)
            
            pg_cursor.execute(
                """
                INSERT INTO trips
                (id, user_id, destination, arrival_date, departure_date)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (
                    trip_dict['id'],
                    trip_dict['user_id'],
                    trip_dict['destination'],
                    trip_dict['arrival_date'],
                    trip_dict['departure_date']
                )
            )
        
        # 3. Migrate stops
        print("Migrating stops...")
        sqlite_cursor.execute("SELECT * FROM stops")
        stops = sqlite_cursor.fetchall()
        
        for stop in stops:
            stop_dict = dict(stop)
            
            pg_cursor.execute(
                """
                INSERT INTO stops
                (id, trip_id, user_id, action, time, date, destination, route)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (
                    stop_dict['id'],
                    stop_dict['trip_id'],
                    stop_dict['user_id'],
                    stop_dict['action'],
                    stop_dict['time'],
                    stop_dict['date'],
                    stop_dict['destination'],
                    stop_dict['route']
                )
            )
        
        # 4. Migrate route steps
        print("Migrating route steps...")
        sqlite_cursor.execute("SELECT * FROM route_steps")
        steps = sqlite_cursor.fetchall()
        
        for step in steps:
            step_dict = dict(step)
            
            pg_cursor.execute(
                """
                INSERT INTO route_steps
                (id, stop_id, step_order, step_text)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (
                    step_dict['id'],
                    step_dict['stop_id'],
                    step_dict['step_order'],
                    step_dict['step_text']
                )
            )
        
        # 5. Update sequences
        print("Updating sequences...")
        tables = ['users', 'trips', 'stops', 'route_steps']
        for table in tables:
            pg_cursor.execute(f"SELECT setval('{table}_id_seq', (SELECT MAX(id) FROM {table}), true)")
        
        # Commit changes
        pg_conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        pg_conn.rollback()
        print(f"Error during migration: {e}")
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate_data()