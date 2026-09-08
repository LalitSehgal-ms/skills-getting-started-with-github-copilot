from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def restore_activity_state():
    original_state = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_state)


@pytest.fixture
def client():
    return TestClient(app)


def test_root_redirects_to_static_index(client):
    expected_location = "/static/index.html"

    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data(client):
    expected_activity = activities["Chess Club"]

    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()["Chess Club"] == expected_activity


def test_signup_adds_student_to_activity(client):
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"

    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_student(client):
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    assert response.status_code == 400
    assert response.json() == {"detail": "Student is already signed up for this activity"}


def test_signup_rejects_unknown_activity(client):
    activity_name = "Unknown Club"
    email = "new.student@mergington.edu"

    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_remove_student_from_activity(client):
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_remove_rejects_unknown_activity(client):
    activity_name = "Unknown Club"
    email = "student@mergington.edu"

    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_remove_rejects_non_participant(client):
    activity_name = "Chess Club"
    email = "not-signed-up@mergington.edu"

    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}