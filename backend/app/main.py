from datetime import date, datetime, timedelta, timezone

from typing import Optional, List

import os, re



import jwt

from jwt import InvalidTokenError

from argon2 import PasswordHasher

from argon2.exceptions import VerifyMismatchError, VerificationError

from fastapi import FastAPI, Depends, HTTPException, status, Query

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, Field, ConfigDict, field_validator

from pydantic_settings import BaseSettings

from sqlalchemy import (

    create_engine, String, Integer, Boolean, Date, DateTime, ForeignKey,

    Text, select, and_, or_, func

)

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session





class Settings(BaseSettings):

    secret_key: str = "dev-only-change-this-secret-before-deployment"

    database_url: str = "sqlite:///./borrowbox.db"

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    access_token_minutes: int = 720



    class Config:

        env_file = ".env"

        extra = "ignore"





settings = Settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)





class Base(DeclarativeBase):

    pass





class User(Base):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    password_hash: Mapped[str] = mapped_column(String(500), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    availability_status: Mapped[str] = mapped_column(String(30), default="available", nullable=False)

    items: Mapped[List["Item"]] = relationship(back_populates="owner")

    borrowings: Mapped[List["Borrowing"]] = relationship(back_populates="borrower")





class Item(Base):

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(140), nullable=False, index=True)

    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    category: Mapped[str] = mapped_column(String(60), default="Other", nullable=False, index=True)

    condition: Mapped[str] = mapped_column(String(40), default="Good", nullable=False)

    image_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    location: Mapped[str] = mapped_column(String(140), default="Campus", nullable=False)

    available_from: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)

    available_until: Mapped[date] = mapped_column(Date, default=lambda: date.today() + timedelta(days=365), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    owner: Mapped["User"] = relationship(back_populates="items")

    borrowings: Mapped[List["Borrowing"]] = relationship(back_populates="item")





class Borrowing(Base):

    __tablename__ = "borrowings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False, index=True)

    borrower_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)

    due_date: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False, index=True)

    message: Mapped[str] = mapped_column(Text, default="", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    picked_up_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    returned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    item: Mapped["Item"] = relationship(back_populates="borrowings")

    borrower: Mapped["User"] = relationship(back_populates="borrowings")

    reports: Mapped[List["ConditionReport"]] = relationship(back_populates="borrowing", cascade="all, delete-orphan")





class ConditionReport(Base):

    __tablename__ = "condition_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    borrowing_id: Mapped[int] = mapped_column(ForeignKey("borrowings.id"), nullable=False, index=True)

    report_type: Mapped[str] = mapped_column(String(30), nullable=False)

    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    photo_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    borrowing: Mapped["Borrowing"] = relationship(back_populates="reports")





class Message(Base):

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    borrowing_id: Mapped[int] = mapped_column(ForeignKey("borrowings.id", ondelete="CASCADE"), nullable=False, index=True)

    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    body: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    sender: Mapped["User"] = relationship()

    borrowing: Mapped["Borrowing"] = relationship()





class Notification(Base):

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    borrowing_id: Mapped[Optional[int]] = mapped_column(ForeignKey("borrowings.id", ondelete="CASCADE"), nullable=True, index=True)

    kind: Mapped[str] = mapped_column(String(40), default="activity", nullable=False)

    title: Mapped[str] = mapped_column(String(160), nullable=False)

    body: Mapped[str] = mapped_column(String(500), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)





class WantedRequest(Base):
    """A community post describing an item a member wants to borrow."""
    __tablename__ = "wanted_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(140), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    category: Mapped[str] = mapped_column(String(60), default="Other", nullable=False, index=True)
    needed_from: Mapped[date] = mapped_column(Date, nullable=False)
    needed_until: Mapped[date] = mapped_column(Date, nullable=False)
    location: Mapped[str] = mapped_column(String(140), default="Campus", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    requester: Mapped["User"] = relationship()


class WantedInterest(Base):
    __tablename__ = "wanted_interests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    wanted_request_id: Mapped[int] = mapped_column(ForeignKey("wanted_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    lender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    lender: Mapped["User"] = relationship()
    wanted_request: Mapped["WantedRequest"] = relationship()


class WantedMessage(Base):
    __tablename__ = "wanted_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    interest_id: Mapped[int] = mapped_column(ForeignKey("wanted_interests.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    sender: Mapped["User"] = relationship()


Base.metadata.create_all(bind=engine)

# Small forward-compatible migration for databases created by an earlier BorrowBox version.

with engine.begin() as connection:

    user_columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(users)").fetchall()} if settings.database_url.startswith("sqlite") else set()

    if settings.database_url.startswith("sqlite") and "availability_status" not in user_columns:

        connection.exec_driver_sql("ALTER TABLE users ADD COLUMN availability_status VARCHAR(30) NOT NULL DEFAULT 'available'")

    if settings.database_url.startswith("sqlite"):

        item_columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(items)").fetchall()}

        if "available_from" not in item_columns:

            connection.exec_driver_sql("ALTER TABLE items ADD COLUMN available_from DATE")

            connection.exec_driver_sql("UPDATE items SET available_from = date('now') WHERE available_from IS NULL")

        if "available_until" not in item_columns:

            connection.exec_driver_sql("ALTER TABLE items ADD COLUMN available_until DATE")

            connection.exec_driver_sql("UPDATE items SET available_until = date('now', '+365 day') WHERE available_until IS NULL")

ALGORITHM = "HS256"

_password_hasher = PasswordHasher()





def hash_password(password: str) -> str:

    """Hash a password with Argon2id using argon2-cffi defaults."""

    return _password_hasher.hash(password)





def verify_password(password: str, stored: str) -> bool:

    try:

        return _password_hasher.verify(stored, password)

    except (VerifyMismatchError, VerificationError, ValueError, TypeError):

        return False





# Seed a small, clearly documented demo shelf when the database is empty. This fixes

# the confusing first-run experience where Browse showed zero items in a fresh install.

def seed_demo_items():

    db = SessionLocal()

    try:

        email = "demo@borrowbox.local"

        owner = db.scalar(select(User).where(User.email == email))

        if owner is not None and db.scalar(select(Item.id).where(Item.owner_id == owner.id).limit(1)) is not None:

            return

        if owner is None:

            owner = User(name="BorrowBox Demo Lender", email=email,

                         password_hash=hash_password("BorrowBox123!"), availability_status="available")

            db.add(owner)

            db.flush()

        start = date.today()

        end = start + timedelta(days=180)

        demo_items = [

            ("Class Notes Bundle", "Neatly organized handwritten notes for semester revision.", "Books", "Good", "https://images.unsplash.com/photo-1455390582262-044c065d9b84?auto=format&fit=crop&w=900&q=80"),

            ("Scientific Calculator", "Scientific calculator for exams and engineering coursework.", "Electronics", "Like new", "https://images.unsplash.com/photo-1587145820266-a5951ee6f620?auto=format&fit=crop&w=900&q=80"),

            ("Programming Textbook", "A useful programming reference for lab work and practice.", "Books", "Good", "https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&w=900&q=80"),

            ("Laptop Stand", "Foldable stand for a comfortable study setup.", "Electronics", "Like new", "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=80"),

            ("Tool Kit", "Basic screwdriver and home-repair tool kit.", "Tools", "Good", "https://images.unsplash.com/photo-1504148455328-c376907d081c?auto=format&fit=crop&w=900&q=80"),

            ("Badminton Racket", "A racket for casual games and practice.", "Sports", "Good", "https://images.unsplash.com/photo-1626224583764-f87db24ac4ea?auto=format&fit=crop&w=900&q=80"),

        ]

        for title, description, category, condition, image_url in demo_items:

            db.add(Item(owner_id=owner.id, title=title, description=description, category=category,

                        condition=condition, image_url=image_url, location="Campus pickup",

                        available_from=start, available_until=end, is_active=True))

        db.commit()

    finally:

        db.close()





seed_demo_items()



app = FastAPI(

    title="BorrowBox API",

    description="API for item sharing, borrowing lifecycle, private transaction chat, in-app notifications, and condition reports.",

    version="1.1.0",

)

origins = [x.strip() for x in settings.cors_origins.split(",") if x.strip()]

app.add_middleware(

    CORSMiddleware,

    allow_origins=origins,

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)





def get_db():

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()





# ---------- Schemas ----------

class RegisterIn(BaseModel):

    name: str = Field(min_length=2, max_length=100)

    email: str = Field(min_length=5, max_length=255)

    password: str = Field(min_length=8, max_length=128)



    @field_validator("email")

    @classmethod

    def validate_email(cls, value: str) -> str:

        value = value.strip().lower()

        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):

            raise ValueError("Enter a valid email address")

        return value





class LoginIn(BaseModel):

    email: str = Field(min_length=5, max_length=255)

    password: str = Field(min_length=1, max_length=128)



    @field_validator("email")

    @classmethod

    def validate_email(cls, value: str) -> str:

        value = value.strip().lower()

        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):

            raise ValueError("Enter a valid email address")

        return value





