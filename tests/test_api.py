"""
Test suite for Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    activities.clear()
    activities.update({
        "Soccer Team": {
            "description": "Join the school soccer team and compete in inter-school matches",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 6:00 PM",
            "max_participants": 25,
            "participants": ["alex@mergington.edu", "sarah@mergington.edu"]
        },
        "Basketball Club": {
            "description": "Practice basketball skills and participate in tournaments",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu", "emily@mergington.edu"]
        },
        "Art Workshop": {
            "description": "Explore various art techniques including painting and drawing",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["lily@mergington.edu", "noah@mergington.edu"]
        }
    })


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_all_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Soccer Team" in data
        assert "Basketball Club" in data
        assert "Art Workshop" in data

    def test_activities_have_correct_structure(self, client):
        """Test that activities have the correct data structure"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_student(self, client):
        """Test signing up a new student for an activity"""
        response = client.post(
            "/activities/Soccer Team/signup?email=new.student@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "new.student@mergington.edu" in data["message"]

    def test_signup_adds_student_to_participants(self, client):
        """Test that signup actually adds the student to the participants list"""
        email = "test@mergington.edu"
        client.post(f"/activities/Soccer Team/signup?email={email}")
        
        response = client.get("/activities")
        data = response.json()
        assert email in data["Soccer Team"]["participants"]

    def test_signup_duplicate_student(self, client):
        """Test that signing up the same student twice returns an error"""
        email = "alex@mergington.edu"  # Already in Soccer Team
        response = client.post(f"/activities/Soccer Team/signup?email={email}")
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity(self, client):
        """Test signing up for a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_special_characters_in_activity_name(self, client):
        """Test signing up for an activity with special characters in the name"""
        # Add an activity with special characters
        activities["Arts & Crafts"] = {
            "description": "Creative arts",
            "schedule": "Fridays",
            "max_participants": 10,
            "participants": []
        }
        
        response = client.post(
            "/activities/Arts & Crafts/signup?email=student@mergington.edu"
        )
        assert response.status_code == 200


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant(self, client):
        """Test unregistering an existing participant"""
        email = "alex@mergington.edu"  # Already in Soccer Team
        response = client.delete(f"/activities/Soccer Team/unregister?email={email}")
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert email in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        email = "alex@mergington.edu"
        client.delete(f"/activities/Soccer Team/unregister?email={email}")
        
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Soccer Team"]["participants"]

    def test_unregister_non_participant(self, client):
        """Test unregistering a student who is not in the activity"""
        response = client.delete(
            "/activities/Soccer Team/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_nonexistent_activity(self, client):
        """Test unregistering from a non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]


class TestIntegrationScenarios:
    """Integration tests for common user workflows"""

    def test_signup_and_unregister_workflow(self, client):
        """Test the complete flow of signing up and then unregistering"""
        email = "workflow@mergington.edu"
        activity = "Basketball Club"
        
        # Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify signup
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email in data[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify unregister
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email not in data[activity]["participants"]

    def test_multiple_students_signup(self, client):
        """Test multiple students signing up for the same activity"""
        activity = "Art Workshop"
        students = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        for email in students:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all students are registered
        activities_response = client.get("/activities")
        data = activities_response.json()
        for email in students:
            assert email in data[activity]["participants"]

    def test_student_cannot_signup_after_unregister_then_signup_again(self, client):
        """Test that a student can re-signup after unregistering"""
        email = "resignup@mergington.edu"
        activity = "Soccer Team"
        
        # First signup
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Unregister
        client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Re-signup should succeed
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify student is in the list
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email in data[activity]["participants"]
