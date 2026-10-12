import { useLocation, useNavigate } from "react-router-dom";
import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowRight, ArrowUpRight, BadgeCheck, Bell, BookOpen, CalendarDays, Check,
  CheckCircle2, ChevronDown, Clock3, Compass, Filter, HandHeart, HeartHandshake,
  Laptop, Leaf, LogIn, LogOut, Menu, Package, PackagePlus, Search, ShieldCheck,
  Sparkles, UserRound, X, Plus, LayoutDashboard, MapPin, RefreshCw, AlertCircle,
  ClipboardCheck, Pencil, Trash2, Send, Eye, CircleHelp, CheckCircle, AlarmClock, History, CalendarCheck, SlidersHorizontal, MessageSquare
} from "lucide-react";
import { api } from "./api";

const categories = ["All", "Books", "Electronics", "Study essentials", "Tools", "Sports", "Lifestyle", "Other"];
const demoImages = {
  Books: "https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&w=900&q=80",
  Electronics: "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=80",
  "Study essentials": "https://images.unsplash.com/photo-1455390582262-044c065d9b84?auto=format&fit=crop&w=900&q=80",
  Tools: "https://images.unsplash.com/photo-1504148455328-c376907d081c?auto=format&fit=crop&w=900&q=80",
  Sports: "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?auto=format&fit=crop&w=900&q=80",
  Lifestyle: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=80",
  Other: "https://images.unsplash.com/photo-1494438639946-1ebd1d20bf85?auto=format&fit=crop&w=900&q=80"
};
const money = n => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n || 0);
const fmtDate = s => s ? new Date(`${s}T00:00:00`).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" }) : "—";
const initials = name => (name || "B").split(" ").map(x => x[0]).join("").slice(0, 2).toUpperCase();

function ItemImage({ item, className = "" }) {
  const [failed, setFailed] = useState(false);
  const url = item.image_url || demoImages[item.category] || demoImages.Other;
  return <div className={`item-image ${className}`}>
    {!failed ? <img src={url} alt={item.title} onError={() => setFailed(true)} /> :
      <div className="image-fallback"><Package size={32}/><span>{item.category}</span></div>}
    <span className="condition-pill">{item.condition || "Good"} condition</span>
  </div>;
}

function Brand({ onClick }) {
  return <button className="brand" onClick={onClick} aria-label="BorrowBox home">
    <span className="brand-mark"><Package size={21} strokeWidth={2.4}/></span>
    <span>borrow<span className="brand-accent">box</span><small>SHARE MORE. BUY LESS.</small></span>
  </button>;
}

function Button({ children, variant = "primary", size = "", className = "", ...props }) {
  return <button className={`btn btn-${variant} ${size ? `btn-${size}` : ""} ${className}`} {...props}>{children}</button>;
}

function StatusBadge({ status }) {
  const labels = {
    pending: "Awaiting approval", approved: "Approved", rejected: "Declined",
    cancelled: "Cancelled", active: "Borrowed", return_pending: "Return pending",
    completed: "Completed"
  };
  return <span className={`status status-${status}`}>{labels[status] || status}</span>;
}

function Modal({ title, subtitle, onClose, children, wide = false }) {
  useEffect(() => {
    const fn = e => e.key === "Escape" && onClose();
    window.addEventListener("keydown", fn);
    return () => window.removeEventListener("keydown", fn);
  }, [onClose]);
  return <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && onClose()}>
    <div className={`modal ${wide ? "modal-wide" : ""}`}>
      <div className="modal-head"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div><button className="icon-btn" onClick={onClose}><X size={20}/></button></div>
      {children}
    </div>
  </div>;
}

