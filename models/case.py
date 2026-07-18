# models/case.py
from flask_sqlalchemy import SQLAlchemy
import time

db = SQLAlchemy()

class Case(db.Model):
    __tablename__ = 'cases'
    
    id = db.Column(db.String(100), primary_key=True)
    doc_type = db.Column(db.String(10), default="RM")
    bank = db.Column(db.String(100), nullable=True)
    borrower_count = db.Column(db.Integer, default=1)
    loan_count = db.Column(db.Integer, default=1)
    properties_count = db.Column(db.Integer, default=1)
    sellers_count = db.Column(db.Integer, default=1)
    buyers_count = db.Column(db.Integer, default=1)
    chain_scenario = db.Column(db.String(100), nullable=True)
    selected_template = db.Column(db.String(255), nullable=True)
    property_type = db.Column(db.String(50), default="Plot")
    
    verified_fields = db.Column(db.Text, nullable=True)
    processed_files = db.Column(db.Text, nullable=True)
    files = db.Column(db.Text, nullable=True)
    legal_report_files = db.Column(db.Text, nullable=True)
    
    data = db.Column(db.Text, nullable=True)
    last_updated = db.Column(db.Float, default=time.time, onupdate=time.time)
