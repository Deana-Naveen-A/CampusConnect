"""Rebuild every Redis structure from MySQL (MySQL is the source of truth).
Run after loading seed data, or any time Redis is wiped:  python rebuild_redis.py
"""
import os
import pymysql
import redis

db = pymysql.connect(
    host=os.getenv("MYSQL_HOST", "127.0.0.1"), port=int(os.getenv("MYSQL_PORT", "3306")),
    user=os.getenv("MYSQL_USER", "root"), password=os.getenv("MYSQL_PASSWORD", "root"),
    database=os.getenv("MYSQL_DB", "campusconnect"), cursorclass=pymysql.cursors.DictCursor)
R = redis.Redis(host=os.getenv("REDIS_HOST", "127.0.0.1"),
                port=int(os.getenv("REDIS_PORT", "6379")), decode_responses=True)


def rows(sql):
    with db.cursor() as cur:
        cur.execute(sql)
        return cur.fetchall()


R.flushdb()  # this demo uses Redis DB 0 only for CampusConnect
pipe = R.pipeline()

# 1) Like sets and counters
for r in rows("SELECT post_id, user_id FROM post_like"):
    pipe.sadd(f"post:{r['post_id']}:likers", r["user_id"])
for r in rows("SELECT post_id, COUNT(*) AS n FROM post_like GROUP BY post_id"):
    pipe.set(f"post:{r['post_id']}:likes", r["n"])

# 2) Feeds: each user sees own posts + posts of accepted connections (sorted set, score = timestamp)
feed_sql = """
SELECT f.uid, p.post_id, UNIX_TIMESTAMP(p.created_at) AS ts
FROM (SELECT user_id AS uid, user_id AS author FROM user
      UNION ALL SELECT user_a, user_b FROM connection WHERE status='accepted'
      UNION ALL SELECT user_b, user_a FROM connection WHERE status='accepted') f
JOIN post p ON p.user_id = f.author
"""
for r in rows(feed_sql):
    pipe.zadd(f"feed:{r['uid']}", {r["post_id"]: float(r["ts"])})

# 3) Leaderboard: endorsements per skill, per department (dept 0 = general users)
lb_sql = """
SELECT COALESCE(u.dept_id,0) AS d, s.name AS skill, COUNT(*) AS n
FROM endorsement e JOIN user u ON u.user_id = e.endorsee_id
JOIN skill s ON s.skill_id = e.skill_id GROUP BY d, s.name
"""
for r in rows(lb_sql):
    pipe.zadd(f"lb:skills:{r['d']}", {r["skill"]: r["n"]})

# 4) Leaderboard: alumni activity = posts + jobs posted
act_sql = """
SELECT x.uid, COUNT(*) AS n FROM
 (SELECT user_id AS uid FROM post UNION ALL SELECT posted_by FROM job) x
JOIN user u ON u.user_id = x.uid AND u.user_type = 'alumni'
GROUP BY x.uid
"""
for r in rows(act_sql):
    pipe.zadd("lb:alumni:active", {r["uid"]: r["n"]})

pipe.execute()
print("Redis rebuilt. Keys:", R.dbsize())
