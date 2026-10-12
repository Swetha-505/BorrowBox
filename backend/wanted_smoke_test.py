"""Smoke tests for wanted-board offers/chat and physical item availability."""
from datetime import date, timedelta
import os, tempfile
fd, dbfile = tempfile.mkstemp(prefix='borrowbox-wanted-', suffix='.db'); os.close(fd)
os.environ['DATABASE_URL'] = f"sqlite:///{dbfile}"
os.environ['SECRET_KEY'] = 'test-only-secret'
from fastapi.testclient import TestClient
from app.main import app

def ok(condition, message):
    if not condition: raise AssertionError(message)

with TestClient(app) as c:
    a = c.post('/api/auth/register', json={'name':'Requester Test','email':'requester@example.test','password':'requester-pass-123'}); ok(a.status_code==201,a.text)
    b = c.post('/api/auth/register', json={'name':'Lender Test','email':'lender@example.test','password':'lender-pass-123'}); ok(b.status_code==201,b.text)
    ah={'Authorization':f"Bearer {a.json()['access_token']}"}; bh={'Authorization':f"Bearer {b.json()['access_token']}"}
    today=date.today(); w=c.post('/api/wanted-requests',headers=ah,json={'title':'Tripod','description':'Need a camera tripod','category':'Electronics','needed_from':str(today+timedelta(days=1)),'needed_until':str(today+timedelta(days=3)),'location':'Campus'}); ok(w.status_code==201,w.text); wid=w.json()['id']
    listed=c.get('/api/wanted-requests'); ok(listed.status_code==200 and len(listed.json())==1,'wanted request should appear publicly')
    own=c.post(f'/api/wanted-requests/{wid}/interests',headers=ah,json={'message':'self'}); ok(own.status_code==400,'requester must not respond to own request')
    interest=c.post(f'/api/wanted-requests/{wid}/interests',headers=bh,json={'message':'I can lend a tripod'}); ok(interest.status_code==201,interest.text); iid=interest.json()['id']
    responses=c.get(f'/api/wanted-requests/{wid}/interests',headers=ah); ok(responses.status_code==200 and len(responses.json())==1,'requester should see lender offer')
    chat=c.get(f'/api/wanted-interests/{iid}/messages',headers=ah); ok(chat.status_code==200 and chat.json()[0]['body']=='I can lend a tripod','wanted chat should include first message')
    sent=c.post(f'/api/wanted-interests/{iid}/messages',headers=ah,json={'body':'Great, let us coordinate'}); ok(sent.status_code==201,sent.text)
    # Borrowing lifecycle: item becomes unavailable after pickup and remains so until return confirmation.
    item=c.post('/api/items',headers=bh,json={'title':'Borrow Test Camera','description':'Camera','category':'Electronics','condition':'Good','location':'Campus','available_from':str(today),'available_until':str(today+timedelta(days=60))}); ok(item.status_code==201,item.text); itemid=item.json()['id']
    req=c.post('/api/borrowings',headers=ah,json={'item_id':itemid,'start_date':str(today+timedelta(days=1)),'due_date':str(today+timedelta(days=5)),'message':'Need camera'}); ok(req.status_code==201,req.text); bid=req.json()['id']
    ok(c.patch(f'/api/borrowings/{bid}/approve',headers=bh).status_code==200,'approval should work')
    ok(c.patch(f'/api/borrowings/{bid}/pickup',headers=ah).status_code==200,'pickup should work')
    items=c.get('/api/items',params={'search':'Borrow Test Camera'}).json(); ok(items and items[0]['availability_status']=='borrowed','item should show as borrowed/unavailable after pickup')
    blocked=c.post('/api/borrowings',headers=ah,json={'item_id':itemid,'start_date':str(today+timedelta(days=10)),'due_date':str(today+timedelta(days=12))}); ok(blocked.status_code==409,'item should reject requests while physically out')
    print('PASS: wanted requests, lender offers, private wanted chat, and item unavailable after pickup')
os.remove(dbfile)
