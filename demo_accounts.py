"""DEMO ONLY: gives the sample users from seed.sql a login and creates a demo admin.
   Sample users  -> password  demo1234   (e.g. sneha.kulkarni@example.com)
   Admin         -> admin@campusconnect.local / admin1234   (can open Reports)
Do not use these passwords on anything that other people can reach.   Run:  python demo_accounts.py"""
from werkzeug.security import generate_password_hash

from db import ensure_auth_columns, sql

ensure_auth_columns()
sql("UPDATE users SET password_hash=%s WHERE is_admin=0 AND password_hash IS NULL", (generate_password_hash("demo1234"),))
admin_hash = generate_password_hash("admin1234")
if sql("SELECT 1 AS x FROM users WHERE email='admin@campusconnect.local'"):
    sql("UPDATE users SET password_hash=%s, is_admin=1 WHERE email='admin@campusconnect.local'", (admin_hash,))
else:
    sql("INSERT INTO users(name, email, headline, location, password_hash, is_admin) "
        "VALUES ('Admin', 'admin@campusconnect.local', 'Administrator', '', %s, 1)", (admin_hash,))
print("Demo accounts ready. Sample users: demo1234 | Admin: admin@campusconnect.local / admin1234")