class UserOut(BaseModel):

    id: int

    name: str

    email: str

    created_at: datetime

    availability_status: str = "available"

    model_config = ConfigDict(from_attributes=True)





class AvailabilityIn(BaseModel):

    availability_status: str = Field(pattern="^(available|not_lending)$")





class TokenOut(BaseModel):

    access_token: str

    token_type: str = "bearer"

    user: UserOut





class ItemIn(BaseModel):

    title: str = Field(min_length=2, max_length=140)

    description: str = Field(default="", max_length=3000)

    category: str = Field(default="Other", max_length=60)

    condition: str = Field(default="Good", max_length=40)

    image_url: Optional[str] = Field(default=None, max_length=1000)

    location: str = Field(default="Campus", max_length=140)

    available_from: date = Field(default_factory=date.today)

    available_until: date = Field(default_factory=lambda: date.today() + timedelta(days=365))



    @field_validator("available_until")

    @classmethod

    def validate_availability_end(cls, value: date, info):

        start = info.data.get("available_from")

        if start and value <= start:

            raise ValueError("Availability end date must be after the start date")

        return value





class ItemOut(BaseModel):

    id: int

    owner_id: int

    owner_name: str

    title: str

    description: str

    category: str

    condition: str

    image_url: Optional[str]

    location: str

    available_from: date

    available_until: date

    is_active: bool

    availability_status: str = "available"

    created_at: datetime





class BorrowingIn(BaseModel):

    item_id: int

    start_date: date

    due_date: date

    message: str = Field(default="", max_length=1000)





class BorrowingOut(BaseModel):

    id: int

    item_id: int

    item_title: str

    item_image_url: Optional[str]

    item_owner_id: int

    item_owner_name: str

    borrower_id: int

    borrower_name: str

    start_date: date

    due_date: date

    status: str

    message: str

    created_at: datetime

    picked_up_at: Optional[datetime]

    returned_at: Optional[datetime]





class ConditionReportIn(BaseModel):

    report_type: str = Field(pattern="^(pickup|return)$")

    notes: str = Field(default="", max_length=2000)

    photo_url: Optional[str] = Field(default=None, max_length=1000)





