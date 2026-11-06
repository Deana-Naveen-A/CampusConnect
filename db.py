"""Connections to the three stores. Configure with environment variables (defaults work for the README setup)."""
import os
import mysql.connector
import redis
from neo4j import GraphDatabase

R = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", "6379")),
                db=int(os.getenv("REDIS_DB", "1")), decode_responses=True)

NEO = GraphDatabase.driver(os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                           auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "campusconnect")))


def sql(query, params=()):
    con = mysql.connector.connect(host=os.getenv("MYSQL_HOST", "localhost"), user=os.getenv("MYSQL_USER", "root"),
                                  password=os.getenv("MYSQL_PASSWORD", ""), database="mini_linkedin")
    cur = con.cursor(dictionary=True)
    cur.execute(query, params)
    rows = cur.fetchall() if cur.with_rows else []
    con.commit()
    cur.close()
    con.close()
    return rows


def cypher(query, **params):
    with NEO.session() as s:
        return [r.data() for r in s.run(query, **params)]


def ensure_auth_columns():
    """Adds login columns to an existing users table (safe to run any number of times)."""
    have = {r["c"] for r in sql("SELECT COLUMN_NAME AS c FROM information_schema.COLUMNS "
                                "WHERE TABLE_SCHEMA='mini_linkedin' AND TABLE_NAME='users'")}
    if "password_hash" not in have:
        sql("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255) NULL")
    if "is_admin" not in have:
        sql("ALTER TABLE users ADD COLUMN is_admin TINYINT(1) NOT NULL DEFAULT 0")
