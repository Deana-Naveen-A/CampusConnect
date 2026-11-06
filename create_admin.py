"""Creates (or promotes) a developer/stakeholder account that can open the Reports page.   python create_admin.py"""
import getpass

from werkzeug.security import generate_password_hash

from db import ensure_auth_columns, sql

ensure_auth_columns()
name = input("Admin name: ").strip() or "Developer"
email = input("Admin email: ").strip().lower()
pw = getpass.getpass("Admin password (min 8 characters): ")
if len(pw) < 8 or "@" not in email:
    raise SystemExit("Need a valid email and a password of at least 8 characters.")
h = generate_password_hash(pw)
if sql("SELECT 1 AS x FROM users WHERE email=%s", (email,)):
    sql("UPDATE users SET password_hash=%s, is_admin=1 WHERE email=%s", (h, email))
else:
    sql("INSERT INTO users(name, email, headline, location, password_hash, is_admin) VALUES (%s,%s,'Administrator','',%s,1)",
        (name, email, h))
print("Admin account ready:", email)
