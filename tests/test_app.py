"""
Tests for the Mergington High School Activities API
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

# Create test client
client = TestClient(app)


class TestActivitiesEndpoint:
    """Test the /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that GET /activities returns status 200"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)

    def test_get_activities_contains_expected_activities(self):
        """Test that activities response contains expected activities"""
        response = client.get("/activities")
        data = response.json()
        expected_activities = [
            "Basketball Team",
            "Tennis Club",
            "Drama Club",
            "Art Studio",
            "Debate Team",
            "Science Club",
            "Chess Club",
            "Programming Class",
            "Gym Class"
        ]
        for activity in expected_activities:
            assert activity in data

    def test_activity_structure(self):
        """Test that each activity has the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)


class TestSignupEndpoint:
    """Test the /activities/{activity_name}/signup endpoint"""

    def test_signup_for_existing_activity(self):
        """Test signing up for an existing activity"""
        response = client.post(
            "/activities/Basketball Team/signup?email=student@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "student@mergington.edu" in data["message"]

    def test_signup_for_nonexistent_activity(self):
        """Test signing up for a non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_duplicate_signup_returns_400(self):
        """Test signing up twice for same activity returns 400"""
        email = "duplicate@mergington.edu"
        
        # First signup
        response1 = client.post(
            f"/activities/Basketball Team/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Attempt duplicate signup
        response2 = client.post(
            f"/activities/Basketball Team/signup?email={email}"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_adds_participant_to_list(self):
        """Test that signup actually adds the participant to the activity"""
        email = "newstudent@mergington.edu"
        
        # Get activities before signup
        response_before = client.get("/activities")
        participants_before = response_before.json()["Tennis Club"]["participants"].copy()
        
        # Signup
        client.post(f"/activities/Tennis Club/signup?email={email}")
        
        # Get activities after signup
        response_after = client.get("/activities")
        participants_after = response_after.json()["Tennis Club"]["participants"]
        
        assert email in participants_after
        assert len(participants_after) == len(participants_before) + 1


class TestUnregisterEndpoint:
    """Test the /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant(self):
        """Test unregistering a student from an activity"""
        # First, sign up a student
        email = "unregister_test@mergington.edu"
        client.post(f"/activities/Art Studio/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/Art Studio/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_unregister_from_nonexistent_activity(self):
        """Test unregistering from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404

    def test_unregister_nonexistent_participant(self):
        """Test unregistering a student not in activity returns 400"""
        response = client.delete(
            "/activities/Basketball Team/unregister?email=notexist@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        email = "removal_test@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Science Club/signup?email={email}")
        
        # Verify they're signed up
        response_before = client.get("/activities")
        assert email in response_before.json()["Science Club"]["participants"]
        
        # Unregister
        client.delete(f"/activities/Science Club/unregister?email={email}")
        
        # Verify they're removed
        response_after = client.get("/activities")
        assert email not in response_after.json()["Science Club"]["participants"]


class TestRootEndpoint:
    """Test the root endpoint"""

    def test_root_redirects_to_index(self):
        """Test that / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
