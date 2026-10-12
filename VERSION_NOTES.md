# BorrowBox v5 — Transaction Chat & Notifications

Built on v4, preserving account login, availability windows, seeded demo items, date-conflict validation, borrowing lifecycle, transaction history, condition reports, and return reminders.

## New in v5
- Private, transaction-linked lender/borrower chat, including during pending requests.
- Persistent messages in SQLite with sender, timestamp, and read state.
- Chat access checks on every request; only the lender and borrower can read/send messages. Rejected/cancelled requests are read-only/closed for messaging.
- Chat automatically refreshes every 3 seconds while open. Dashboard conversation previews refresh every 5 seconds.
- Conversation list with last message, transaction status, other participant, and unread message count.
- Persistent in-app notifications for requests, messages, approvals/rejections/cancellations, pickup, returns, and confirmation.
- Mark one notification or all notifications as read.
- New API endpoints are documented in README and Swagger `/docs`.

## Verification
- Python compilation passed.
- Backend TestClient checks passed for health, account registration, item creation, borrowing request, message creation, message read, conversation preview, notification creation, and rejecting access from a non-participant.
- Frontend build was not run successfully because `npm install` timed out in the build environment. Run `npm install` and `npm run build` locally before presenting/deploying.
- Messaging uses lightweight polling (not a WebSocket server), so it updates automatically while the page is open without requiring an extra service.


## Version 6 — Listing and request cancellation
- Added a cancel-listing (trash) action beside Edit in the dashboard's My listings tab.
- Cancelling a listing hides it from Browse and atomically cancels all pending requests for that item, with an in-app notification to each affected borrower.
- Backend prevents cancelling a listing with approved, active, or return-pending transactions, avoiding disruption to an agreed handover.
- Added confirmation before a borrower cancels their pending/approved request.
- Existing borrower-only request cancellation API now remains discoverable and documented.


## Version 7 — Physical availability and Wanted Board
- Item status becomes **Unavailable · borrowed** immediately after pickup is confirmed and remains unavailable through return-pending until the lender confirms receipt. The backend rejects new borrowing requests while the item is physically out, even if the requested dates would otherwise not overlap.
- Added a Wanted Board for borrowers who cannot find an item in current listings. Posts include category, description, needed dates, and pickup area.
- Lenders can offer to help with a message; requesters can review responses and start private, persistent conversations with interested lenders.
- Wanted conversations are permission-checked and refresh automatically while open. Offers and messages create in-app notifications.
- Added `wanted_smoke_test.py` for the new feature and unavailable-item rules.
- Verification: backend compilation, the existing core `smoke_test.py`, and `wanted_smoke_test.py` passed. JSX syntax parsing passed. A full Vite production build could not be run here because `npm install` timed out; run `npm install` then `npm run build` locally before deployment.
