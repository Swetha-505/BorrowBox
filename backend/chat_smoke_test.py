"""Isolated API smoke test for private BorrowBox chat and notifications.
Run: python chat_smoke_test.py
Uses a temporary SQLite database and leaves the normal borrowbox.db untouched.
"""
import os, tempfile, time
from pathlib import Path

_tmp = tempfile.NamedTemporaryFile(prefix="borrowbox_chat_", suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = "sqlite:///" + _tmp.name.replace("\\", "/")

from fastapi.testclient import TestClient
from app.main import app


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    client = TestClient(app)
    suffix = str(time.time_ns())
    def register(name):
        response = client.post("/api/auth/register", json={"name": name, "email": f"{name.lower().replace(' ', '.')}.{suffix}@example.test", "password": "BorrowBoxTest123!"})
        check(response.status_code == 201, f"register failed: {response.text}")
        return response.json()["access_token"]
    lender = register("Test Lender")
    borrower = register("Test Borrower")
    outsider = register("Test Outsider")
    h_lender = {"Authorization": f"Bearer {lender}"}
    h_borrower = {"Authorization": f"Bearer {borrower}"}
    h_outsider = {"Authorization": f"Bearer {outsider}"}
    item = client.post("/api/items", headers=h_lender, json={"title": "Chat Test Item", "description": "Test", "category": "Books", "condition": "Good", "location": "Campus", "available_from": "2026-10-12", "available_until": "2027-10-12"})
    check(item.status_code == 201, f"item create failed: {item.text}")
    request = client.post("/api/borrowings", headers=h_borrower, json={"item_id": item.json()["id"], "start_date": "2026-10-14", "due_date": "2026-10-16", "message": "Pickup coordination"})
    check(request.status_code == 201, f"request create failed: {request.text}")
    borrowing_id = request.json()["id"]
    sent = client.post(f"/api/borrowings/{borrowing_id}/messages", headers=h_borrower, json={"body": "Can we meet at 2 PM for pickup?"})
    check(sent.status_code == 201, f"message send failed: {sent.text}")
    messages = client.get(f"/api/borrowings/{borrowing_id}/messages", headers=h_lender)
    check(messages.status_code == 200 and len(messages.json()) == 1, "message history failed")
    conversations = client.get("/api/messages/conversations", headers=h_lender)
    check(conversations.status_code == 200 and conversations.json()[0]["borrowing_id"] == borrowing_id, "conversation list failed")
    notifications = client.get("/api/notifications", headers=h_lender)
    check(notifications.status_code == 200 and len(notifications.json()) >= 2, "notification creation failed")
    denied = client.get(f"/api/borrowings/{borrowing_id}/messages", headers=h_outsider)
    check(denied.status_code == 403, "non-participant was allowed to read private messages")
    print("PASS: private transaction chat, message history, conversation preview, notifications, and participant authorization")


if __name__ == "__main__":
    try:
        main()
    finally:
        try: os.unlink(_tmp.name)
        except OSError: pass