function AuthModal({ mode, setMode, onClose, onSuccess, notify }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async e => {
    e.preventDefault(); setBusy(true);
    try {
      const result = await api(mode === "register" ? "/api/auth/register" : "/api/auth/login", {
        method: "POST", body: JSON.stringify(mode === "register" ? { name, email, password } : { email, password })
      });
      localStorage.setItem("borrowbox_token", result.access_token);
      onSuccess(result.user); notify(mode === "register" ? "Welcome to BorrowBox!" : "You're signed in. Welcome back!", "success"); onClose();
    } catch (err) { notify(err.message, "error"); }
    finally { setBusy(false); }
  };
  return <Modal title={mode === "register" ? "Join the sharing circle" : "Welcome back"} subtitle={mode === "register" ? "One small share can make a big difference." : "Sign in to continue your BorrowBox journey."} onClose={onClose}>
    <form className="form-stack" onSubmit={submit}>
      {mode === "register" && <label>Your name<input required minLength="2" value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Swetha L." /></label>}
      <label>Email address<input required type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" /></label>
      <label>Password<input required minLength="8" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="At least 8 characters" /></label>
      <Button disabled={busy} type="submit" className="full-width">{busy ? "Please wait…" : mode === "register" ? "Create my account" : "Sign in"} <ArrowRight size={17}/></Button>
      <p className="form-switch">{mode === "register" ? "Already part of the circle?" : "New to BorrowBox?"} <button type="button" onClick={() => setMode(mode === "register" ? "login" : "register")}>{mode === "register" ? "Sign in" : "Create an account"}</button></p>
    </form>
  </Modal>;
}

function AuthPage({ mode, onSuccess, notify, onNavigateHome }) {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const register = mode === "register";
  const submit = async e => {
    e.preventDefault();
    if (register && password !== confirm) { notify("Passwords do not match.", "error"); return; }
    setBusy(true);
    try {
      const result = await api(register ? "/api/auth/register" : "/api/auth/login", {
        method: "POST", body: JSON.stringify(register ? { name, email, password } : { email, password })
      });
      localStorage.setItem("borrowbox_token", result.access_token);
      onSuccess(result.user); notify(register ? "Welcome to BorrowBox!" : "You're signed in. Welcome back!", "success");
      navigate("/dashboard");
    } catch (err) { notify(err.message, "error"); }
    finally { setBusy(false); }
  };
  return <div className="auth-page page-container">
    <section className="auth-visual"><div className="auth-visual-mark"><Package size={25}/></div><div className="eyebrow">YOUR COMMUNITY, SHARED</div><h1>{register ? "Make room for a little more sharing." : "Welcome back to your sharing circle."}</h1><p>{register ? "Create an account to lend what you own, borrow what you need, and keep every return on track." : "Your items, borrowing requests, and return reminders are all waiting in one place."}</p><div className="auth-benefits"><span><CheckCircle2 size={17}/> Lend and borrow with one account</span><span><CheckCircle2 size={17}/> Know what's available</span><span><CheckCircle2 size={17}/> Never lose track of a return</span></div><div className="auth-illustration"><div className="auth-float-card"><BookOpen size={22}/><div><strong>Share a little</strong><small>Make someone's day easier</small></div></div><div className="auth-float-card auth-float-card-two"><CalendarCheck size={22}/><div><strong>Return on time</strong><small>Friendly reminders included</small></div></div></div></section>
    <section className="auth-form-side"><button className="auth-back" onClick={onNavigateHome}>← Back to BorrowBox</button><div className="auth-form-wrap"><div className="eyebrow">{register ? "START SHARING" : "YOUR SPACE IS READY"}</div><h2>{register ? "Create your account" : "Sign in to BorrowBox"}</h2><p className="auth-form-subtitle">{register ? "It only takes a minute to join." : "Pick up where your community left off."}</p><form className="form-stack auth-page-form" onSubmit={submit}>
      {register && <label>Full name<input autoComplete="name" required minLength="2" maxLength="100" value={name} onChange={e => setName(e.target.value)} placeholder="Your name"/></label>}
      <label>Email address<input autoComplete="email" required type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com"/></label>
      <label>Password<input autoComplete={register ? "new-password" : "current-password"} required minLength={register ? 8 : 1} type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder={register ? "At least 8 characters" : "Enter your password"}/></label>
      {register && <label>Confirm password<input autoComplete="new-password" required minLength="8" type="password" value={confirm} onChange={e => setConfirm(e.target.value)} placeholder="Re-enter your password"/></label>}
      <Button type="submit" disabled={busy} className="full-width auth-submit">{busy ? "Please wait…" : register ? "Create my account" : "Sign in securely"}<ArrowRight size={17}/></Button>
    </form><div className="auth-switch">{register ? "Already have an account?" : "New to BorrowBox?"} <button onClick={() => navigate(register ? "/login" : "/register")}>{register ? "Sign in" : "Create an account"}</button></div><div className="auth-security"><ShieldCheck size={16}/> Your account is protected with secure password hashing.</div></div></section>
  </div>;
}

function ItemCard({ item, currentUser, onOpen, onEdit, onDelete }) {
  const mine = currentUser && item.owner_id === currentUser.id;
  const availability = item.availability_status || (item.is_active ? "available" : "inactive");
  const availabilityLabel = { available: "Available", reserved: "Reserved today", borrowed: "Unavailable · borrowed", inactive: "Inactive listing", owner_unavailable: "Lender unavailable" }[availability] || "Availability varies by dates";
  return <article className="item-card">
    <button className="item-open" onClick={() => onOpen(item)} aria-label={`View ${item.title}`}><ItemImage item={item}/></button>
    <div className="item-card-body">
      <div className="item-category-row"><div className="item-category">{item.category}</div><span className={`availability-pill availability-${availability}`}><span/> {availabilityLabel}</span></div>
      <button className="item-title" onClick={() => onOpen(item)}>{item.title}</button>
      <p className="item-description">{item.description || "A useful item ready for its next adventure."}</p>
      <div className="item-meta"><span><MapPin size={14}/>{item.location || "Campus"}</span><span><UserRound size={14}/>{mine ? "Your listing" : item.owner_name}</span></div>
      <div className="item-date-window"><CalendarDays size={14}/> Lendable {fmtDate(item.available_from)} – {fmtDate(item.available_until)}</div>
      <div className="item-card-footer">
        <span className="free-label"><HeartHandshake size={15}/> Free to borrow</span>
        {mine ? <div className="mini-actions"><button title="Edit listing" onClick={() => onEdit(item)}><Pencil size={16}/></button><button title="Deactivate listing" onClick={() => onDelete(item)}><Trash2 size={16}/></button></div> :
          <Button variant="dark" size="sm" onClick={() => onOpen(item)}>View item <ArrowUpRight size={15}/></Button>}
      </div>
    </div>
  </article>;
}

function ItemForm({ item, onClose, onSaved, notify }) {
  const [form, setForm] = useState({
    title: item?.title || "", description: item?.description || "", category: item?.category || "Study essentials",
    condition: item?.condition || "Good", image_url: item?.image_url || "", location: item?.location || "Campus",
    available_from: item?.available_from || new Date(Date.now() + 86400000).toLocaleDateString("en-CA"),
    available_until: item?.available_until || new Date(Date.now() + 180 * 86400000).toLocaleDateString("en-CA")
  });
  const [busy, setBusy] = useState(false);
  const change = e => {
    const { name, value } = e.target;
    setForm(previous => {
      const next = { ...previous, [name]: value };
      if (name === "available_from" && next.available_until <= value) {
        const suggested = new Date(`${value}T00:00:00`);
        suggested.setDate(suggested.getDate() + 30);
        next.available_until = `${suggested.getFullYear()}-${String(suggested.getMonth()+1).padStart(2,"0")}-${String(suggested.getDate()).padStart(2,"0")}`;
      }
      return next;
    });
  };
  const submit = async e => {
    e.preventDefault(); setBusy(true);
    try {
      await api(item ? `/api/items/${item.id}` : "/api/items", { method: item ? "PATCH" : "POST", body: JSON.stringify(form) });
      notify(item ? "Listing updated." : "Your item is now listed!", "success"); onSaved(); onClose();
    } catch (err) { notify(err.message, "error"); }
    finally { setBusy(false); }
  };
  return <Modal title={item ? "Edit your listing" : "Give an item a second life"} subtitle="Add a few details so the right person can find it." onClose={onClose}>
    <form className="form-stack" onSubmit={submit}>
      <label>Item name<input required minLength="2" maxLength="140" name="title" value={form.title} onChange={change} placeholder="e.g. Scientific calculator" /></label>
      <label>Description<textarea name="description" maxLength="3000" rows="3" value={form.description} onChange={change} placeholder="What should a borrower know about it?"/></label>
      <div className="form-grid">
        <label>Category<select name="category" value={form.category} onChange={change}>{categories.filter(c => c !== "All").map(c => <option key={c}>{c}</option>)}</select></label>
        <label>Condition<select name="condition" value={form.condition} onChange={change}>{["New", "Like new", "Good", "Fair"].map(c => <option key={c}>{c}</option>)}</select></label>
      </div>
      <label>Photo URL <span className="optional">optional</span><input name="image_url" type="url" value={form.image_url} onChange={change} placeholder="https://…"/></label>
      <label>Pickup area<input name="location" maxLength="140" value={form.location} onChange={change} placeholder="e.g. Library entrance"/></label>
      <div className="availability-window-box"><div><CalendarDays size={17}/><strong>When can people borrow this item?</strong></div><p>Borrowers can only request dates inside this availability window.</p><div className="form-grid"><label>Available from<input type="date" name="available_from" required min={new Date().toLocaleDateString("en-CA")} value={form.available_from} onChange={change}/></label><label>Available until<input type="date" name="available_until" required min={form.available_from || new Date().toLocaleDateString("en-CA")} value={form.available_until} onChange={change}/></label></div></div>
      <Button type="submit" disabled={busy} className="full-width">{busy ? "Saving…" : item ? "Save changes" : "Publish listing"} <ArrowRight size={17}/></Button>
    </form>
  </Modal>;
}

function ItemDetail({ item, currentUser, onClose, onBorrow, onEdit }) {
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const isOwner = currentUser && currentUser.id === item.owner_id;
  const minDate = new Date().toLocaleDateString("en-CA");
  const windowStart = item.available_from || minDate;
  const windowEnd = item.available_until || "";
  const submit = async e => {
    e.preventDefault(); setError("");
    if (!currentUser) { setError("Please sign in to request an item."); return; }
    if (isOwner) { setError("You cannot borrow your own listing."); return; }
    setBusy(true);
    try {
      await api("/api/borrowings", { method: "POST", body: JSON.stringify({ item_id: item.id, start_date: start, due_date: end, message }) });
      onBorrow(); onClose();
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };
  return <Modal wide title={item.title} subtitle={`${item.category} · shared by ${item.owner_name}`} onClose={onClose}>
    <div className="detail-layout">
      <ItemImage item={item} className="detail-image"/>
      <div className="detail-content">
        <div className="detail-badges"><span className="soft-tag">{item.condition} condition</span><span className="free-label"><HeartHandshake size={15}/> Free to borrow</span></div>
        <p className="detail-description">{item.description || "This useful item is ready to be shared. Send a request to coordinate dates with the owner."}</p>
        <div className="detail-info"><span><MapPin size={16}/>{item.location || "Campus pickup"}</span><span><UserRound size={16}/>{item.owner_name}</span><span><span className={`availability-dot availability-dot-${item.availability_status || "available"}`}/>{({available:"Available to request",reserved:"Reserved for today",borrowed:"Currently borrowed",inactive:"Inactive listing",owner_unavailable:"Lender is not lending right now"})[item.availability_status || "available"]}</span><span><CalendarDays size={16}/>Lendable {fmtDate(windowStart)} – {fmtDate(windowEnd)}</span></div>
        {isOwner ? <div className="notice"><CheckCircle2 size={18}/> This is your listing. You can manage it from your dashboard.</div> : item.availability_status === "borrowed" ? <div className="notice notice-unavailable"><AlertCircle size={18}/> This item has been handed to a borrower and is currently unavailable. It will become requestable after the lender confirms its return.</div> : item.availability_status === "owner_unavailable" ? <div className="notice notice-unavailable"><AlertCircle size={18}/> This lender has paused lending and is not accepting new requests right now.</div> :
          <form className="form-stack request-form" onSubmit={submit}>
            <h3>Request to borrow</h3>
            <div className="form-grid"><label>Pickup date<input type="date" required min={windowStart > minDate ? windowStart : minDate} max={windowEnd || undefined} value={start} onChange={e => { setStart(e.target.value); if (end && e.target.value >= end) setEnd(""); }}/></label><label>Return date<input type="date" required min={start || windowStart} max={windowEnd || undefined} value={end} onChange={e => setEnd(e.target.value)}/></label></div>
            <label>Message to owner <span className="optional">optional</span><textarea rows="2" maxLength="1000" value={message} onChange={e => setMessage(e.target.value)} placeholder="What do you need it for?"/></label>
            {error && <div className="inline-error"><AlertCircle size={16}/>{error}</div>}
            <Button type="submit" disabled={busy} className="full-width">{busy ? "Sending request…" : "Send borrowing request"} <ArrowRight size={17}/></Button>
            <p className="tiny-note"><ShieldCheck size={14}/> The owner must approve your request before pickup.</p>
          </form>}
      </div>
    </div>
  </Modal>;
}

function ReportModal({ borrowing, onClose, onSaved, notify }) {
  const [type, setType] = useState(borrowing.status === "approved" ? "pickup" : "return");
  const [notes, setNotes] = useState("");
  const [photo, setPhoto] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async e => {
    e.preventDefault(); setBusy(true);
    try {
      await api(`/api/borrowings/${borrowing.id}/condition-reports`, { method: "POST", body: JSON.stringify({ report_type: type, notes, photo_url: photo || null }) });
      notify("Condition report saved.", "success"); onSaved(); onClose();
    } catch (err) { notify(err.message, "error"); }
    finally { setBusy(false); }
  };
  return <Modal title="Condition passport" subtitle={`Record the item's condition · ${borrowing.item_title}`} onClose={onClose}>
    <form className="form-stack" onSubmit={submit}>
      <label>Report type<select value={type} onChange={e => setType(e.target.value)}><option value="pickup">At pickup</option><option value="return">At return</option></select></label>
      <label>Condition notes<textarea rows="4" maxLength="2000" value={notes} onChange={e => setNotes(e.target.value)} placeholder="Describe scratches, missing parts, or the item's current state…" required/></label>
      <label>Photo URL <span className="optional">optional</span><input type="url" value={photo} onChange={e => setPhoto(e.target.value)} placeholder="https://…"/></label>
      <Button type="submit" disabled={busy} className="full-width">{busy ? "Saving…" : "Save condition report"} <ClipboardCheck size={17}/></Button>
    </form>
  </Modal>;
}

function MessageSquareIcon() { return <MessageSquare size={18}/>; }

function ChatModal({ borrowing, onClose, notify, user }) {
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const loadMessages = useCallback(async (quiet = false) => {
    try {
      const data = await api(`/api/borrowings/${borrowing.id}/messages`);
      setMessages(data);
    } catch (err) { if (!quiet) notify(err.message, "error"); }
    finally { if (!quiet) setLoading(false); }
  }, [borrowing.id, notify]);
  useEffect(() => {
    loadMessages();
    const timer = window.setInterval(() => loadMessages(true), 3000);
    return () => window.clearInterval(timer);
  }, [loadMessages]);
  useEffect(() => {
    const node = document.querySelector(".chat-messages");
    if (node) node.scrollTop = node.scrollHeight;
  }, [messages]);
  const send = async e => {
    e.preventDefault();
    if (!draft.trim()) return;
    setSending(true);
    try {
      const message = await api(`/api/borrowings/${borrowing.id}/messages`, { method: "POST", body: JSON.stringify({ body: draft.trim() }) });
      setMessages(current => current.some(x => x.id === message.id) ? current : [...current, message]);
      setDraft("");
    } catch (err) { notify(err.message, "error"); }
    finally { setSending(false); }
  };
  return <Modal wide title={`Chat · ${borrowing.item_title}`} subtitle={`Transaction #${borrowing.id} · Coordinate pickup, questions, and returns privately.`} onClose={onClose}>
    <div className="chat-context"><span className={`status status-${borrowing.status}`}>{borrowing.status.replaceAll("_", " ")}</span><span><CalendarDays size={14}/> {fmtDate(borrowing.start_date)} – {fmtDate(borrowing.due_date)}</span><span><ShieldCheck size={14}/> Only transaction participants can view this chat</span></div>
    <div className="chat-messages" aria-live="polite">
      {loading ? <div className="loading-state"><div className="spinner"/>Loading conversation…</div> : messages.length ? messages.map(m => <article key={m.id} className={`chat-bubble ${m.sender_id === user.id ? "chat-mine" : ""}`}><div className="chat-message-meta"><strong>{m.sender_name}</strong><small>{new Date(m.created_at).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}</small></div><p>{m.body}</p></article>) : <EmptyState icon={Send} title="Start the conversation" text="Ask about pickup time, location, item condition, or return arrangements."/>}
    </div>
    <form className="chat-compose" onSubmit={send}><textarea value={draft} onChange={e => setDraft(e.target.value)} maxLength={2000} rows={2} placeholder="Write a message about this borrowing…" aria-label="Message"/><Button type="submit" disabled={sending || !draft.trim()}>{sending ? "Sending…" : "Send"} <Send size={16}/></Button></form>
    <p className="chat-poll-note"><RefreshCw size={12}/> Messages refresh automatically every 3 seconds while this chat is open.</p>
  </Modal>;
}


function WantedChatModal({ interest, user, onClose, notify }) {
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const load = useCallback(async () => {
    try { setMessages(await api(`/api/wanted-interests/${interest.id}/messages`)); }
    catch (err) { notify(err.message, "error"); }
  }, [interest.id, notify]);
  useEffect(() => { load(); const timer = window.setInterval(load, 3000); return () => window.clearInterval(timer); }, [load]);
  const send = async e => {
    e.preventDefault(); if (!draft.trim()) return; setSending(true);
    try { await api(`/api/wanted-interests/${interest.id}/messages`, { method: "POST", body: JSON.stringify({ body: draft.trim() }) }); setDraft(""); await load(); }
    catch (err) { notify(err.message, "error"); } finally { setSending(false); }
  };
  return <Modal title={`Chat with ${interest.lender_id === user?.id ? "the requester" : interest.lender_name}`} subtitle="Discuss availability and coordinate the handover." onClose={onClose} wide>
    <div className="chat-messages wanted-chat-messages">{messages.map(m => <div key={m.id} className={`chat-message ${m.sender_id === user?.id ? "own-message" : ""}`}><div className="chat-message-meta"><strong>{m.sender_id === user?.id ? "You" : m.sender_name}</strong><small>{new Date(m.created_at).toLocaleString("en-IN", { day:"numeric", month:"short", hour:"2-digit", minute:"2-digit" })}</small></div><p>{m.body}</p></div>)}{!messages.length && <p className="empty-chat-note">Start the conversation.</p>}</div>
    <form className="chat-compose" onSubmit={send}><textarea value={draft} onChange={e => setDraft(e.target.value)} maxLength={2000} rows={2} placeholder="Write a message…"/><Button type="submit" disabled={sending || !draft.trim()}>{sending ? "Sending…" : "Send"}<Send size={16}/></Button></form>
    <p className="chat-poll-note"><RefreshCw size={12}/> Messages refresh automatically every 3 seconds.</p>
  </Modal>;
}

function WantedBoard({ user, notify, onNeedLogin }) {
  const [requests, setRequests] = useState([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [showForm, setShowForm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [responsesFor, setResponsesFor] = useState(null);
  const [responses, setResponses] = useState([]);
  const [chatInterest, setChatInterest] = useState(null);
  const [form, setForm] = useState({ title:"", description:"", category:"Study essentials", needed_from:new Date(Date.now()+86400000).toLocaleDateString("en-CA"), needed_until:new Date(Date.now()+7*86400000).toLocaleDateString("en-CA"), location:"Campus" });
  const load = useCallback(async () => {
    try { const params = new URLSearchParams(); if (search.trim()) params.set("search", search.trim()); if (category !== "All") params.set("category", category); setRequests(await api(`/api/wanted-requests?${params.toString()}`)); }
    catch (err) { notify(err.message, "error"); }
  }, [search, category, notify]);
  useEffect(() => { load(); }, [load]);
  const submit = async e => {
    e.preventDefault(); if (!user) { onNeedLogin(); return; } setBusy(true);
    try { await api("/api/wanted-requests", { method:"POST", body:JSON.stringify(form) }); notify("Your wanted request is now visible to the community.", "success"); setForm({ title:"", description:"", category:"Study essentials", needed_from:new Date(Date.now()+86400000).toLocaleDateString("en-CA"), needed_until:new Date(Date.now()+7*86400000).toLocaleDateString("en-CA"), location:"Campus" }); setShowForm(false); await load(); }
    catch (err) { notify(err.message, "error"); } finally { setBusy(false); }
  };
  const offer = async wanted => {
    if (!user) { onNeedLogin(); return; }
    if (wanted.requester_id === user.id) { try { setResponses(await api(`/api/wanted-requests/${wanted.id}/interests`)); setResponsesFor(wanted); } catch (err) { notify(err.message, "error"); } return; }
    try {
      const mine = await api(`/api/wanted-requests/${wanted.id}/my-interest`);
      if (mine) { setChatInterest(mine); return; }
      const message = window.prompt(`Tell ${wanted.requester_name} how you can help with “${wanted.title}”:`, "Hi! I may be able to lend this item. Let's discuss the dates and handover.");
      if (!message || !message.trim()) return;
      const interest = await api(`/api/wanted-requests/${wanted.id}/interests`, { method:"POST", body:JSON.stringify({ message:message.trim() }) });
      setChatInterest(interest); notify("Your offer was sent. You can now chat with the requester.", "success");
    } catch (err) { notify(err.message, "error"); }
  };
  const openResponses = async wanted => { try { setResponses(await api(`/api/wanted-requests/${wanted.id}/interests`)); setResponsesFor(wanted); } catch (err) { notify(err.message, "error"); } };
  return <div className="wanted-page page-container">
    <div className="page-intro"><div><div className="eyebrow">COMMUNITY WANTED BOARD</div><h1>Ask for what you need.</h1><p>Can't find an item on the shelf? Post a request and let people who have it reach out to you.</p></div><Button onClick={() => user ? setShowForm(v => !v) : onNeedLogin()}><Plus size={17}/>{showForm ? "Close form" : "Post a request"}</Button></div>
    {showForm && <section className="wanted-form-panel"><div className="wanted-panel-heading"><HandHeart size={21}/><div><h2>What are you looking to borrow?</h2><p>Only share the details a potential lender needs to help.</p></div></div><form className="form-stack" onSubmit={submit}><label>Item name<input required minLength="2" maxLength="140" value={form.title} onChange={e=>setForm({...form,title:e.target.value})} placeholder="e.g. DSLR camera, lab coat, bicycle"/></label><label>Description<textarea rows="3" maxLength="2000" value={form.description} onChange={e=>setForm({...form,description:e.target.value})} placeholder="Mention specifications or any important details."/></label><div className="form-grid"><label>Category<select value={form.category} onChange={e=>setForm({...form,category:e.target.value})}>{categories.filter(c=>c!=="All").map(c=><option key={c}>{c}</option>)}</select></label><label>Pickup area<input maxLength="140" value={form.location} onChange={e=>setForm({...form,location:e.target.value})}/></label></div><div className="form-grid"><label>Needed from<input type="date" required min={new Date().toLocaleDateString("en-CA")} value={form.needed_from} onChange={e=>setForm({...form,needed_from:e.target.value,needed_until:form.needed_until<form.needed_from?e.target.value:form.needed_until})}/></label><label>Needed until<input type="date" required min={form.needed_from} value={form.needed_until} onChange={e=>setForm({...form,needed_until:e.target.value})}/></label></div><Button type="submit" disabled={busy}>{busy?"Posting…":"Publish wanted request"}<ArrowRight size={16}/></Button></form></section>}
    <div className="browse-toolbar"><div className="browse-search"><Search size={18}/><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search wanted items…"/>{search&&<button onClick={()=>setSearch("")}><X size={15}/></button>}</div><div className="filter-wrap"><Filter size={16}/><select value={category} onChange={e=>setCategory(e.target.value)}>{categories.map(c=><option key={c}>{c}</option>)}</select></div></div>
    <div className="results-line"><span><strong>{requests.length}</strong> open {requests.length===1?"request":"requests"}</span><span>Help someone find what they need <HeartHandshake size={15}/></span></div>
    {requests.length ? <div className="wanted-grid">{requests.map(w=><article className="wanted-card" key={w.id}><div className="wanted-card-top"><span className="item-category">{w.category}</span><span className="wanted-open-pill"><span/> Open request</span></div><h2>{w.title}</h2><p>{w.description||"The requester has not added extra details."}</p><div className="wanted-meta"><span><UserRound size={14}/>{w.requester_name}</span><span><MapPin size={14}/>{w.location}</span></div><div className="wanted-date"><CalendarDays size={15}/>{fmtDate(w.needed_from)} – {fmtDate(w.needed_until)}</div><div className="wanted-card-footer"><span><HeartHandshake size={15}/> Community request</span>{user?.id===w.requester_id?<Button variant="dark" size="sm" onClick={()=>openResponses(w)}><MessageSquare size={15}/> View responses</Button>:<Button variant="dark" size="sm" onClick={()=>offer(w)}><Send size={15}/>{user?"I can help":"Offer to lend"}</Button>}</div></article>)}</div> : <EmptyState icon={CircleHelp} title="No open requests found" text="Try another search or post the item you need so potential lenders can find you."/>}
    {responsesFor && <Modal title={`Responses to “${responsesFor.title}”`} subtitle="Choose a potential lender to start or continue a private conversation." onClose={()=>setResponsesFor(null)}>{responses.length?<div className="wanted-responses">{responses.map(r=><button className="wanted-response-row" key={r.id} onClick={()=>{setResponsesFor(null);setChatInterest(r);}}><span className="avatar">{initials(r.lender_name)}</span><span><strong>{r.lender_name}</strong><small>{r.last_message||"Interested in helping"}</small></span><MessageSquare size={17}/></button>)}</div>:<EmptyState icon={MessageSquare} title="No responses yet" text="When a lender offers to help, their message will appear here."/>}</Modal>}
    {chatInterest && <WantedChatModal interest={chatInterest} user={user} onClose={()=>setChatInterest(null)} notify={notify}/>}
  </div>;
}

function Dashboard({ user, refreshKey, notify, onEdit, onDelete, onReport, onUserUpdate }) {
  const [mine, setMine] = useState([]);
  const [sent, setSent] = useState([]);
  const [received, setReceived] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [availabilityBusy, setAvailabilityBusy] = useState(false);
  const [tab, setTab] = useState("sent");
  const [reportsFor, setReportsFor] = useState(null);
  const [reports, setReports] = useState([]);
  const [busyId, setBusyId] = useState(null);
  const [chatFor, setChatFor] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [conversations, setConversations] = useState([]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [a, b, c, d, n, chats] = await Promise.all([
        api("/api/items/mine"), api("/api/borrowings/mine"), api("/api/borrowings/received"), api("/api/reminders"),
        api("/api/notifications"), api("/api/messages/conversations")
      ]);
      setMine(a); setSent(b); setReceived(c); setReminders(d); setNotifications(n); setConversations(chats);
    } catch (err) { notify(err.message, "error"); }
    finally { setLoading(false); }
  }, [notify, refreshKey]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    const timer = window.setInterval(async () => {
      try {
        const [n, chats] = await Promise.all([api("/api/notifications"), api("/api/messages/conversations")]);
        setNotifications(n); setConversations(chats);
      } catch { /* Keep the dashboard usable if a background refresh briefly fails. */ }
    }, 5000);
    return () => window.clearInterval(timer);
  }, []);

  const act = async (b, action, success) => {
    setBusyId(`${b.id}-${action}`);
    if (action === "cancel" && !window.confirm(`Cancel your borrowing request for "${b.item_title}"? This cannot be undone.`)) return;
    try { await api(`/api/borrowings/${b.id}/${action}`, { method: "PATCH" }); notify(success, "success"); await load(); }
    catch (err) { notify(err.message, "error"); }
    finally { setBusyId(null); }
  };
  const viewReports = async b => {
    try { const data = await api(`/api/borrowings/${b.id}/condition-reports`); setReports(data); setReportsFor(b); }
    catch (err) { notify(err.message, "error"); }
  };
  const allTransactions = [...sent.map(b => ({ ...b, transaction_role: "borrower" })), ...received.map(b => ({ ...b, transaction_role: "lender" }))]
    .filter((b, i, arr) => arr.findIndex(x => x.id === b.id) === i)
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  const shown = tab === "sent" ? sent : tab === "received" ? received : tab === "history" ? allTransactions : [];
  const changeAvailability = async value => {
    setAvailabilityBusy(true);
    try { const updated = await api("/api/auth/availability", { method: "PATCH", body: JSON.stringify({ availability_status: value }) }); onUserUpdate(updated); notify(value === "available" ? "Your profile now shows that you're available to lend." : "Your profile now shows that you're not lending right now.", "success"); }
    catch (err) { notify(err.message, "error"); }
    finally { setAvailabilityBusy(false); }
  };
  const stats = [
    { label: "Your listings", value: mine.filter(x => x.is_active).length, icon: Package },
    { label: "Requests sent", value: sent.length, icon: Send },
    { label: "Requests to you", value: received.filter(x => x.status === "pending").length, icon: Bell },
    { label: "Completed shares", value: [...sent, ...received].filter(x => x.status === "completed").length, icon: CheckCircle2 }
  ];
  return <div className="dashboard-page">
    <div className="dashboard-welcome"><div><div className="eyebrow"><Sparkles size={15}/> YOUR SHARING SPACE</div><h1>Good to see you, {user.name.split(" ")[0]}.</h1><p>Everything you share and borrow, all in one place.</p><div className="profile-availability"><span className={`availability-dot ${user.availability_status === "not_lending" ? "away" : ""}`}/><span>You are <strong>{user.availability_status === "not_lending" ? "not lending right now" : "available to lend"}</strong></span><select aria-label="Your lending availability" disabled={availabilityBusy} value={user.availability_status || "available"} onChange={e => changeAvailability(e.target.value)}><option value="available">Available to lend</option><option value="not_lending">Not lending right now</option></select></div></div><div className="avatar-large">{initials(user.name)}</div></div>
    <section className="reminders-panel"><div className="reminders-heading"><div className="reminder-bell"><AlarmClock size={20}/></div><div><h2>Return reminders</h2><p>Upcoming due dates, overdue items, and returns waiting for your confirmation.</p></div><span className="reminder-count">{reminders.length}</span></div>{reminders.length ? <div className="reminders-grid">{reminders.map(r => <article key={r.id} className={`reminder-card reminder-${r.type}`}><div className="reminder-card-icon">{r.type === "overdue" ? <AlertCircle size={18}/> : r.type === "confirm_return" ? <Package size={18}/> : <CalendarDays size={18}/>}</div><div className="reminder-card-content"><strong>{r.item_title}</strong><p>{r.message}</p><small>{r.type === "confirm_return" ? "Action needed · Confirm receipt" : `Return date: ${fmtDate(r.due_date)}`}</small></div>{r.type === "confirm_return" && <Button size="sm" onClick={() => { setTab("received"); document.querySelector(".dashboard-panel")?.scrollIntoView({ behavior: "smooth", block: "start" }); }}>Review</Button>}</article>)}</div> : <div className="reminders-empty"><CheckCircle2 size={17}/><span>You're all caught up. Return reminders will appear here when a borrowed item is due within 3 days or a return needs confirmation.</span></div>}</section>
    <div className="stats-grid">{stats.map(s => <div className="stat-card" key={s.label}><div className="stat-icon"><s.icon size={19}/></div><div><strong>{s.value}</strong><span>{s.label}</span></div></div>)}</div>
    <div className="dashboard-panel">
      <div className="panel-head"><div><h2>Your activity</h2><p>Manage requests and keep your items moving.</p></div><Button variant="outline" onClick={load}><RefreshCw size={15}/> Refresh</Button></div>
      <div className="tabs">
        <button className={tab === "sent" ? "active" : ""} onClick={() => setTab("sent")}>My borrowings <span>{sent.length}</span></button>
        <button className={tab === "received" ? "active" : ""} onClick={() => setTab("received")}>Requests to me <span>{received.length}</span></button>
        <button className={tab === "items" ? "active" : ""} onClick={() => setTab("items")}>My listings <span>{mine.length}</span></button>
      <button className={tab === "history" ? "active" : ""} onClick={() => setTab("history")}>Transaction history <span>{allTransactions.length}</span></button>
      <button className={tab === "messages" ? "active" : ""} onClick={() => setTab("messages")}>Messages <span>{conversations.reduce((n, c) => n + c.unread_count, 0)}</span></button>
      <button className={tab === "notifications" ? "active" : ""} onClick={() => setTab("notifications")}>Notifications <span>{notifications.filter(n => !n.read_at).length}</span></button>
      </div>
      {loading ? <div className="loading-state"><div className="spinner"/>Loading your dashboard…</div> :
        tab === "messages" ? <div className="conversation-list">{conversations.length ? conversations.map(c => <button className="conversation-row" key={c.borrowing_id} onClick={() => { const b = [...sent, ...received].find(x => x.id === c.borrowing_id); if (b) setChatFor(b); }}><span className="conversation-avatar"><MessageSquareIcon /></span><span className="conversation-main"><strong>{c.item_title}</strong><small>Chat with {c.other_user_name} · {c.status.replaceAll("_", " ")}</small><span>{c.last_message}</span></span><span className="conversation-trailing">{c.unread_count > 0 && <b>{c.unread_count}</b>}<small>{new Date(c.last_message_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}</small></span></button>) : <EmptyState icon={Send} title="No conversations yet" text="Open a borrowing request and use Chat to coordinate pickup and returns."/>}</div> :
        tab === "notifications" ? <div className="notification-list">{notifications.filter(n => !n.read_at).length > 0 && <div className="notification-list-head"><span>Unread activity</span><Button variant="outline" size="sm" onClick={async () => { try { await api("/api/notifications/read-all", { method: "PATCH" }); await load(); } catch (e) { notify(e.message, "error"); } }}>Mark all read</Button></div>}{notifications.length ? notifications.map(n => <article className={`notification-row ${n.read_at ? "notification-read" : ""}`} key={n.id}><span className="notification-icon"><Bell size={17}/></span><div><strong>{n.title}</strong><p>{n.body}</p><small>{new Date(n.created_at).toLocaleString("en-IN")}</small></div>{!n.read_at && <Button size="sm" variant="outline" onClick={async () => { try { await api(`/api/notifications/${n.id}/read`, { method: "PATCH" }); await load(); } catch (e) { notify(e.message, "error"); } }}>Mark read</Button>}</article>) : <EmptyState icon={Bell} title="You're all caught up" text="Borrowing updates and new messages will appear here."/>}</div> :
        tab === "items" ? <div className="listing-manage">{mine.length ? mine.map(item => <div className="manage-row" key={item.id}><ItemImage item={item} className="manage-thumb"/><div className="manage-main"><strong>{item.title}</strong><span>{item.category} · {item.location}</span></div><span className={`availability-pill availability-${item.availability_status || (item.is_active ? "available" : "inactive")}`}>{({available:"Available",reserved:"Reserved today",borrowed:"Borrowed",inactive:"Inactive",owner_unavailable:"Lending paused"})[item.availability_status || (item.is_active ? "available" : "inactive")]}</span><button className="icon-btn" title="Edit listing" aria-label={`Edit ${item.title}`} onClick={() => onEdit(item)}><Pencil size={16}/></button>{item.is_active && <button className="icon-btn danger-action" title="Cancel listing" aria-label={`Cancel listing ${item.title}`} onClick={() => onDelete(item)}><Trash2 size={16}/></button>}</div>) : <EmptyState icon={Package} title="No listings yet" text="Share your first item and help someone nearby."/>} </div> :
        shown.length ? <div className="borrowing-list">{shown.map(b => {
          const incoming = tab === "received" ? true : tab === "history" ? b.transaction_role === "lender" : false;
          return <div className="borrowing-row" key={`${tab}-${b.id}`}>
            <ItemImage item={{ title: b.item_title, category: "Other", condition: "Shared", image_url: b.item_image_url }} className="borrowing-thumb"/>
            <div className="borrowing-main"><div className="borrowing-title-line"><strong>{b.item_title}</strong><StatusBadge status={b.status}/></div><span>{tab === "history" ? (incoming ? `You lent to ${b.borrower_name}` : `You borrowed from ${b.item_owner_name}`) : incoming ? `Requested by ${b.borrower_name}` : `Owner: ${b.item_owner_name}`}</span><small><CalendarDays size={13}/>{fmtDate(b.start_date)} – {fmtDate(b.due_date)}{tab === "history" ? ` · Requested ${new Date(b.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}` : ""}</small>{b.message && <p className="borrow-message">“{b.message}”</p>}</div>
            <div className="row-actions">
              {tab !== "history" && incoming && b.status === "pending" && <><Button size="sm" onClick={() => act(b, "approve", "Request approved.")} disabled={!!busyId}>{busyId === `${b.id}-approve` ? "…" : <><Check size={14}/> Approve</>}</Button><Button variant="outline" size="sm" onClick={() => act(b, "reject", "Request declined.")} disabled={!!busyId}>Decline</Button></>}
              {tab !== "history" && !incoming && ["pending", "approved"].includes(b.status) && <Button variant="outline" size="sm" onClick={() => act(b, "cancel", "Request cancelled.")} disabled={!!busyId}>Cancel</Button>}
              {tab !== "history" && !incoming && b.status === "approved" && <Button size="sm" onClick={() => act(b, "pickup", "Pickup confirmed. Have a great borrow!")}>Confirm pickup</Button>}
              {tab !== "history" && !incoming && b.status === "active" && <Button size="sm" onClick={() => act(b, "return", "Return marked. Ask the owner to confirm receipt.")}>Mark returned</Button>}
              {tab !== "history" && incoming && b.status === "return_pending" && <Button size="sm" onClick={() => act(b, "confirm-return", "Return confirmed. Thanks for sharing!")}>Confirm return</Button>}
              {! ["rejected", "cancelled"].includes(b.status) && <Button variant="outline" size="sm" onClick={() => setChatFor(b)}><MessageSquareIcon /> Chat</Button>}
              {["approved", "active", "return_pending", "completed"].includes(b.status) && <Button variant="outline" size="sm" onClick={() => onReport(b)}><ClipboardCheck size={14}/> Condition</Button>}
              <button className="text-action" onClick={() => viewReports(b)} title="View condition reports"><Eye size={15}/> Reports</button>
            </div>
          </div>;
        })}</div> : <EmptyState icon={tab === "sent" ? HandHeart : tab === "history" ? History : Bell} title={tab === "sent" ? "Your next borrow starts here" : tab === "history" ? "Your story starts here" : "No requests just yet"} text={tab === "sent" ? "Browse the community and request something useful." : tab === "history" ? "Completed and ongoing transactions will appear here." : "When someone requests your item, it will appear here."}/>}
    </div>
    {chatFor && <ChatModal borrowing={chatFor} onClose={() => { setChatFor(null); load(); }} notify={notify} user={user}/>}
    {reportsFor && <Modal title="Condition history" subtitle={reportsFor.item_title} onClose={() => setReportsFor(null)}><div className="reports-list">{reports.length ? reports.map(r => <div className="report-card" key={r.id}><div className="report-top"><span className="soft-tag">{r.report_type === "pickup" ? "At pickup" : "At return"}</span><small>{new Date(r.created_at).toLocaleString()}</small></div><p>{r.notes || "No notes added."}</p>{r.photo_url && <a href={r.photo_url} target="_blank" rel="noreferrer">View condition photo <ArrowUpRight size={14}/></a>}</div>) : <EmptyState icon={ClipboardCheck} title="No reports yet" text="Condition reports will appear here once added."/>}</div></Modal>}
  </div>;
}

function EmptyState({ icon: Icon = Package, title, text }) {
  return <div className="empty-state"><div className="empty-icon"><Icon size={25}/></div><h3>{title}</h3><p>{text}</p></div>;
}

function Toast({ toast, onClose }) {
  if (!toast) return null;
  return <div className={`toast toast-${toast.type}`}><span className="toast-icon">{toast.type === "success" ? <CheckCircle2 size={19}/> : <AlertCircle size={19}/>}</span><span>{toast.message}</span><button onClick={onClose}><X size={16}/></button></div>;
}

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const routePage = location.pathname === "/browse" ? "browse" : location.pathname === "/dashboard" ? "dashboard" : location.pathname === "/login" ? "login" : location.pathname === "/register" ? "register" : location.pathname === "/wanted" ? "wanted" : "home";
  const [user, setUser] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [page, setPage] = useState(routePage);
  const [authMode, setAuthMode] = useState(null);
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [selectedItem, setSelectedItem] = useState(null);
  const [editingItem, setEditingItem] = useState(null);
  const [reportBorrowing, setReportBorrowing] = useState(null);
  const [showItemForm, setShowItemForm] = useState(false);
  const [mobileMenu, setMobileMenu] = useState(false);
  const [toast, setToast] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [loadingItems, setLoadingItems] = useState(true);

  const notify = useCallback((message, type = "success") => {
    setToast({ message, type });
    window.clearTimeout(window.__borrowboxToast);
    window.__borrowboxToast = window.setTimeout(() => setToast(null), 4300);
  }, []);

  const loadItems = useCallback(async () => {
    setLoadingItems(true);
    try {
      const params = new URLSearchParams();
      if (search.trim()) params.set("search", search.trim());
      if (category !== "All") params.set("category", category);
      const data = await api(`/api/items?${params.toString()}`);
      setItems(data);
    } catch (err) { notify(err.message, "error"); }
    finally { setLoadingItems(false); }
  }, [search, category, notify]);

  useEffect(() => { loadItems(); }, [loadItems, refreshKey]);
  useEffect(() => {
    const token = localStorage.getItem("borrowbox_token");
    if (!token) { setAuthChecked(true); return; }
    api("/api/auth/me").then(setUser).catch(() => localStorage.removeItem("borrowbox_token")).finally(() => setAuthChecked(true));
  }, []);

  const refresh = useCallback(() => setRefreshKey(x => x + 1), []);
  useEffect(() => { setPage(routePage); }, [routePage]);
  const go = p => { setPage(p); navigate(({ browse: "/browse", dashboard: "/dashboard", login: "/login", register: "/register", wanted: "/wanted" })[p] || "/"); setMobileMenu(false); window.scrollTo({ top: 0, behavior: "smooth" }); };
  const logout = () => { localStorage.removeItem("borrowbox_token"); setUser(null); go("home"); notify("You have signed out.", "success"); };
  const openListing = item => setSelectedItem(item);
  const editListing = item => { setEditingItem(item); setShowItemForm(true); };
  const deactivateListing = async item => {
    if (!window.confirm(`Cancel the listing "${item.title}"? It will disappear from Browse. Any pending requests will be cancelled and those borrowers notified. Listings with approved or active borrowings cannot be cancelled.`)) return;
    try { const result = await api(`/api/items/${item.id}`, { method: "DELETE" }); notify(result.message || "Listing cancelled.", "success"); refresh(); }
    catch (err) { notify(err.message, "error"); }
  };
  const afterBorrow = () => { refresh(); notify("Request sent! You can track it in your dashboard.", "success"); };

  const visibleItems = items;
  const homeItems = useMemo(() => visibleItems.slice(0, 4), [visibleItems]);
  const onAuthSuccess = u => { setUser(u); setPage("dashboard"); navigate("/dashboard"); refresh(); };

  if (!authChecked) return <div className="app-loading"><div className="brand-mark"><Package size={22}/></div><div className="spinner"/><p>Getting your sharing space ready…</p></div>;

  return <div className="app-shell">
    <header className="site-header">
      <div className="header-inner">
        <Brand onClick={() => go("home")}/>
        <nav className={`main-nav ${mobileMenu ? "nav-open" : ""}`}>
          <button className={page === "home" ? "nav-link active" : "nav-link"} onClick={() => go("home")}>Home</button>
          <button className={page === "browse" ? "nav-link active" : "nav-link"} onClick={() => go("browse")}>Explore items</button>
          <button className={page === "wanted" ? "nav-link active" : "nav-link"} onClick={() => go("wanted")}>Wanted board</button>
          {user && <button className={page === "dashboard" ? "nav-link active" : "nav-link"} onClick={() => go("dashboard")}>My dashboard</button>}
        </nav>
        <div className="header-actions">
          {user ? <>
            <Button variant="outline" size="sm" className="list-header-btn" onClick={() => { setEditingItem(null); setShowItemForm(true); }}><Plus size={16}/> List an item</Button>
            <button className="user-chip" onClick={() => go("dashboard")}><span className="avatar">{initials(user.name)}</span><span className="user-chip-name">{user.name.split(" ")[0]}</span><ChevronDown size={15}/></button>
            <button className="icon-btn logout-btn" title="Sign out" onClick={logout}><LogOut size={18}/></button>
          </> : <>
            <button className="login-link" onClick={() => go("login")}>Sign in</button>
            <Button size="sm" onClick={() => go("register")}>Join BorrowBox <ArrowRight size={15}/></Button>
          </>}
          <button className="icon-btn mobile-menu-btn" onClick={() => setMobileMenu(!mobileMenu)}><Menu size={20}/></button>
        </div>
      </div>
    </header>

    <main>
      {page === "home" && <div className="home-page">
        <section className="hero">
          <div className="hero-copy">
            <div className="eyebrow"><span className="eyebrow-dot"/> A LITTLE SHARING GOES A LONG WAY</div>
            <h1>Good things are<br/>better <span>shared.</span></h1>
            <p className="hero-subtitle">Borrow what you need. Lend what you don't. Make your community a little more resourceful.</p>
            <form className="hero-search" onSubmit={e => { e.preventDefault(); go("browse"); }}>
              <Search size={19}/><input value={search} onChange={e => setSearch(e.target.value)} placeholder="What are you looking for?"/>
              <Button type="submit">Find an item <ArrowRight size={16}/></Button>
            </form>
            <div className="hero-proof"><div className="avatar-stack"><span>R</span><span>A</span><span>M</span><span>+</span></div><span>Small shares. <strong>Big difference.</strong></span><span className="proof-dot">•</span><span>Always free to borrow</span></div>
          </div>
          <div className="hero-art">
            <div className="hero-orbit orbit-one"/><div className="hero-orbit orbit-two"/>
            <div className="hero-main-card"><div className="hero-card-top"><span className="hero-card-label"><Sparkles size={14}/> THE SHARING CIRCLE</span><span className="live-dot">● LIVE</span></div><div className="hero-item-collage"><div className="collage-card collage-book"><img src={demoImages.Books} alt="Books"/><span>Books & notes</span></div><div className="collage-card collage-tech"><img src={demoImages.Electronics} alt="Laptop"/><span>Tech essentials</span></div><div className="collage-card collage-tools"><img src={demoImages.Tools} alt="Tools"/><span>Tools & more</span></div></div><div className="hero-card-footer"><div className="hero-footer-icon"><HeartHandshake size={20}/></div><div><strong>Borrow. Return. Repeat.</strong><span>Less waste, more possibility.</span></div><ArrowUpRight size={20}/></div></div>
            <div className="floating-note note-top"><span className="note-icon green"><Leaf size={17}/></span><div><strong>Use more. Own less.</strong><small>Sharing is a good habit.</small></div></div>
            <div className="floating-note note-bottom"><span className="note-icon yellow"><ShieldCheck size={17}/></span><div><strong>Borrow with confidence</strong><small>Clear requests & returns</small></div></div>
            <div className="hero-sparkle sparkle-a">✳</div><div className="hero-sparkle sparkle-b">✦</div>
          </div>
        </section>

        <section className="value-strip">
          <div><span className="value-icon"><HandHeart size={20}/></span><div><strong>Community first</strong><small>People helping people</small></div></div>
          <div><span className="value-icon"><ShieldCheck size={20}/></span><div><strong>Clear & accountable</strong><small>Track every borrow</small></div></div>
          <div><span className="value-icon"><Leaf size={20}/></span><div><strong>Less waste</strong><small>Give items more life</small></div></div>
        </section>

        <section className="section-block">
          <div className="section-heading"><div><div className="eyebrow">FIND YOUR NEXT BORROW</div><h2>Useful things, shared locally.</h2><p>Discover something you need from someone in your community.</p></div><button className="arrow-link" onClick={() => go("browse")}>Explore everything <ArrowRight size={17}/></button></div>
          <div className="category-row">{categories.filter(c => c !== "All").map((c, i) => <button key={c} className={`category-chip ${category === c ? "selected" : ""}`} onClick={() => { setCategory(c); go("browse"); }}><span>{["▤","⌘","✎","⚒","◉","✳","＋"][i]}</span>{c}</button>)}</div>
          {loadingItems ? <div className="loading-state"><div className="spinner"/>Finding useful things…</div> : homeItems.length ? <div className="items-grid">{homeItems.map(item => <ItemCard key={item.id} item={item} currentUser={user} onOpen={openListing} onEdit={editListing} onDelete={deactivateListing}/>)}</div> : <EmptyState icon={Package} title="The shelf is waiting" text="Be the first to share something useful with your community."/>}
        </section>

        <section className="how-section">
          <div className="section-heading centered"><div><div className="eyebrow">SIMPLE BY DESIGN</div><h2>Sharing, made easy.</h2><p>Three small steps. A more resourceful community.</p></div></div>
          <div className="steps-grid"><div className="step-card"><span className="step-number">01</span><div className="step-icon"><Search size={23}/></div><h3>Find what you need</h3><p>Browse useful items shared by people around you. No endless group chats.</p></div><div className="step-connector">→</div><div className="step-card"><span className="step-number">02</span><div className="step-icon"><CalendarDays size={23}/></div><h3>Request your dates</h3><p>Send a request, agree on a time, and keep the details in one place.</p></div><div className="step-connector">→</div><div className="step-card"><span className="step-number">03</span><div className="step-icon"><HeartHandshake size={23}/></div><h3>Borrow & return</h3><p>Keep track of pickup and return, then pass the good thing along.</p></div></div>
        </section>

        <section className="cta-banner"><div className="cta-decoration">✳</div><div><div className="eyebrow">YOUR SHELF HAS POTENTIAL</div><h2>Have something sitting unused?</h2><p>Someone nearby might need it today. Give it another story.</p></div><Button variant="light" onClick={() => user ? (setEditingItem(null), setShowItemForm(true)) : setAuthMode("register")}>Share an item <ArrowRight size={17}/></Button></section>
      </div>}

      {page === "browse" && <div className="browse-page page-container">
        <div className="page-intro"><div><div className="eyebrow">THE COMMUNITY SHELF</div><h1>Find something useful.</h1><p>Good things are already out there. Let's help them find their next use.</p></div><Button onClick={() => user ? (setEditingItem(null), setShowItemForm(true)) : setAuthMode("register")}><Plus size={17}/> List an item</Button></div>
        <div className="browse-toolbar"><div className="browse-search"><Search size={18}/><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search items, categories, or descriptions…"/>{search && <button onClick={() => setSearch("")}><X size={15}/></button>}</div><div className="filter-wrap"><Filter size={16}/><select value={category} onChange={e => setCategory(e.target.value)}>{categories.map(c => <option key={c}>{c}</option>)}</select></div></div>
        <div className="results-line"><span><strong>{items.length}</strong> {items.length === 1 ? "item" : "items"} to discover</span><span>Free to borrow <HeartHandshake size={15}/></span></div>
        {loadingItems ? <div className="loading-state"><div className="spinner"/>Loading community items…</div> : visibleItems.length ? <div className="items-grid">{visibleItems.map(item => <ItemCard key={item.id} item={item} currentUser={user} onOpen={openListing} onEdit={editListing} onDelete={deactivateListing}/>)}</div> : <EmptyState icon={Search} title="No matches just yet" text="Try another search or category, or be the first to list what you have."/>}
      </div>}

      {page === "wanted" && <WantedBoard user={user} notify={notify} onNeedLogin={() => go("login")}/> }
      {page === "dashboard" && (user ? <div className="page-container"><Dashboard user={user} refreshKey={refreshKey} notify={notify} onEdit={editListing} onDelete={deactivateListing} onReport={b => setReportBorrowing(b)} onUserUpdate={setUser}/></div> : <div className="page-container"><EmptyState icon={LogIn} title="Sign in to see your dashboard" text="Your listings and borrowing requests will be waiting for you."/><div className="center-actions"><Button onClick={() => go("login")}>Sign in</Button></div></div>)}
      {(page === "login" || page === "register") && !user && <AuthPage mode={page} onSuccess={onAuthSuccess} notify={notify} onNavigateHome={() => go("home")}/>}
      {(page === "login" || page === "register") && user && <div className="page-container"><EmptyState icon={CheckCircle2} title="You're already signed in" text="Head to your dashboard to manage your items and transactions."/><div className="center-actions"><Button onClick={() => go("dashboard")}>Open dashboard</Button></div></div>}
    </main>

    <footer className="site-footer"><div className="footer-main"><Brand onClick={() => go("home")}/><p>A little less buying. A little more sharing.<br/>Built for communities that look out for each other.</p><div className="footer-social"><span><Leaf size={16}/> Thoughtful sharing</span><span><ShieldCheck size={16}/> Responsible borrowing</span></div></div><div className="footer-links"><div><strong>Discover</strong><button onClick={() => go("browse")}>Explore items</button><button onClick={() => go("wanted")}>Wanted board</button><button onClick={() => user ? (setEditingItem(null), setShowItemForm(true)) : setAuthMode("register")}>List an item</button></div><div><strong>Your space</strong><button onClick={() => user ? go("dashboard") : setAuthMode("login")}>Dashboard</button><button onClick={() => setAuthMode("register")}>Join BorrowBox</button></div></div><div className="footer-bottom"><span>© {new Date().getFullYear()} BorrowBox. Share more. Buy less.</span><span>Made for a more resourceful community <HeartHandshake size={15}/></span></div></footer>

    {authMode && <AuthModal mode={authMode} setMode={setAuthMode} onClose={() => setAuthMode(null)} onSuccess={onAuthSuccess} notify={notify}/>}
    {showItemForm && user && <ItemForm item={editingItem} onClose={() => { setShowItemForm(false); setEditingItem(null); }} onSaved={refresh} notify={notify}/>}
    {selectedItem && <ItemDetail item={selectedItem} currentUser={user} onClose={() => setSelectedItem(null)} onBorrow={afterBorrow}/>}
    {reportBorrowing && <ReportModal borrowing={reportBorrowing} onClose={() => setReportBorrowing(null)} onSaved={refresh} notify={notify}/>}
    <Toast toast={toast} onClose={() => setToast(null)}/>
  </div>;
}
