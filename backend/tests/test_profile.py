"""Tests for profile endpoints: get, update, import-resume."""


def test_get_empty_profile(client, auth_headers):
    resp = client.get("/api/profile", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["personal"]["name"] == ""


def test_update_profile(client, auth_headers):
    profile = {
        "personal": {"name": "Test User", "email": "test@test.com", "phone": "555-1234",
                      "location": "Boston, MA", "linkedin": "testuser", "github": "testuser"},
        "education": [{"institution": "MIT", "degree": "BS CS", "start_date": "Sep 2020",
                        "end_date": "May 2024", "is_current": False, "location": "Cambridge, MA"}],
        "experience": [{"role": "SWE Intern", "company": "Google", "location": "MTV",
                         "start_date": "Jun 2023", "end_date": "", "is_current": True,
                         "description": "Built ML pipeline for recommendations"}],
        "projects": [{"name": "ChatBot", "tech_stack": ["Python", "FastAPI"],
                       "url": "github.com/test", "description": "An AI chatbot"}],
        "skills_categories": [{"category": "Languages", "items": ["Python", "JS"]}],
        "leadership": [{"description": "Led a team of 10 engineers"}],
        "preferences": {"target_roles": ["ML Engineer"], "industries": ["Tech"]},
    }
    resp = client.put("/api/profile", json=profile, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["personal"]["name"] == "Test User"
    assert len(data["experience"]) == 1
    assert data["experience"][0]["is_current"] == True


def test_profile_persists(client, auth_headers):
    client.put("/api/profile", json={
        "personal": {"name": "Persisted User"},
    }, headers=auth_headers)

    resp = client.get("/api/profile", headers=auth_headers)
    assert resp.json()["personal"]["name"] == "Persisted User"


def test_profile_isolation(client, auth_headers, second_user_headers):
    """One user's profile shouldn't be visible to another."""
    client.put("/api/profile", json={"personal": {"name": "User A"}}, headers=auth_headers)
    client.put("/api/profile", json={"personal": {"name": "User B"}}, headers=second_user_headers)

    resp_a = client.get("/api/profile", headers=auth_headers)
    resp_b = client.get("/api/profile", headers=second_user_headers)
    assert resp_a.json()["personal"]["name"] == "User A"
    assert resp_b.json()["personal"]["name"] == "User B"


def test_profile_unauthenticated(client):
    resp = client.get("/api/profile")
    assert resp.status_code == 401
