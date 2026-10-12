"""Smoke tests for borrower request cancellation and lender listing cancellation."""
from datetime import date, timedelta
import os, tempfile
fd, path = tempfile.mkstemp(prefix='borrowbox-cancel-', suffix='.db'); os.close(fd)
os.environ['DATABASE_URL'] = f"sqlite:///{path.replace(os.sep, '/')}"
os.environ['SECRET_KEY'] = 'cancellation-test-only-secret'
from fastapi.testclient import TestClient
from app.main import app

def check(ok, message):
    if not ok: raise AssertionError(message)

with TestClient(app) as c:
    lender = c.post('/api/auth/register', json={'name':'Cancel Lender','email':'cancel-lender@example.test','password':'password123'}).json()
    borrower = c.post('/api/auth/register', json={'name':'Cancel Borrower','email':'cancel-borrower@example.test','password':'password123'}).json()
    lh = {'Authorization':f"Bearer {lender['access_token']}"}; bh = {'Authorization':f"Bearer {borrower['access_token']}"}
    item = c.post('/api/items', headers=lh, json={'title':'Cancel Test Item','description':'Test','category':'Books','condition':'Good','location':'Campus'}).json()
    payload = {'item_id':item['id'],'start_date':str(date.today()+timedelta(days=1)),'due_date':str(date.today()+timedelta(days=2)),'message':'Please lend this'}
    request = c.post('/api/borrowings', headers=bh, json=payload)
    check(request.status_code == 201, f"request creation failed: {request.text}")
    cancelled_request = c.patch(f"/api/borrowings/{request.json()['id']}/cancel", headers=bh)
    check(cancelled_request.status_code == 200 and cancelled_request.json()['status'] == 'cancelled', 'borrower could not cancel their own request')
    check(any(n['title'] == 'Request cancelled' for n in c.get('/api/notifications', headers=lh).json()), 'lender was not notified of borrower cancellation')
    # Create a second pending request, then withdraw the listing as its owner.
    request2 = c.post('/api/borrowings', headers=bh, json=payload)
    check(request2.status_code == 201, f"second request creation failed: {request2.text}")
    withdrawn = c.delete(f"/api/items/{item['id']}", headers=lh)
    check(withdrawn.status_code == 200 and withdrawn.json()['cancelled_requests'] == 1, f"listing cancellation failed: {withdrawn.text}")
    check(c.get(f"/api/borrowings/{request2.json()['id']}", headers=bh).json()['status'] == 'cancelled', 'pending request was not cancelled with listing')
    check(any(n['title'] == 'Listing withdrawn' for n in c.get('/api/notifications', headers=bh).json()), 'borrower was not notified that listing was withdrawn')
    check(c.get('/api/items', params={'search':'Cancel Test Item'}).json() == [], 'cancelled listing still appears in public browse')
    print('PASS: borrower request cancellation, lender notification, listing cancellation, pending request cancellation, borrower notification, and public listing removal')
try: os.remove(path)
except OSError: pass
