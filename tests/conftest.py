import pytest
from fastapi.testclient import TestClient

from diabetes.service.app import app


@pytest.fixture(scope='session')
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def good_row():
    return {
        "gender": "Female",
        "age": 44,
        "hypertension": 0,
        "heart_disease": 0,
        "smoking_history": "never",
        "bmi": 19.31,
        "HbA1c_level": 6.5,
        "blood_glucose_level": 200
    }

@pytest.fixture()
def bad_row():
    return {
        "HbA1c_level": 6.5
    }