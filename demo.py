"""Hybrid demo: MySQL (relational) + Redis (feeds, counters, leaderboards).
pip install mysql-connector-python redis
Edit MYSQL below if your password differs (or set MYSQL_PASSWORD)."""
import os

import mysql.connector
import redis

MYSQL = dict(host="localhost", user="root", password=os.getenv("MYSQL_PASSWORD", ""), database="mini_linkedin")
sql = mysql.connector.connect(**MYSQL)
R = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", "6379")),
                db=int(os.getenv("REDIS_DB", "1")), decode_responses=True)


def q(query, params=None):
    cur = sql.cursor(dictionary=True)
    cur.execute(query, params or ())
    rows = cur.fetchall()
    cur.close()
    return rows


def show(rows, title):
    print(f"\n=== {title} ===")
    for r in rows:
        print("  ", dict(r))


def names():
    return {r["user_id"]: r["name"] for r in q("SELECT user_id, name FROM users")}


def hybrid_feed(uid):
    """SQL: who are my connections?  Redis: their latest posts (union of their timelines)."""
    friends = [r["friend_id"] for r in q(
        "SELECT friend_id FROM (SELECT requester_id AS user_id, receiver_id AS friend_id FROM connection WHERE status='accepted' "
        "UNION SELECT receiver_id, requester_id FROM connection WHERE status='accepted') c WHERE user_id=%s", (uid,))]
    nm = names()
    print(f"\n=== Feed for {nm[uid]} (from {len(friends)} connections) ===")
    if not friends:
        print("   No connections yet.")
        return
    tmp = f"tmp:feed:{uid}"
    R.zunionstore(tmp, [f"user:{f}:posts" for f in friends], aggregate="MAX")
    post_ids = R.zrevrange(tmp, 0, 4)
    R.delete(tmp)
    for pid in post_ids:
        author, content = R.hmget(f"post:{pid}", "user_id", "content")
        print(f"  {nm[int(author)]}: {content}  | {R.scard(f'post:{pid}:likes')} likes, {R.llen(f'post:{pid}:comments')} comments")


def redis_reports():
    nm = names()
    top = [{"post_id": int(p), "content": R.hget(f"post:{p}", "content"), "likes": int(s)}
           for p, s in R.zrevrange("lb:posts:likes", 0, 4, withscores=True)]
    show(top, "Top 5 most-liked posts (Redis)")
    show([{"hashtag": t, "posts": int(s)} for t, s in R.zrevrange("tags:trending", 0, 4, withscores=True)],
         "Trending hashtags (Redis)")
    show([{"user": nm[int(u)], "comments": int(s)} for u, s in R.zrevrange("lb:commenters", 0, 4, withscores=True)],
         "Most active commenters (Redis)")
    show([{"user": nm[int(u)], "unread": int(s)} for u, s in R.zrevrange("lb:unread", 0, 4, withscores=True)],
         "Users with most unread messages (Redis)")


def sql_reports():
    show(q("SELECT department, ROUND(AVG(salary),2) AS avg_salary_lpa FROM job GROUP BY department ORDER BY 2 DESC"),
         "Average salary per department")
    show(q("SELECT s.name skill, COUNT(*) endorsements FROM skill s JOIN user_skill us USING(skill_id) "
           "JOIN endorsement e USING(user_skill_id) GROUP BY s.skill_id ORDER BY 2 DESC LIMIT 5"), "Top endorsed skills")


def call(proc, uid, title):
    cur = sql.cursor(dictionary=True)
    cur.callproc(proc, (uid,))
    for res in cur.stored_results():
        show(res.fetchall(), title)
    cur.close()


MENU = """
1  SQL reports            4  Skill-gap analyzer (novelty)
2  Redis reports          5  People you may know (novelty)
3  Hybrid feed (SQL+Redis)   0  Exit"""

if __name__ == "__main__":
    while True:
        print(MENU)
        c = input("choice: ").strip()
        if c == "0":
            break
        if c == "1": sql_reports()
        elif c == "2": redis_reports()
        elif c in ("3", "4", "5"):
            uid = int(input("user_id (1-20): "))
            if c == "3": hybrid_feed(uid)
            elif c == "4": call("skill_gap", uid, f"Skill-gap for user {uid}")
            else: call("recommend_connections", uid, f"Suggested connections for user {uid}")
