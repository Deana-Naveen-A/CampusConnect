"""Seeds Redis (posts with comments + likes, hashtags, messages, notifications).
user_id values match users.user_id in MySQL. Run after the MySQL scripts.
Uses Redis logical DB 1 (override with REDIS_DB) so it never touches other projects' keys."""
import json
import os
import random
from datetime import datetime, timedelta

import redis

random.seed(11)
r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", "6379")),
                db=int(os.getenv("REDIS_DB", "1")), decode_responses=True)
r.flushdb()

texts = [
    ("Just finished my first ML mini project!", ["ml", "student"]),
    ("Excited to start my internship this month", ["internship", "career"]),
    ("Tips for cracking DSA interviews?", ["dsa", "placements"]),
    ("Hackathon weekend was amazing", ["hackathon", "coding"]),
    ("Learning Redis alongside SQL for my DBMS project", ["dbms", "redis"]),
    ("Open to work: backend roles", ["hiring", "backend"]),
    ("Published my first blog on Docker basics", ["docker", "devops"]),
    ("Campus placement season is here", ["placements", "career"]),
]
now = datetime(2026, 10, 24)
ts = lambda d: d.timestamp()          # score used for time ordering
pipe = r.pipeline()

# ---- posts: hash (fields) + set (likes) + list (comments) + sorted sets (indexes)
for pid in range(1, 41):
    text, tags = random.choice(texts)
    author = random.randint(1, 20)
    created = now - timedelta(hours=random.randint(1, 400))
    likes = random.sample([u for u in range(1, 21) if u != author], random.randint(0, 10))
    comments = [{"user_id": random.randint(1, 20),
                 "text": random.choice(["Congrats!", "Nice work", "Great post", "Thanks for sharing"]),
                 "at": ts(now - timedelta(hours=random.randint(0, 50)))}
                for _ in range(random.randint(0, 4))]

    pipe.hset(f"post:{pid}", mapping={"user_id": author, "content": text, "created_at": ts(created)})
    pipe.zadd(f"user:{author}:posts", {pid: ts(created)})      # per-author timeline (feed building block)
    for tag in tags:
        pipe.zincrby("tags:trending", 1, tag)                  # trending hashtags
        pipe.sadd(f"tag:{tag}", pid)                           # posts per hashtag
    if likes:
        pipe.sadd(f"post:{pid}:likes", *likes)                 # who liked (no double likes)
    pipe.zadd("lb:posts:likes", {pid: len(likes)})             # most-liked leaderboard
    for c in comments:
        pipe.rpush(f"post:{pid}:comments", json.dumps(c))      # comments in order
        pipe.zincrby("lb:commenters", 1, c["user_id"])         # most active commenters

# ---- messages: hash per message, inbox sorted set per receiver, unread leaderboard
for mid in range(1, 61):
    a, b = random.sample(range(1, 21), 2)
    sent = now - timedelta(minutes=random.randint(1, 5000))
    read = random.random() < .6
    pipe.hset(f"msg:{mid}", mapping={"from_id": a, "to_id": b, "sent_at": ts(sent), "read": int(read),
                                     "text": random.choice(["Hi!", "Can you refer me?", "Let's connect", "Thanks!"])})
    pipe.zadd(f"inbox:{b}", {mid: ts(sent)})
    if not read:
        pipe.zincrby("lb:unread", 1, b)

# ---- notifications: one sorted set per user and state (member = JSON, score = time)
for nid in range(1, 51):
    uid = random.randint(1, 20)
    created = now - timedelta(minutes=random.randint(1, 3000))
    seen = random.random() < .5
    note = json.dumps({"id": nid, "type": random.choice(["like", "comment", "connection_request", "job_alert"]),
                       "from": random.randint(1, 20)})
    pipe.zadd(f"notif:{uid}:{'seen' if seen else 'unseen'}", {note: ts(created)})

pipe.execute()
print(f"Redis (db {r.connection_pool.connection_kwargs['db']}) seeded: "
      f"{len(r.keys('post:?')) + len(r.keys('post:??'))} posts, {len(r.keys('msg:*'))} messages, "
      f"{len(r.keys('notif:*'))} notification sets, {r.dbsize()} keys total")
