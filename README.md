# BorrowBox — Full-Stack Resource Sharing Platform

BorrowBox is a full-stack community marketplace where one account can both lend items and borrow items from other people. It tracks listing availability, borrowing requests, pickup and return actions, transaction history, private transaction-linked chat, in-app notifications, return reminders, and a Wanted Board for requests that are not yet listed.

## Technology stack

- **Frontend:** React 18, Vite, React Router, JavaScript/JSX, CSS, Lucide icons
- **Backend:** Python, FastAPI, Uvicorn, Pydantic
- **Database:** SQLite + SQLAlchemy ORM (no separate database server required)
- **Authentication:** JWT bearer tokens and Argon2 password hashing

## Features

### Account and availability
- Dedicated `/login` and `/register` pages with form validation and password confirmation.
- Secure password hashing and JWT-protected actions.
- A user can lend and borrow from the same account.
- Dashboard availability selector: **Available to lend** or **Not lending right now**.
- When a user pauses lending, new borrowing requests for that user's items are rejected by the backend and the listing shows the lender's unavailable status.

### Items
- Create, browse, search, category-filter, edit, and cancel/deactivate item listings from the item card or My listings dashboard. Cancelling a listing automatically cancels its pending requests and notifies affected borrowers; listings with approved or active transactions cannot be cancelled until those transactions are resolved.
- Item title, description, category, condition, photo URL, and pickup location.
- Each listing has an owner-defined **Available from** and **Available until** date window. Date pickers enforce the window in the UI, and the API independently rejects requests outside it.
- A fresh database automatically receives six sample listings so Browse Items is not empty; sample records are stored in SQLite and can be searched like normal listings.
- Item cards and details show availability status: available, reserved today, unavailable/borrowed, lender unavailable, or inactive. Once pickup is confirmed, the item remains unavailable until the lender confirms the return; the backend also rejects new requests while the item is physically out.
- Date validation and server-side overlap checks when requesting and approving items.


### Wanted Board and direct offers
- Use **Wanted board** in the main navigation when the required item is missing from Browse.
- Signed-in borrowers can publish a wanted post with category, details, required dates, and pickup area.
- Other signed-in members can offer to lend the item with a message. The requester can open **View responses** and privately chat with each interested lender.
- Wanted conversations are stored in SQLite, permission-checked so only the requester and responding lender can read or send messages, and refreshed automatically while open.
- Wanted posts and offers create in-app notifications. A lender cannot respond to their own wanted post or respond while their account is paused from lending.

### Borrowing workflow
- Send requests for a selected start and return date.
- Lenders can approve or reject pending requests.
- Borrowers can cancel their own pending or approved requests from My borrowings; the lender is notified. Borrowers cannot cancel a request after pickup or once the return process has begun. They can confirm pickup and mark an item returned.
- Lenders confirm return receipt before the transaction is completed.
- Pickup and return condition reports support notes and an optional photo URL.

### Private lender–borrower communication
- Every borrowing request has a private conversation shared only by the lender and borrower for that transaction.
- Chat is available from the borrowing row and the Messages dashboard tab, including while a request is pending so users can coordinate.
- Messages are stored in SQLite with sender and timestamp, persist after logout/restart, and are marked read when the other participant opens the conversation.
- The chat refreshes automatically every 3 seconds while open. The dashboard refreshes conversation previews, unread counts, and notifications every 5 seconds while open.
- Messages are blocked for rejected/cancelled requests. The API checks that the caller is a transaction participant on every read/write.

### In-app notifications
- Notifications are stored in the database for new borrowing requests, new messages, approval/rejection/cancellation, pickup, return, and return confirmation.
- Users can view unread activity, mark a notification read, or mark all notifications read.
- Notifications are in-app only; email/SMS/push delivery is not configured.

### Dashboard, history, and reminders
- Dashboard cards for listings, requests sent, requests received, and completed transactions.
- Separate views for My borrowings, Requests to me, My listings, and **Transaction history**.
- Transaction history includes role, status, requested dates, creation date, and condition-report access.
- In-app return reminders appear for active borrowings due within three days, overdue items, and returns awaiting lender confirmation. Reminders are calculated from database records when the dashboard loads or refreshes; they are not email/SMS/push notifications.

## Requirements

- Python 3.10+
- Node.js 18+
- Internet access is not required by the application at runtime, apart from loading optional remote item photos and installing dependencies the first time.

## Run on Windows

### 1. Start the backend

Open a terminal in the `BorrowBox` folder:

