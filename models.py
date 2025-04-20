from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import UniqueConstraint
from werkzeug.security import check_password_hash
from database import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Distributor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    email = db.Column(db.String(128))
    whatsapp = db.Column(db.String(20))
    area = db.Column(db.String(128))
    
    targets = db.relationship('Target', backref='distributor', lazy=True, cascade="all, delete-orphan")
    actuals = db.relationship('Actual', backref='distributor', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Distributor {self.name}>"

class Target(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributor.id'), nullable=False)
    period_type = db.Column(db.String(20), nullable=False)  # 'Weekly', 'Monthly', 'Quarterly', 'Yearly'
    period_identifier = db.Column(db.String(20), nullable=False)  # 'Wk 16-2025', 'Apr-2025', 'Q2-2025', '2025'
    target_value = db.Column(db.Float, nullable=False)
    week_start_date = db.Column(db.String(10))  # Store as 'YYYY-MM-DD' for weekly targets
    week_end_date = db.Column(db.String(10))  # Store as 'YYYY-MM-DD' for weekly targets
    
    __table_args__ = (
        UniqueConstraint('distributor_id', 'period_type', 'period_identifier', name='uix_target_distributor_period'),
    )
    
    def __repr__(self):
        return f"<Target {self.distributor.name} - {self.period_type} {self.period_identifier}>"

class Actual(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributor.id'), nullable=False)
    week_start_date = db.Column(db.String(10), nullable=False)  # Store as 'YYYY-MM-DD'
    week_end_date = db.Column(db.String(10), nullable=False)  # Store as 'YYYY-MM-DD'
    actual_sales = db.Column(db.Float, nullable=False)
    month = db.Column(db.String(10), nullable=False)  # Auto-calculated: e.g., "Apr-2025"
    quarter = db.Column(db.String(10), nullable=False)  # Auto-calculated: e.g., "Q2-2025"
    year = db.Column(db.String(4), nullable=False)  # Auto-calculated: e.g., "2025"
    
    __table_args__ = (
        UniqueConstraint('distributor_id', 'week_start_date', 'week_end_date', name='uix_actual_distributor_week'),
    )
    
    def __repr__(self):
        return f"<Actual {self.distributor.name} - Week of {self.week_start_date}>"