class ConditionReportOut(BaseModel):

    id: int

    borrowing_id: int

    report_type: str

    notes: str

    photo_url: Optional[str]

    created_by: int

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)





class MessageIn(BaseModel):

    body: str = Field(min_length=1, max_length=2000)





class MessageOut(BaseModel):

    id: int

    borrowing_id: int

    sender_id: int

    sender_name: str

    body: str

    created_at: datetime

    read_at: Optional[datetime] = None





class NotificationOut(BaseModel):

    id: int

    borrowing_id: Optional[int]

    kind: str

    title: str

    body: str

    created_at: datetime

    read_at: Optional[datetime]





class WantedRequestIn(BaseModel):
    title: str = Field(min_length=2, max_length=140)
    description: str = Field(default="", max_length=2000)
    category: str = Field(default="Other", max_length=60)
    needed_from: date
    needed_until: date
    location: str = Field(default="Campus", max_length=140)

    @field_validator("needed_until")
    @classmethod
    def validate_needed_until(cls, value: date, info):
        start = info.data.get("needed_from")
        if start and value < start:
            raise ValueError("Required-until date must be on or after the start date")
        return value


class WantedRequestOut(BaseModel):
    id: int
    requester_id: int
    requester_name: str
    title: str
    description: str
    category: str
    needed_from: date
    needed_until: date
    location: str
    status: str
    created_at: datetime


class WantedInterestIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)

class WantedInterestOut(BaseModel):
    id: int
    wanted_request_id: int
    lender_id: int
    lender_name: str
    created_at: datetime
    last_message: str = ""

class WantedMessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)

class WantedMessageOut(BaseModel):
    id: int
    interest_id: int
    sender_id: int
    sender_name: str
    body: str
    created_at: datetime


# ---------- Helpers ----------

def create_access_token(user: User) -> str:

    now = datetime.now(timezone.utc)

    payload = {

        "sub": str(user.id),

        "iat": now,

        "exp": now + timedelta(minutes=settings.access_token_minutes),

    }

    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)





def get_current_user(

    db: Session = Depends(get_db),

    authorization: Optional[str] = None,

) -> User:

    # This function is replaced by the Header-aware dependency below.

    raise HTTPException(status_code=401, detail="Authentication required")





from fastapi import Header





def current_user(

    authorization: Optional[str] = Header(default=None),

    db: Session = Depends(get_db),

) -> User:

    if not authorization or not authorization.lower().startswith("bearer "):

        raise HTTPException(status_code=401, detail="Please log in to continue")

    token = authorization.split(" ", 1)[1].strip()

    try:

        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])

        user_id = int(payload.get("sub", ""))

    except (InvalidTokenError, ValueError, TypeError):

        raise HTTPException(status_code=401, detail="Session expired or invalid. Please log in again.")

    user = db.get(User, user_id)

    if not user:

        raise HTTPException(status_code=401, detail="User no longer exists")

    return user





def serialize_item(item: Item) -> dict:

    today = date.today()

    all_reservations = [b for b in item.borrowings if b.status in ACTIVE_RESERVATION_STATUSES]
    current_bookings = [b for b in all_reservations if b.start_date <= today < b.due_date]
    # Confirmed pickup means the physical item is out until return is confirmed.
    physically_out = any(b.status in ("active", "return_pending") for b in all_reservations)
    if not item.is_active:
        availability = "inactive"
    elif physically_out:
        availability = "borrowed"
    elif item.owner and item.owner.availability_status == "not_lending":
        availability = "owner_unavailable"
    elif current_bookings:
        availability = "reserved"
    else:
        availability = "available"
    return {

        "id": item.id, "owner_id": item.owner_id,

        "owner_name": item.owner.name if item.owner else "Member",

        "title": item.title, "description": item.description,

        "category": item.category, "condition": item.condition,

        "image_url": item.image_url, "location": item.location,

        "available_from": item.available_from, "available_until": item.available_until,

        "is_active": item.is_active, "availability_status": availability,

        "created_at": item.created_at,

    }





def serialize_borrowing(b: Borrowing) -> dict:

    return {

        "id": b.id, "item_id": b.item_id,

        "item_title": b.item.title if b.item else "Item",

        "item_image_url": b.item.image_url if b.item else None,

        "item_owner_id": b.item.owner_id if b.item else 0,

        "item_owner_name": b.item.owner.name if b.item and b.item.owner else "Member",

        "borrower_id": b.borrower_id,

        "borrower_name": b.borrower.name if b.borrower else "Member",

        "start_date": b.start_date, "due_date": b.due_date,

        "status": b.status, "message": b.message, "created_at": b.created_at,

        "picked_up_at": b.picked_up_at, "returned_at": b.returned_at,

    }





ACTIVE_RESERVATION_STATUSES = ("approved", "active", "return_pending")





def check_no_conflict(db: Session, item_id: int, start: date, end: date, exclude_id: Optional[int] = None):

    if end <= start:

        raise HTTPException(status_code=422, detail="Return date must be after the start date.")

    stmt = select(Borrowing).where(

        Borrowing.item_id == item_id,

        Borrowing.status.in_(ACTIVE_RESERVATION_STATUSES),

        Borrowing.start_date < end,

        Borrowing.due_date > start,

    )

    if exclude_id is not None:

        stmt = stmt.where(Borrowing.id != exclude_id)

    conflict = db.scalar(stmt.limit(1))

    if conflict:

        raise HTTPException(status_code=409, detail="Those dates overlap with an existing approved booking.")





