# /backend/app/__init__.py

import os # <-- 1. Importuj 'os'
from dotenv import load_dotenv # <-- 2. Importuj 'load_dotenv'
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail

# --- 3. Wczytaj zmienne z pliku .env ---
# Zrób to na samej górze, zanim cokolwiek zostanie skonfigurowane
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
# ---

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
mail = Mail()

def create_app():
    app = Flask(__name__)

    # --- 4. Zastąp twarde kody zmiennymi środowiskowymi ---
    
    # Konfiguracja ogólna
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db" # (To może zostać, nie jest sekretem)

    # Konfiguracja Maila
    app.config['MAIL_SERVER'] = os.environ.get("MAIL_SERVER")
    app.config['MAIL_PORT'] = int(os.environ.get("MAIL_PORT", 587))
    app.config['MAIL_USE_TLS'] = os.environ.get("MAIL_USE_TLS", 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
    app.config['MAIL_DEFAULT_SENDER'] = ('System Zamówień', os.environ.get("MAIL_USERNAME"))
    
    # Konfiguracja VAPID
    app.config['VAPID_PUBLIC_KEY'] = os.environ.get("VAPID_PUBLIC_KEY")
    app.config['VAPID_PRIVATE_KEY'] = os.environ.get("VAPID_PRIVATE_KEY")
    app.config['VAPID_CLAIMS'] = {
        'sub': os.environ.get("VAPID_MAILTO")
    }
    # --- KONIEC ZMIAN ---

    # Inicjalizacja rozszerzeń
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
    
    # Włączenie CORS (bez zmian)
    CORS(app, resources={r"/api/*": {"origins": [
        "http://localhost:5174", 
        "http://localhost:5173"
    ]}})

    # Rejestracja modeli i blueprintów
    with app.app_context():
        from . import models
        from . import routes 
        app.register_blueprint(routes.api_bp)

    return app