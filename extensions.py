"""Ekstensi Flask yang dibuat sekali lalu dipasang ke app di app.py (init_app)."""
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