def get_borrowing_or_404(db: Session, borrowing_id: int) -> Borrowing:

    borrowing = db.get(Borrowing, borrowing_id)

    if not borrowing:

        raise HTTPException(status_code=404, detail="Borrowing request not found")

    return borrowing





def require_owner_or_borrower(b: Borrowing, user: User):

    if user.id not in (b.borrower_id, b.item.owner_id):

        raise HTTPException(status_code=403, detail="You are not a participant in this borrowing")





# ---------- Messaging and notification helpers ----------

def add_notification(db: Session, user_id: int, title: str, body: str, kind: str = "activity", borrowing_id: Optional[int] = None):

    if user_id:

        db.add(Notification(user_id=user_id, borrowing_id=borrowing_id, kind=kind, title=title, body=body))





def message_dict(message: Message) -> dict:

    return {"id": message.id, "borrowing_id": message.borrowing_id, "sender_id": message.sender_id,

            "sender_name": message.sender.name if message.sender else "Member", "body": message.body,

            "created_at": message.created_at, "read_at": message.read_at}





# ---------- Routes ----------

@app.get("/")

def root():

    return {"name": "BorrowBox API", "status": "running", "docs": "/docs"}





@app.get("/api/health")

def health():

    return {"status": "ok", "service": "BorrowBox API"}





@app.post("/api/auth/register", response_model=TokenOut, status_code=201)

def register(payload: RegisterIn, db: Session = Depends(get_db)):

    email = payload.email.lower().strip()

    if db.scalar(select(User).where(User.email == email)):

        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = User(name=payload.name.strip(), email=email, password_hash=hash_password(payload.password))

    db.add(user)

    db.commit()

    db.refresh(user)

    return {"access_token": create_access_token(user), "token_type": "bearer", "user": user}





@app.post("/api/auth/login", response_model=TokenOut)

def login(payload: LoginIn, db: Session = Depends(get_db)):

    user = db.scalar(select(User).where(User.email == payload.email.lower().strip()))

    if not user or not verify_password(payload.password, user.password_hash):

        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    return {"access_token": create_access_token(user), "token_type": "bearer", "user": user}





@app.get("/api/auth/me", response_model=UserOut)

def me(user: User = Depends(current_user)):

    return user





@app.patch("/api/auth/availability", response_model=UserOut)

def update_availability(payload: AvailabilityIn, db: Session = Depends(get_db), user: User = Depends(current_user)):

    user.availability_status = payload.availability_status

    db.commit()

    db.refresh(user)

    return user





