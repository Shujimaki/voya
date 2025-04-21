# Voya

Voya is a web-based travel planning app that helps you create, manage, and organize detailed itineraries. Built by Brian Metrillo, it offers an intuitive interface for planning trips, tracking destinations, and managing stops with routes. Perfect for adventurers and planners alike, Voya simplifies your travel experience.

## Features

- **User Authentication**:
  - Secure registration with email verification (links valid for 24 hours).
  - Login with email or username.
  - Passwords require 8+ characters, including uppercase and lowercase.
  - Anti-spam measures prevent rapid form submissions.
- **Trip Management**:
  - Create trips with destination, arrival, and departure dates.
  - Edit or delete trips.
  - View upcoming trips in a dashboard carousel.
- **Itinerary Planning**:
  - Organize trips by day with a navigable day selector.
  - Add, edit, or delete stops with action, time, destination, and route steps.
  - View detailed stop info, including step-by-step routes.
- **Responsive Design**:
  - Mobile-friendly interface for on-the-go planning.
  - Clean, modern styling across all pages.
- **Additional Pages**:
  - **About**: Learn about Voya and Brian Metrillo, with LinkedIn and GitHub links.
  - **Contact**: Reach out via email (in-app system in development).
  - **Dashboard**: Personalized welcome with trip summaries.
- **Security**:
  - Cache control prevents back/forward caching of sensitive pages.
  - Session and local storage cleared on page load.
  - Email verification for secure registration.

## Installation

### Prerequisites

- Python 3.8+
- Flask
- Database (e.g., SQLite, PostgreSQL)
- Mail server/service (e.g., SMTP, SendGrid)
- Git

### Steps

1. Clone the repo:

   ```bash
   git clone https://github.com/Shujimaki/voya.git
   cd voya
   ```

2. Set up a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install flask flask-sqlalchemy flask-mail gunicorn python-dotenv
   ```

4. Configure environment variables in a `.env` file:

   ```plaintext
   FLASK_APP=app.py
   FLASK_ENV=development
   SECRET_KEY=your-secret-key
   DATABASE_URL=sqlite:///voya.db  # Or PostgreSQL URL
   MAIL_SERVER=smtp.your-mail-server.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your-mail-username
   MAIL_PASSWORD=your-mail-password
   ```

5. Initialize the database:

   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

6. Run the app:

   ```bash
   flask run
   ```

   Access at `http://localhost:5000`.

## Usage

1. **Register**: Go to `/register`, enter your email, and click the verification link to set a username and password.
2. **Log In**: Use email/username and password at `/login`.
3. **Create a Trip**: Visit `/new` to add a destination and dates.
4. **Manage Itineraries**: From the dashboard, add/edit/delete stops for each trip day and view routes.
5. **Explore Pages**:
   - `/about`: Discover Voya and its developer.
   - `/contact`: Send feedback via email.

## Technologies Used

- **Frontend**:
  - HTML5, CSS3
  - JavaScript (for modals, carousel)
  - Jinja2 (Flask templating)
- **Backend**:
  - Flask (Python web framework)
  - Flask-SQLAlchemy (database management, assumed)
  - Flask-Mail (email verification, assumed)
- **Security**:
  - Cloudflare (challenge platform, per templates)
  - Email obfuscation for contact links

## Contributing

Contributions are welcome! To contribute:

1. Fork the repo.
2. Create a branch: `git checkout -b feature/your-feature`.
3. Commit changes: `git commit -m "Add your feature"`.
4. Push: `git push origin feature/your-feature`.
5. Open a pull request with a clear description.

Follow the project's coding style and include tests where possible.

## Contact

Questions, suggestions, or feedback? Reach out:

- **Email**: contactbonvoya@gmail.com
- **LinkedIn**: Brian Metrillo
- **GitHub**: Shujimaki

In-app contact system coming soon.

## License

© 2025 Voya by Brian Metrillo. All rights reserved.
