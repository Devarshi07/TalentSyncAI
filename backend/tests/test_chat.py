"""Tests for chat and thread endpoints."""


def test_chat_creates_thread(client, auth_headers):
    """Sending a message without thread_id should auto-create a thread."""
    resp = client.post("/api/chat", json={"message": "Hello!"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "thread_id" in data
    assert data["thread_id"] is not None
    assert data["intent"] == "general"  # no Gemini in tests, falls back to general


def test_chat_continues_thread(client, auth_headers):
    """Sending messages with the same thread_id should append."""
    r1 = client.post("/api/chat", json={"message": "First"}, headers=auth_headers)
    tid = r1.json()["thread_id"]

    r2 = client.post("/api/chat", json={"message": "Second", "thread_id": tid}, headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["thread_id"] == tid

    # Check thread has 4 messages (2 user + 2 assistant)
    thread = client.get(f"/api/threads/{tid}", headers=auth_headers)
    assert len(thread.json()["messages"]) == 4


def test_list_threads(client, auth_headers):
    client.post("/api/chat", json={"message": "Chat 1"}, headers=auth_headers)
    client.post("/api/chat", json={"message": "Chat 2"}, headers=auth_headers)

    resp = client.get("/api/threads", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["threads"]) == 2
    assert "storage_used" in data
    assert "storage_limit" in data


def test_delete_thread(client, auth_headers):
    r1 = client.post("/api/chat", json={"message": "To delete"}, headers=auth_headers)
    tid = r1.json()["thread_id"]

    resp = client.delete(f"/api/threads/{tid}", headers=auth_headers)
    assert resp.status_code == 200

    # Thread should be gone
    resp2 = client.get(f"/api/threads/{tid}", headers=auth_headers)
    assert resp2.status_code == 404


def test_rename_thread(client, auth_headers):
    r1 = client.post("/api/chat", json={"message": "Original title"}, headers=auth_headers)
    tid = r1.json()["thread_id"]

    resp = client.patch(f"/api/threads/{tid}", json={"title": "New Title"}, headers=auth_headers)
    assert resp.status_code == 200

    thread = client.get(f"/api/threads/{tid}", headers=auth_headers)
    assert thread.json()["thread"]["title"] == "New Title"


def test_thread_isolation(client, auth_headers, second_user_headers):
    """User A shouldn't see User B's threads."""
    r1 = client.post("/api/chat", json={"message": "A's chat"}, headers=auth_headers)
    tid_a = r1.json()["thread_id"]

    client.post("/api/chat", json={"message": "B's chat"}, headers=second_user_headers)

    # User B shouldn't access User A's thread
    resp = client.get(f"/api/threads/{tid_a}", headers=second_user_headers)
    assert resp.status_code == 404

    # Each user sees only their own
    a_threads = client.get("/api/threads", headers=auth_headers).json()["threads"]
    b_threads = client.get("/api/threads", headers=second_user_headers).json()["threads"]
    assert len(a_threads) == 1
    assert len(b_threads) == 1


def test_chat_unauthenticated(client):
    resp = client.post("/api/chat", json={"message": "Hello"})
    assert resp.status_code == 401
