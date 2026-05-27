import os
from flask import Flask, url_for
from config import Config
from database.db import init_pool
from routes.auth import auth_bp
from routes.main import main_bp
from routes.admin import admin_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    try:
        init_pool()
        print("Database connection pool initialized.")
    except Exception as e:
        print(f"Warning: Could not connect to database: {e}")
        print("Make sure MySQL is running and the database is created.")

    @app.context_processor
    def override_url_for():
        return dict(url_for=dated_url_for)

    def dated_url_for(endpoint, **values):
        if endpoint == 'static':
            filename = values.get('filename', None)
            if filename:
                file_path = os.path.join(app.static_folder, filename)
                if os.path.exists(file_path):
                    values['v'] = int(os.stat(file_path).st_mtime)
        return url_for(endpoint, **values)

    @app.after_request
    def add_header(response):
        # Disable browser caching for static files and assets permanently
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "-1"
        
        # Hardened Web Security Headers (Hack-Proofing)
        response.headers["X-Frame-Options"] = "DENY"  # 100% Blocks Clickjacking attacks
        response.headers["X-Content-Type-Options"] = "nosniff"  # Blocks MIME-Sniffing script execution
        response.headers["X-XSS-Protection"] = "1; mode=block"  # Enables browser-level XSS filters
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"  # Stops leaking data in referrer fields
        # Content Security Policy (CSP) - Blocks remote script injections and whitelists fonts/styles
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self';"
        return response

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
