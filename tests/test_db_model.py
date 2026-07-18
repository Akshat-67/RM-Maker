# tests/test_db_model.py
import pytest
import time
from models.case import Case, db
from flask import Flask

@pytest.fixture
def app():
    app = Flask("test_app")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app

def test_case_model(app):
    with app.app_context():
        case = Case(
            id="test_case_1",
            doc_type="RM",
            property_type="Plot",
            data='{"key": "value"}',
            last_updated=time.time()
        )
        db.session.add(case)
        db.session.commit()
        
        fetched = db.session.get(Case, "test_case_1")
        assert fetched is not None
        assert fetched.doc_type == "RM"
        assert fetched.data == '{"key": "value"}'
