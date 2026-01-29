import pytest


class TestRoot:
    """Tests for the root endpoint"""
    
    def test_root_redirect(self, client):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the get activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that get_activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Check that all expected activities are present
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert "Basketball Team" in data
        assert "Tennis Club" in data
        assert "Drama Club" in data
        assert "Digital Art" in data
        assert "Debate Team" in data
        assert "Science Club" in data
    
    def test_activity_has_required_fields(self, client, reset_activities):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity in data.items():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity
            assert isinstance(activity["participants"], list)
    
    def test_participants_list_contains_initial_members(self, client, reset_activities):
        """Test that participants list contains expected members"""
        response = client.get("/activities")
        data = response.json()
        
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]
        assert "emma@mergington.edu" in data["Programming Class"]["participants"]


class TestSignupForActivity:
    """Tests for the signup endpoint"""
    
    def test_signup_new_student(self, client, reset_activities):
        """Test that a new student can sign up for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up newstudent@mergington.edu for Chess Club" in data["message"]
        
        # Verify student was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_already_registered_student(self, client, reset_activities):
        """Test that a student already signed up gets an error"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test that signing up for non-existent activity returns 404"""
        response = client.post(
            "/activities/NonExistent%20Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_multiple_activities(self, client, reset_activities):
        """Test that a student can sign up for multiple activities"""
        student = "multi@mergington.edu"
        
        response1 = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": student}
        )
        assert response1.status_code == 200
        
        response2 = client.post(
            "/activities/Programming%20Class/signup",
            params={"email": student}
        )
        assert response2.status_code == 200
        
        # Verify student is in both
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert student in activities_data["Chess Club"]["participants"]
        assert student in activities_data["Programming Class"]["participants"]


class TestUnregisterFromActivity:
    """Tests for the unregister endpoint"""
    
    def test_unregister_existing_participant(self, client, reset_activities):
        """Test that an existing participant can be unregistered"""
        response = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered michael@mergington.edu from Chess Club" in data["message"]
        
        # Verify student was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]
    
    def test_unregister_not_registered_student(self, client, reset_activities):
        """Test that unregistering a non-participant returns error"""
        response = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "notstudent@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]
    
    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test that unregistering from non-existent activity returns 404"""
        response = client.post(
            "/activities/NonExistent%20Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_then_unregister(self, client, reset_activities):
        """Test complete flow of signing up and then unregistering"""
        student = "signup_then_unregister@mergington.edu"
        activity = "Basketball%20Team"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": student}
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert student in activities_data["Basketball Team"]["participants"]
        
        # Unregister
        unregister_response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": student}
        )
        assert unregister_response.status_code == 200
        
        # Verify unregister
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert student not in activities_data["Basketball Team"]["participants"]


class TestActivityParticipantLimits:
    """Tests for activity participant limits"""
    
    def test_activity_respects_max_participants(self, client, reset_activities):
        """Test that activities have max_participants set correctly"""
        response = client.get("/activities")
        data = response.json()
        
        # Check specific activities
        assert data["Chess Club"]["max_participants"] == 12
        assert data["Tennis Club"]["max_participants"] == 10
        assert data["Gym Class"]["max_participants"] == 30
    
    def test_participant_count_matches_list(self, client, reset_activities):
        """Test that participant count matches the participants list length"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity in data.items():
            expected_count = len(activity["participants"])
            max_participants = activity["max_participants"]
            assert expected_count <= max_participants, \
                f"{activity_name} has {expected_count} participants but max is {max_participants}"
