"""Accounts, login, people and connections. Whatever real users enter goes to MySQL first; the graph is refreshed from it."""
from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

import seed_neo4j
from db import sql

bp = Blueprint("auth", __name__)


def user():
    uid = session.get("uid")
    rows = sql("SELECT user_id, name, headline, is_admin FROM users WHERE user_id=%s", (uid,)) if uid else []
    return rows[0] if rows else None


def login_required(f):
    @wraps(f)
    def w(*a, **k):
        return f(*a, **k) if user() else redirect("/login")
    return w


def admin_required(f):
    @wraps(f)
    def w(*a, **k):
        u = user()
        if not u:
            return redirect("/login")
        if not u["is_admin"]:
            abort(403)
        return f(*a, **k)
    return w


def refresh_graph():
    try:
        seed_neo4j.sync()
    except Exception:
        pass  # MySQL already has the data; admins can use "Rebuild graph" on the Reports page


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        f = request.form
        name, email, pw = f["name"].strip(), f["email"].strip().lower(), f["password"]
        if len(pw) < 8 or "@" not in email or not name:
            flash("Enter your name, a valid email and a password of at least 8 characters.")
        elif sql("SELECT 1 AS x FROM users WHERE email=%s", (email,)):
            flash("That email is already registered. Try logging in.")
        else:
            sql("INSERT INTO users(name, email, headline, location, password_hash) VALUES (%s,%s,%s,%s,%s)",
                (name, email, f["headline"].strip(), f["location"].strip(), generate_password_hash(pw)))
            uid = sql("SELECT user_id FROM users WHERE email=%s", (email,))[0]["user_id"]
            if f["school"].strip():
                yr = int(f["grad_year"]) if f["grad_year"].strip().isdigit() else None
                sql("INSERT INTO education(user_id, school, degree, grad_year) VALUES (%s,%s,%s,%s)",
                    (uid, f["school"].strip(), f["degree"].strip(), yr))
            for sid in request.form.getlist("skills"):
                sql("INSERT IGNORE INTO user_skill(user_id, skill_id) VALUES (%s,%s)", (uid, int(sid)))
            refresh_graph()
            session["uid"] = uid
            return redirect("/people")
    return render_template("signup.html", skills=sql("SELECT skill_id, name FROM skill ORDER BY name"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        r = sql("SELECT user_id, password_hash FROM users WHERE email=%s", (request.form["email"].strip().lower(),))
        if r and r[0]["password_hash"] and check_password_hash(r[0]["password_hash"], request.form["password"]):
            session["uid"] = r[0]["user_id"]
            return redirect("/")
        flash("Wrong email or password.")
    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@bp.route("/people")
@login_required
def people_page():
    uid, q = session["uid"], request.args.get("q", "").strip()
    rel = {}
    for c in sql("SELECT requester_id, receiver_id, status FROM connection WHERE requester_id=%s OR receiver_id=%s", (uid, uid)):
        other = c["receiver_id"] if c["requester_id"] == uid else c["requester_id"]
        if c["status"] == "accepted":
            rel[other] = "connected"
        elif c["status"] == "pending":
            rel[other] = "sent" if c["requester_id"] == uid else "incoming"
        else:
            rel[other] = "rejected"
    found = sql("SELECT user_id, name, headline, location FROM users WHERE is_admin=0 AND user_id<>%s "
                "AND (name LIKE %s OR headline LIKE %s) ORDER BY name", (uid, f"%{q}%", f"%{q}%"))
    for p in found:
        p["rel"] = rel.get(p["user_id"], "")
    incoming = sql("SELECT u.user_id, u.name, u.headline FROM connection c JOIN users u ON u.user_id=c.requester_id "
                   "WHERE c.receiver_id=%s AND c.status='pending'", (uid,))
    return render_template("people.html", people=found, incoming=incoming, q=q)


@bp.post("/connect/<int:other>")
@login_required
def connect(other):
    uid = session["uid"]
    if other != uid and not sql("SELECT 1 AS x FROM connection WHERE (requester_id=%s AND receiver_id=%s) "
                                "OR (requester_id=%s AND receiver_id=%s)", (uid, other, other, uid)):
        sql("INSERT INTO connection(requester_id, receiver_id, status) VALUES (%s,%s,'pending')", (uid, other))
    return redirect("/people")


@bp.post("/respond/<int:other>/<action>")
@login_required
def respond(other, action):
    if action not in ("accept", "decline"):
        abort(400)
    sql("UPDATE connection SET status=%s WHERE requester_id=%s AND receiver_id=%s AND status='pending'",
        ("accepted" if action == "accept" else "rejected", other, session["uid"]))
    if action == "accept":
        refresh_graph()
    return redirect("/people")