@app.post("/api/wanted-requests", response_model=WantedRequestOut, status_code=201)
def create_wanted_request(
    payload: WantedRequestIn,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    if payload.needed_from < date.today():
        raise HTTPException(status_code=422, detail="The required start date cannot be in the past.")

    wanted = WantedRequest(
        requester_id=user.id,
        title=payload.title.strip(),
        description=payload.description.strip(),
        category=payload.category.strip() or "Other",
        needed_from=payload.needed_from,
        needed_until=payload.needed_until,
        location=payload.location.strip() or "Campus",
        status="open",
    )
    db.add(wanted)
    db.commit()
    db.refresh(wanted)
    return {
        "id": wanted.id,
        "requester_id": wanted.requester_id,
        "requester_name": user.name,
        "title": wanted.title,
        "description": wanted.description,
        "category": wanted.category,
        "needed_from": wanted.needed_from,
        "needed_until": wanted.needed_until,
        "location": wanted.location,
        "status": wanted.status,
        "created_at": wanted.created_at,
    }


@app.get("/api/wanted-requests", response_model=List[WantedRequestOut])
def list_wanted_requests(
    search: Optional[str] = Query(default=None, max_length=140),
    category: Optional[str] = Query(default=None, max_length=60),
    db: Session = Depends(get_db),
):
    statement = (
        select(WantedRequest, User.name)
        .join(User, User.id == WantedRequest.requester_id)
        .where(WantedRequest.status == "open")
    )
    if search and search.strip():
        term = f"%{search.strip()}%"
        statement = statement.where(
            or_(WantedRequest.title.ilike(term), WantedRequest.description.ilike(term))
        )
    if category and category.lower() != "all":
        statement = statement.where(WantedRequest.category == category)

    rows = db.execute(statement.order_by(WantedRequest.created_at.desc())).all()
    return [
        {
            "id": wanted.id,
            "requester_id": wanted.requester_id,
            "requester_name": requester_name,
            "title": wanted.title,
            "description": wanted.description,
            "category": wanted.category,
            "needed_from": wanted.needed_from,
            "needed_until": wanted.needed_until,
            "location": wanted.location,
            "status": wanted.status,
            "created_at": wanted.created_at,
        }
        for wanted, requester_name in rows
    ]


@app.post("/api/wanted-requests/{wanted_id}/interests", response_model=WantedInterestOut, status_code=201)
def create_wanted_interest(wanted_id: int, payload: WantedInterestIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    wanted = db.get(WantedRequest, wanted_id)
    if not wanted or wanted.status != "open":
        raise HTTPException(status_code=404, detail="This wanted request is no longer open.")
    if wanted.requester_id == user.id:
        raise HTTPException(status_code=400, detail="You cannot respond to your own request.")
    if user.availability_status == "not_lending":
        raise HTTPException(status_code=409, detail="Your profile is set to not lending right now.")
    interest = db.scalar(select(WantedInterest).where(WantedInterest.wanted_request_id == wanted_id, WantedInterest.lender_id == user.id))
    if not interest:
        interest = WantedInterest(wanted_request_id=wanted_id, lender_id=user.id)
        db.add(interest)
        db.flush()
    body = payload.message.strip()
    if not body:
        raise HTTPException(status_code=422, detail="Please add a message.")
    db.add(WantedMessage(interest_id=interest.id, sender_id=user.id, body=body))
    add_notification(db, wanted.requester_id, f"Someone can help: {wanted.title}", f"{user.name} is interested in your wanted request.", "wanted")
    db.commit(); db.refresh(interest)
    return {"id": interest.id, "wanted_request_id": wanted.id, "lender_id": user.id, "lender_name": user.name, "created_at": interest.created_at, "last_message": body}


@app.get("/api/wanted-requests/{wanted_id}/my-interest", response_model=Optional[WantedInterestOut])
def get_my_wanted_interest(wanted_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    wanted = db.get(WantedRequest, wanted_id)
    if not wanted:
        raise HTTPException(status_code=404, detail="Wanted request not found.")
    interest = db.scalar(select(WantedInterest).where(WantedInterest.wanted_request_id == wanted_id, WantedInterest.lender_id == user.id))
    if not interest:
        return None
    last = db.scalar(select(WantedMessage).where(WantedMessage.interest_id == interest.id).order_by(WantedMessage.created_at.desc()).limit(1))
    return {"id": interest.id, "wanted_request_id": wanted_id, "lender_id": interest.lender_id, "lender_name": interest.lender.name, "created_at": interest.created_at, "last_message": last.body if last else ""}


@app.get("/api/wanted-requests/{wanted_id}/interests", response_model=List[WantedInterestOut])
def list_wanted_interests(wanted_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    wanted = db.get(WantedRequest, wanted_id)
    if not wanted:
        raise HTTPException(status_code=404, detail="Wanted request not found.")
    if wanted.requester_id != user.id:
        raise HTTPException(status_code=403, detail="Only the requester can view all responses.")
    interests = db.scalars(select(WantedInterest).where(WantedInterest.wanted_request_id == wanted_id).order_by(WantedInterest.created_at.desc())).all()
    result = []
    for interest in interests:
        last = db.scalar(select(WantedMessage).where(WantedMessage.interest_id == interest.id).order_by(WantedMessage.created_at.desc()).limit(1))
        result.append({"id": interest.id, "wanted_request_id": wanted.id, "lender_id": interest.lender_id, "lender_name": interest.lender.name, "created_at": interest.created_at, "last_message": last.body if last else ""})
    return result


def require_wanted_participant(interest: WantedInterest, user: User):
    if user.id not in (interest.lender_id, interest.wanted_request.requester_id):
        raise HTTPException(status_code=403, detail="You are not part of this conversation.")


@app.get("/api/wanted-interests/{interest_id}/messages", response_model=List[WantedMessageOut])
def list_wanted_messages(interest_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    interest = db.get(WantedInterest, interest_id)
    if not interest:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    require_wanted_participant(interest, user)
    rows = db.scalars(select(WantedMessage).where(WantedMessage.interest_id == interest_id).order_by(WantedMessage.created_at.asc())).all()
    return [{"id": m.id, "interest_id": m.interest_id, "sender_id": m.sender_id, "sender_name": m.sender.name, "body": m.body, "created_at": m.created_at} for m in rows]


@app.post("/api/wanted-interests/{interest_id}/messages", response_model=WantedMessageOut, status_code=201)
def send_wanted_message(interest_id: int, payload: WantedMessageIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    interest = db.get(WantedInterest, interest_id)
    if not interest:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    require_wanted_participant(interest, user)
    body = payload.body.strip()
    if not body:
        raise HTTPException(status_code=422, detail="Message cannot be empty.")
    message = WantedMessage(interest_id=interest_id, sender_id=user.id, body=body)
    db.add(message)
    other_id = interest.wanted_request.requester_id if user.id == interest.lender_id else interest.lender_id
    add_notification(db, other_id, f"New message about {interest.wanted_request.title}", f"{user.name}: {body[:160]}", "wanted")
    db.commit(); db.refresh(message)
    return {"id": message.id, "interest_id": message.interest_id, "sender_id": user.id, "sender_name": user.name, "body": message.body, "created_at": message.created_at}


@app.get("/api/items", response_model=List[ItemOut])

def list_items(

    search: Optional[str] = Query(default=None, max_length=100),

    category: Optional[str] = Query(default=None, max_length=60),

    mine: bool = False,

    db: Session = Depends(get_db),

):

    # Public listing; personal listings use /api/items/mine.

    stmt = select(Item).order_by(Item.created_at.desc())

    stmt = stmt.where(Item.is_active.is_(True))

    if search:

        term = f"%{search.strip()}%"

        stmt = stmt.where(or_(Item.title.ilike(term), Item.description.ilike(term), Item.category.ilike(term)))

    if category and category.lower() != "all":

        stmt = stmt.where(Item.category == category)

    items = db.scalars(stmt).all()

    return [serialize_item(i) for i in items]





@app.get("/api/items/mine", response_model=List[ItemOut])

def my_items(db: Session = Depends(get_db), user: User = Depends(current_user)):

    items = db.scalars(select(Item).where(Item.owner_id == user.id).order_by(Item.created_at.desc())).all()

    return [serialize_item(i) for i in items]





@app.get("/api/items/{item_id}", response_model=ItemOut)

def get_item(item_id: int, db: Session = Depends(get_db)):

    item = db.get(Item, item_id)

    if not item or not item.is_active:

        raise HTTPException(status_code=404, detail="Item not found")

    return serialize_item(item)





@app.post("/api/items", response_model=ItemOut, status_code=201)

def create_item(payload: ItemIn, db: Session = Depends(get_db), user: User = Depends(current_user)):

    item = Item(owner_id=user.id, title=payload.title.strip(), description=payload.description.strip(),

                category=payload.category.strip() or "Other", condition=payload.condition,

                image_url=payload.image_url.strip() if payload.image_url else None,

                location=payload.location.strip() or "Campus", available_from=payload.available_from,

                available_until=payload.available_until)

    db.add(item)

    db.commit()

    db.refresh(item)

    return serialize_item(item)





@app.patch("/api/items/{item_id}", response_model=ItemOut)

def update_item(item_id: int, payload: ItemIn, db: Session = Depends(get_db), user: User = Depends(current_user)):

    item = db.get(Item, item_id)

    if not item:

        raise HTTPException(status_code=404, detail="Item not found")

    if item.owner_id != user.id:

        raise HTTPException(status_code=403, detail="You can only edit your own listings.")

    if not item.is_active:

        raise HTTPException(status_code=409, detail="This listing is inactive.")

    for key, value in payload.model_dump().items():

        setattr(item, key, value.strip() if isinstance(value, str) else value)

    db.commit()

    db.refresh(item)

    return serialize_item(item)





@app.delete("/api/items/{item_id}")

def deactivate_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):

    item = db.get(Item, item_id)

    if not item:

        raise HTTPException(status_code=404, detail="Item not found")

    if item.owner_id != user.id:

        raise HTTPException(status_code=403, detail="You can only deactivate your own listings.")

    active = db.scalar(select(Borrowing).where(

        Borrowing.item_id == item.id,

        Borrowing.status.in_(ACTIVE_RESERVATION_STATUSES)

    ).limit(1))

    if active:

        raise HTTPException(status_code=409, detail="This item has an active or approved borrowing and cannot be deactivated yet.")

    item.is_active = False

    db.commit()

    return {"message": "Listing deactivated"}





@app.post("/api/borrowings", response_model=BorrowingOut, status_code=201)

def create_borrowing(payload: BorrowingIn, db: Session = Depends(get_db), user: User = Depends(current_user)):

    item = db.get(Item, payload.item_id)

    if not item or not item.is_active:

        raise HTTPException(status_code=404, detail="This item is not available.")

    if item.owner_id == user.id:

        raise HTTPException(status_code=400, detail="You cannot borrow your own item.")

    if item.owner.availability_status == "not_lending":

        raise HTTPException(status_code=409, detail="This lender is not accepting borrowing requests right now.")

    if db.scalar(select(Borrowing.id).where(Borrowing.item_id == item.id, Borrowing.status.in_(("active", "return_pending"))).limit(1)):
        raise HTTPException(status_code=409, detail="This item has already been handed to a borrower and is unavailable until the return is confirmed.")

    if payload.start_date < date.today():

        raise HTTPException(status_code=422, detail="Start date cannot be in the past.")

    if payload.due_date <= payload.start_date:

        raise HTTPException(status_code=422, detail="Return date must be after the pickup date.")

    if payload.start_date < item.available_from or payload.due_date > item.available_until:

        raise HTTPException(status_code=409, detail=f"This item is only offered from {item.available_from} through {item.available_until}. Choose dates within that window.")

    check_no_conflict(db, item.id, payload.start_date, payload.due_date)

    borrowing = Borrowing(item_id=item.id, borrower_id=user.id, start_date=payload.start_date,

                          due_date=payload.due_date, status="pending", message=payload.message.strip())

    db.add(borrowing)

    db.flush()

    add_notification(db, item.owner_id, "New borrowing request", f"{user.name} requested {item.title} for {payload.start_date} to {payload.due_date}.", "request", borrowing.id)

    db.commit()

    db.refresh(borrowing)

    return serialize_borrowing(borrowing)





@app.get("/api/borrowings/mine", response_model=List[BorrowingOut])

def my_borrowings(db: Session = Depends(get_db), user: User = Depends(current_user)):

    rows = db.scalars(select(Borrowing).where(Borrowing.borrower_id == user.id).order_by(Borrowing.created_at.desc())).all()

    return [serialize_borrowing(b) for b in rows]





@app.get("/api/borrowings/received", response_model=List[BorrowingOut])

def received_borrowings(db: Session = Depends(get_db), user: User = Depends(current_user)):

    rows = db.scalars(

        select(Borrowing).join(Item).where(Item.owner_id == user.id).order_by(Borrowing.created_at.desc())

    ).all()

    return [serialize_borrowing(b) for b in rows]





@app.get("/api/reminders")

def get_reminders(db: Session = Depends(get_db), user: User = Depends(current_user)):

    """Return in-app due-date reminders for the borrower and return-confirmation reminders for lenders."""

    today = date.today()

    reminders = []

    sent = db.scalars(select(Borrowing).where(

        Borrowing.borrower_id == user.id,

        Borrowing.status.in_(("approved", "active"))

    ).order_by(Borrowing.due_date.asc())).all()

    for borrowing in sent:

        days = (borrowing.due_date - today).days

        if borrowing.status == "active" and days < 0:

            reminders.append({"id": f"overdue-{borrowing.id}", "borrowing_id": borrowing.id,

                "item_title": borrowing.item.title, "due_date": borrowing.due_date,

                "type": "overdue", "days_remaining": days, "role": "borrower",

                "message": f"{borrowing.item.title} is overdue. Please arrange its return."})

        elif borrowing.status == "active" and 0 <= days <= 3:

            reminders.append({"id": f"due-{borrowing.id}", "borrowing_id": borrowing.id,

                "item_title": borrowing.item.title, "due_date": borrowing.due_date,

                "type": "due_soon", "days_remaining": days, "role": "borrower",

                "message": "Due today — please return this item." if days == 0 else f"Return this item in {days} day{'s' if days != 1 else ''}."})

    incoming = db.scalars(select(Borrowing).join(Item).where(

        Item.owner_id == user.id, Borrowing.status == "return_pending"

    ).order_by(Borrowing.returned_at.asc())).all()

    for borrowing in incoming:

        reminders.append({"id": f"confirm-{borrowing.id}", "borrowing_id": borrowing.id,

            "item_title": borrowing.item.title, "due_date": borrowing.due_date,

            "type": "confirm_return", "days_remaining": None, "role": "lender",

            "message": f"{borrowing.borrower.name} marked {borrowing.item.title} as returned. Confirm receipt."})

    return sorted(reminders, key=lambda r: (0 if r["type"] == "overdue" else 1 if r["type"] == "due_soon" else 2, str(r["due_date"])))





@app.get("/api/borrowings/{borrowing_id}", response_model=BorrowingOut)

def get_borrowing(borrowing_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):

    b = get_borrowing_or_404(db, borrowing_id)

    require_owner_or_borrower(b, user)

    return serialize_borrowing(b)





@app.patch("/api/borrowings/{borrowing_id}/approve", response_model=BorrowingOut)

def approve_borrowing(borrowing_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):

    b = get_borrowing_or_404(db, borrowing_id)

    if b.item.owner_id != user.id:

        raise HTTPException(status_code=403, detail="Only the item owner can approve this request.")

    if b.status != "pending":

        raise HTTPException(status_code=409, detail="Only pending requests can be approved.")

    check_no_conflict(db, b.item_id, b.start_date, b.due_date, exclude_id=b.id)

    b.status = "approved"

    add_notification(db, b.borrower_id, "Request approved", f"Your request for {b.item.title} was approved. Coordinate pickup in BorrowBox chat.", "status", b.id)

    db.commit()

    db.refresh(b)

    return serialize_borrowing(b)





@app.patch("/api/borrowings/{borrowing_id}/reject", response_model=BorrowingOut)

def reject_borrowing(borrowing_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):

    b = get_borrowing_or_404(db, borrowing_id)

    if b.item.owner_id != user.id:

        raise HTTPException(status_code=403, detail="Only the item owner can reject this request.")

    if b.status != "pending":

        raise HTTPException(status_code=409, detail="Only pending requests can be rejected.")

    b.status = "rejected"

    add_notification(db, b.borrower_id, "Request declined", f"Your request for {b.item.title} was declined.", "status", b.id)

    db.commit()

    db.refresh(b)

    return serialize_borrowing(b)





@app.patch("/api/borrowings/{borrowing_id}/cancel", response_model=BorrowingOut)

def cancel_borrowing(borrowing_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):

    b = get_borrowing_or_404(db, borrowing_id)

    if b.borrower_id != user.id:

        raise HTTPException(status_code=403, detail="Only the borrower can cancel this request.")

    if b.status not in ("pending", "approved"):

        raise HTTPException(status_code=409, detail="This request can no longer be cancelled.")

    b.status = "cancelled"

    add_notification(db, b.item.owner_id, "Request cancelled", f"{user.name} cancelled the request for {b.item.title}.", "status", b.id)

    db.commit()

    db.refresh(b)

    return serialize_borrowing(b)





@app.patch("/api/borrowings/{borrowing_id}/pickup", response_model=BorrowingOut)

def pickup_borrowing(borrowing_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):

    b = get_borrowing_or_404(db, borrowing_id)

    if b.borrower_id != user.id:

        raise HTTPException(status_code=403, detail="Only the borrower can confirm pickup.")

    if b.status != "approved":

        raise HTTPException(status_code=409, detail="Only approved requests can be picked up.")

    b.status = "active"

    b.picked_up_at = datetime.utcnow()

    add_notification(db, b.item.owner_id, "Pickup confirmed", f"{user.name} confirmed pickup of {b.item.title}.", "status", b.id)

    db.commit()

    db.refresh(b)

    return serialize_borrowing(b)





@app.patch("/api/borrowings/{borrowing_id}/return", response_model=BorrowingOut)

def return_borrowing(borrowing_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):

    b = get_borrowing_or_404(db, borrowing_id)

    if b.borrower_id != user.id:

        raise HTTPException(status_code=403, detail="Only the borrower can mark an item returned.")

    if b.status != "active":

        raise HTTPException(status_code=409, detail="Only active borrowings can be marked returned.")

    b.status = "return_pending"

    b.returned_at = datetime.utcnow()

    add_notification(db, b.item.owner_id, "Return awaiting confirmation", f"{user.name} marked {b.item.title} as returned. Please confirm receipt.", "return", b.id)

    db.commit()

    db.refresh(b)

    return serialize_borrowing(b)





@app.patch("/api/borrowings/{borrowing_id}/confirm-return", response_model=BorrowingOut)

def confirm_return(borrowing_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):

    b = get_borrowing_or_404(db, borrowing_id)

    if b.item.owner_id != user.id:

        raise HTTPException(status_code=403, detail="Only the item owner can confirm receipt.")

    if b.status != "return_pending":

        raise HTTPException(status_code=409, detail="This borrowing is not awaiting return confirmation.")

    b.status = "completed"

    add_notification(db, b.borrower_id, "Return confirmed", f"The lender confirmed receipt of {b.item.title}. This transaction is complete.", "status", b.id)

    db.commit()

    db.refresh(b)

    return serialize_borrowing(b)





@app.get("/api/notifications", response_model=List[NotificationOut])

def list_notifications(db: Session = Depends(get_db), user: User = Depends(current_user)):

    return db.scalars(select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(100)).all()





@app.get("/api/notifications/unread-count")

def unread_notification_count(db: Session = Depends(get_db), user: User = Depends(current_user)):

    count = db.scalar(select(func.count(Notification.id)).where(Notification.user_id == user.id, Notification.read_at.is_(None))) or 0

    unread_messages = db.scalar(select(func.count(Message.id)).join(Borrowing, Message.borrowing_id == Borrowing.id).join(Item, Borrowing.item_id == Item.id).where(

        Message.sender_id != user.id, Message.read_at.is_(None), or_(Borrowing.borrower_id == user.id, Item.owner_id == user.id))) or 0

    return {"notifications": count, "messages": unread_messages, "total": count + unread_messages}





@app.patch("/api/notifications/{notification_id}/read")

def mark_notification_read(notification_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):

    item = db.get(Notification, notification_id)

    if not item or item.user_id != user.id:

        raise HTTPException(status_code=404, detail="Notification not found")

    if item.read_at is None:

        item.read_at = datetime.utcnow()

        db.commit()

    return {"message": "Notification marked as read"}





@app.patch("/api/notifications/read-all")

def mark_all_notifications_read(db: Session = Depends(get_db), user: User = Depends(current_user)):

    rows = db.scalars(select(Notification).where(Notification.user_id == user.id, Notification.read_at.is_(None))).all()

    now = datetime.utcnow()

    for row in rows: row.read_at = now

    db.commit()

    return {"updated": len(rows)}





@app.get("/api/messages/conversations")

def list_conversations(db: Session = Depends(get_db), user: User = Depends(current_user)):

    rows = db.scalars(select(Borrowing).join(Item).where(

        or_(Borrowing.borrower_id == user.id, Item.owner_id == user.id),

        Borrowing.status.notin_(("rejected", "cancelled"))

    ).order_by(Borrowing.created_at.desc())).all()

    result = []

    for b in rows:

        last = db.scalar(select(Message).where(Message.borrowing_id == b.id).order_by(Message.created_at.desc()).limit(1))

        unread = db.scalar(select(func.count(Message.id)).where(Message.borrowing_id == b.id, Message.sender_id != user.id, Message.read_at.is_(None))) or 0

        other = b.item.owner if user.id == b.borrower_id else b.borrower

        result.append({"borrowing_id": b.id, "item_title": b.item.title, "status": b.status,

                       "other_user_id": other.id, "other_user_name": other.name,

                       "start_date": b.start_date, "due_date": b.due_date,

                       "last_message": last.body if last else "Start coordinating pickup or return",

                       "last_message_at": last.created_at if last else b.created_at, "unread_count": unread})

    return result





@app.get("/api/borrowings/{borrowing_id}/messages", response_model=List[MessageOut])

def list_messages(borrowing_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):

    b = get_borrowing_or_404(db, borrowing_id)

    require_owner_or_borrower(b, user)

    rows = db.scalars(select(Message).where(Message.borrowing_id == borrowing_id).order_by(Message.created_at.asc())).all()

    now = datetime.utcnow()

    changed = False

    for row in rows:

        if row.sender_id != user.id and row.read_at is None:

            row.read_at = now; changed = True

    if changed: db.commit()

    return [message_dict(row) for row in rows]





@app.post("/api/borrowings/{borrowing_id}/messages", response_model=MessageOut, status_code=201)

def send_message(borrowing_id: int, payload: MessageIn, db: Session = Depends(get_db), user: User = Depends(current_user)):

    b = get_borrowing_or_404(db, borrowing_id)

    require_owner_or_borrower(b, user)

    if b.status in ("rejected", "cancelled"):

        raise HTTPException(status_code=409, detail="Messaging is unavailable for rejected or cancelled requests.")

    body = payload.body.strip()

    if not body:

        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    message = Message(borrowing_id=b.id, sender_id=user.id, body=body)

    db.add(message)

    other_id = b.item.owner_id if user.id == b.borrower_id else b.borrower_id

    add_notification(db, other_id, f"New message about {b.item.title}", f"{user.name}: {body[:160]}", "message", b.id)

    db.commit(); db.refresh(message)

    return message_dict(message)





@app.post("/api/borrowings/{borrowing_id}/condition-reports", response_model=ConditionReportOut, status_code=201)

def create_condition_report(

    borrowing_id: int, payload: ConditionReportIn,

    db: Session = Depends(get_db), user: User = Depends(current_user)

):

    b = get_borrowing_or_404(db, borrowing_id)

    require_owner_or_borrower(b, user)

    if payload.report_type == "pickup" and b.status not in ("approved", "active"):

        raise HTTPException(status_code=409, detail="Pickup reports can only be added around pickup.")

    if payload.report_type == "return" and b.status not in ("active", "return_pending", "completed"):

        raise HTTPException(status_code=409, detail="Return reports can only be added around return.")

    report = ConditionReport(

        borrowing_id=b.id, report_type=payload.report_type,

        notes=payload.notes.strip(), photo_url=payload.photo_url.strip() if payload.photo_url else None,

        created_by=user.id

    )

    db.add(report)

    db.commit()

    db.refresh(report)

    return report





@app.get("/api/borrowings/{borrowing_id}/condition-reports", response_model=List[ConditionReportOut])

def list_condition_reports(

    borrowing_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)

):

    b = get_borrowing_or_404(db, borrowing_id)

    require_owner_or_borrower(b, user)

    return db.scalars(

        select(ConditionReport).where(ConditionReport.borrowing_id == borrowing_id)

        .order_by(ConditionReport.created_at.asc())

    ).all()
