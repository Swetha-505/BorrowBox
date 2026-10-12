"""End-to-end smoke test for BorrowBox's core user and borrowing flows.

Run from the backend directory after installing requirements:
    python smoke_test.py
This uses a temporary SQLite database and does not modify borrowbox.db.
"""
from datetime import date, timedelta
import os
import tempfile

fd, database_path = tempfile.mkstemp(prefix="borrowbox-smoke-", suffix=".db")
os.close(fd)
os.environ["DATABASE_URL"] = f"sqlite:///{database_path.replace(os.sep, '/')}"
os.environ["SECRET_KEY"] = "smoke-test-only-secret-do-not-use-in-production"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    client = TestClient(app)
    try:
        expect(client.get("/api/health").status_code == 200, "health endpoint failed")
        seeded_notes = client.get("/api/items", params={"search": "notes"})
        expect(seeded_notes.status_code == 200 and any("notes" in i["title"].lower() for i in seeded_notes.json()),
               "fresh database should include searchable demo items")

        lender_response = client.post("/api/auth/register", json={
            "name": "Smoke Lender", "email": "smoke-lender@example.test", "password": "demo-pass-123"
        })
        borrower_response = client.post("/api/auth/register", json={
            "name": "Smoke Borrower", "email": "smoke-borrower@example.test", "password": "demo-pass-456"
        })
        expect(lender_response.status_code == 201, f"lender registration failed: {lender_response.text}")
        expect(borrower_response.status_code == 201, f"borrower registration failed: {borrower_response.text}")
        lender, borrower = lender_response.json(), borrower_response.json()
        lender_headers = {"Authorization": f"Bearer {lender['access_token']}"}
        borrower_headers = {"Authorization": f"Bearer {borrower['access_token']}"}

        item_response = client.post("/api/items", headers=lender_headers, json={
            "title": "Smoke Test Calculator", "description": "Scientific calculator",
            "category": "Electronics", "condition": "Good", "location": "Campus"
        })
        expect(item_response.status_code == 201, f"item creation failed: {item_response.text}")
        item = item_response.json()
        expect(item["available_from"] and item["available_until"], "item availability window was not saved")
        out_of_window = client.post("/api/borrowings", headers=borrower_headers, json={
            "item_id": item["id"], "start_date": str(date.today() + timedelta(days=366)),
            "due_date": str(date.today() + timedelta(days=367)), "message": "Outside lender window"
        })
        expect(out_of_window.status_code == 409, "backend must reject dates outside the lender's availability window")

        paused = client.patch("/api/auth/availability", headers=lender_headers,
                              json={"availability_status": "not_lending"})
        expect(paused.status_code == 200, "availability pause failed")
        dates = {"item_id": item["id"], "start_date": str(date.today() + timedelta(days=1)),
                 "due_date": str(date.today() + timedelta(days=2)), "message": "Smoke test request"}
        blocked = client.post("/api/borrowings", headers=borrower_headers, json=dates)
        expect(blocked.status_code == 409, "paused lender should reject new requests")
        resumed = client.patch("/api/auth/availability", headers=lender_headers,
                               json={"availability_status": "available"})
        expect(resumed.status_code == 200, "availability resume failed")

        request = client.post("/api/borrowings", headers=borrower_headers, json=dates)
        expect(request.status_code == 201, f"borrowing request failed: {request.text}")
        borrowing_id = request.json()["id"]
        for action, headers in (("approve", lender_headers), ("pickup", borrower_headers)):
            response = client.patch(f"/api/borrowings/{borrowing_id}/{action}", headers=headers)
            expect(response.status_code == 200, f"{action} failed: {response.text}")

        report = client.post(f"/api/borrowings/{borrowing_id}/condition-reports", headers=borrower_headers,
                             json={"report_type": "pickup", "notes": "Good condition at pickup"})
        expect(report.status_code == 201, f"condition report failed: {report.text}")
        reminders = client.get("/api/reminders", headers=borrower_headers)
        expect(reminders.status_code == 200 and any(r["borrowing_id"] == borrowing_id for r in reminders.json()),
               "borrower due-date reminder was not returned")

        returned = client.patch(f"/api/borrowings/{borrowing_id}/return", headers=borrower_headers)
        expect(returned.status_code == 200, f"return action failed: {returned.text}")
        lender_reminders = client.get("/api/reminders", headers=lender_headers)
        expect(lender_reminders.status_code == 200 and any(r["type"] == "confirm_return" for r in lender_reminders.json()),
               "lender return-confirmation reminder was not returned")
        completed = client.patch(f"/api/borrowings/{borrowing_id}/confirm-return", headers=lender_headers)
        expect(completed.status_code == 200 and completed.json()["status"] == "completed",
               f"return confirmation failed: {completed.text}")
        history = client.get("/api/borrowings/mine", headers=borrower_headers)
        expect(history.status_code == 200 and any(b["id"] == borrowing_id and b["status"] == "completed" for b in history.json()),
               "completed transaction missing from history")
        reports = client.get(f"/api/borrowings/{borrowing_id}/condition-reports", headers=lender_headers)
        expect(reports.status_code == 200 and len(reports.json()) == 1, "condition history could not be retrieved")
        print("PASS: authentication, lending availability, item listing, request, approval, pickup, condition report, due reminder, return, lender reminder, confirmation, and transaction history")
    finally:
        client.close()
        try:
            os.remove(database_path)
        except OSError:
            pass


if __name__ == "__main__":
    main()