```bat
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

For PowerShell, use `Copy-Item .env.example .env` instead of `copy`.

The backend starts at `http://127.0.0.1:8000`. API documentation is available at `http://127.0.0.1:8000/docs`.

### 2. Start the frontend

Open a **second terminal** in the `BorrowBox` folder:

```bat
cd frontend
npm install
copy .env.example .env
npm run dev
```

Open the Vite URL shown in the terminal, usually `http://localhost:5173`.

## First end-to-end demo

On a brand-new empty database, BorrowBox seeds a demo shelf (including **Class Notes Bundle**) so search results are visible immediately. Demo lender login: `demo@borrowbox.local` / `BorrowBox123!`. For a realistic two-person transaction, register a second account as the borrower.

1. Open `/register` and create the **lender** account (or sign in with the demo lender).
2. Open the dashboard and leave the profile set to **Available to lend**.
3. Choose **List an item** and publish a calculator or book.
4. Open an incognito/private browser window and create a second **borrower** account.
5. Browse items, open the listing, select a start and return date, and submit a request.
6. Sign back in as the lender and approve the request in **Requests to me**.
7. Sign in as the borrower and choose **Confirm pickup**.
8. The borrower can see the due date and in-app return reminder when the item is due within three days. The borrower marks it returned; the lender confirms receipt.
9. Open **Transaction history** to review the status and dates. Use **Reports** or **Condition** to record and view condition details.

## API overview

- `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- `PATCH /api/auth/availability` — update the signed-in user's lending status
- `GET /api/wanted-requests`, `POST /api/wanted-requests` — browse and publish wanted posts
- `POST /api/wanted-requests/{id}/interests`, `GET /api/wanted-requests/{id}/interests`, `GET /api/wanted-requests/{id}/my-interest` — offer to lend and review responses
- `GET/POST /api/wanted-interests/{id}/messages` — private wanted-request chat
- `GET /api/items`, `GET /api/items/mine`, `GET /api/items/{item_id}` (item responses include `available_from` and `available_until`)
- `POST /api/items`, `PATCH /api/items/{item_id}`, `DELETE /api/items/{item_id}` — cancel own listing; pending requests are cancelled with notifications
- `POST /api/borrowings`, `GET /api/borrowings/mine`, `GET /api/borrowings/received`
- `PATCH /api/borrowings/{id}/approve`, `/reject`, `/cancel`, `/pickup`, `/return`, `/confirm-return` — borrower cancellation is allowed only while pending or approved
- `GET /api/reminders` — current user's upcoming/overdue/confirmation reminders
- `GET /api/messages/conversations` — conversation list, latest message, participant, and unread count
- `GET /api/borrowings/{id}/messages`, `POST /api/borrowings/{id}/messages` — read/send transaction messages
- `GET /api/notifications`, `GET /api/notifications/unread-count` — notifications and unread totals
- `PATCH /api/notifications/{id}/read`, `PATCH /api/notifications/read-all` — mark notifications read
- `POST /api/borrowings/{id}/condition-reports`, `GET /api/borrowings/{id}/condition-reports`
- `GET /api/health`

All protected routes use a bearer token. The backend checks permissions; hiding a frontend button is not relied upon for security.

## Database

SQLite is configured by default as `sqlite:///./borrowbox.db` and is created automatically when the backend starts. Tables are created through SQLAlchemy. A small startup migration adds the profile availability column to an earlier SQLite database if needed. Delete the local database file only if you intentionally want to reset demo data.

## Configuration and deployment notes

- `backend/.env.example` and `frontend/.env.example` show local configuration.
- Change the development JWT secret before any deployment and use HTTPS in production.
- This is a college-project MVP. Before public deployment, add rate limiting, backups, moderation/dispute handling, and production image storage. The item form accepts photo URLs; it does not upload image files to a storage service.
- SQLite is suitable for local demos. Consider PostgreSQL and stronger transaction/locking strategy for concurrent production booking traffic.

## Run the core workflow smoke test

After installing backend requirements, run this from the `backend` folder:

```bat
python smoke_test.py
python chat_smoke_test.py
```

The script uses a temporary SQLite database and checks registration, lending availability pause/resume, listing creation, borrowing approval, pickup, condition reporting, due reminders, return confirmation, and transaction history. It does not overwrite your normal `borrowbox.db`.


### Additional feature test
Run `python wanted_smoke_test.py` from the `backend` folder. It verifies wanted posts, lender offers, private messages, and that a listing becomes unavailable after pickup and rejects another borrowing request until the return process is completed.
