"""CampusConnect: Flask website.  MySQL = profiles/jobs, Redis = feed/likes/trending, Neo4j = graph reports."""
import json
import os
import re
import time

from flask import Flask, flash, jsonify, redirect, render_template, request, session

import seed_neo4j
from auth import admin_required, bp, login_required, user
from db import R, cypher, ensure_auth_columns, sql

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-only-change-me")
app.register_blueprint(bp)
ensure_auth_columns()

Q = dict(
    stats="""MATCH (u:User) WITH count(u) AS users
MATCH ()-[c:CONNECTED_TO]->() WITH users, count(c) AS links
OPTIONAL MATCH (i:User) WHERE NOT (i)-[:CONNECTED_TO]-()
RETURN users, links, count(i) AS isolated""",
    top="""MATCH (u:User)
OPTIONAL MATCH (u)-[:CONNECTED_TO]-(f:User)
RETURN u.name AS name, u.headline AS headline, count(DISTINCT f) AS degree
ORDER BY degree DESC, name LIMIT 6""",
    path="""MATCH (x:User {id:$a}), (y:User {id:$b})
MATCH p = shortestPath((x)-[:CONNECTED_TO*..8]-(y))
RETURN [n IN nodes(p) | n.name] AS names, length(p) AS hops""",
    pymk="""MATCH (me:User {id:$uid})-[:CONNECTED_TO]-(f:User)-[:CONNECTED_TO]-(s:User)
WHERE s <> me AND NOT (me)-[:CONNECTED_TO]-(s)
WITH me, s, collect(DISTINCT f.name) AS via
OPTIONAL MATCH (me)-[:HAS_SKILL]->(k:Skill)<-[:HAS_SKILL]-(s)
WITH me, s, via, count(DISTINCT k) AS shared
OPTIONAL MATCH (me)-[:STUDIED_AT]->(sc:School)<-[:STUDIED_AT]-(s)
WITH s, via, shared, count(DISTINCT sc) AS same
RETURN s.id AS id, s.name AS name, s.headline AS headline, size(via) AS mutual, via,
       shared, same, 3*size(via) + shared + 2*same AS score
ORDER BY score DESC LIMIT 5""",
    flow="""MATCH (a:Company)<-[:WORKED_AT]-(u:User)-[:WORKED_AT]->(b:Company)
WHERE a.name < b.name
RETURN a.name AS a, b.name AS b, count(DISTINCT u) AS people, collect(DISTINCT u.name) AS who
ORDER BY people DESC, a LIMIT 8""",
    pairs="""MATCH (x:Skill)<-[:HAS_SKILL]-(u:User)-[:HAS_SKILL]->(y:Skill)
WHERE x.name < y.name
RETURN x.name AS x, y.name AS y, count(u) AS people
ORDER BY people DESC, x LIMIT 8""",
    homo="""MATCH (a:User)-[:CONNECTED_TO]->(b:User)
OPTIONAL MATCH (a)-[:STUDIED_AT]->(s:School)<-[:STUDIED_AT]-(b)
WITH a, b, count(s) > 0 AS same
RETURN count(*) AS total, sum(CASE WHEN same THEN 1 ELSE 0 END) AS same_school""",
)


def cur():
    return session.get("uid", 1)


def people():
    return {u["user_id"]: u for u in sql("SELECT user_id, name, headline FROM users")}


@app.context_processor
def inject():
    return dict(viewer=user())


@app.template_filter("initials")
def initials(name):
    return "".join(w[0] for w in name.split()[:2]).upper()


@app.template_filter("ago")
def ago(ts):
    d = time.time() - float(ts)
    for n, u in ((86400, "d"), (3600, "h"), (60, "m")):
        if d >= n:
            return f"{int(d // n)}{u} ago"
    return "just now"


# ---------------------------------------------------------------- feed (MySQL + Redis + Neo4j)
@app.route("/")
@login_required
def feed():
    uid, P = cur(), people()
    friends = [r["friend_id"] for r in sql("SELECT friend_id FROM v_connections WHERE user_id=%s", (uid,))]
    tmp = f"tmp:feed:{uid}"
    R.zunionstore(tmp, [f"user:{i}:posts" for i in friends + [uid]], aggregate="MAX")
    ids = R.zrevrange(tmp, 0, 24)
    R.delete(tmp)
    posts = []
    for pid in ids:
        h = R.hgetall(f"post:{pid}")
        comments = []
        for raw in R.lrange(f"post:{pid}:comments", 0, -1):
            c = json.loads(raw)
            c["who"] = P[c["user_id"]]
            comments.append(c)
        posts.append(dict(id=pid, author=P[int(h["user_id"])], content=h["content"], at=h["created_at"],
                          likes=R.scard(f"post:{pid}:likes"), liked=R.sismember(f"post:{pid}:likes", uid),
                          comments=comments))
    try:
        pymk = cypher(Q["pymk"], uid=uid)[:3]
    except Exception:
        pymk = None
    tags = [(t, int(s)) for t, s in R.zrevrange("tags:trending", 0, 5, withscores=True)]
    return render_template("feed.html", posts=posts, tags=tags, pymk=pymk, nconn=len(friends), me=P[uid])


@app.post("/post")
@login_required
def new_post():
    text = request.form["content"].strip()
    if text:
        if not R.exists("seq:post"):
            R.set("seq:post", 40)
        pid, now = R.incr("seq:post"), time.time()
        R.hset(f"post:{pid}", mapping=dict(user_id=cur(), content=text, created_at=now))
        R.zadd(f"user:{cur()}:posts", {pid: now})
        R.zadd("lb:posts:likes", {pid: 0})
        for t in set(re.findall(r"#(\w+)", text.lower())):
            R.sadd(f"tag:{t}", pid)
            R.zincrby("tags:trending", 1, t)
    return redirect("/")


@app.post("/like/<pid>")
@login_required
def like(pid):
    k = f"post:{pid}:likes"
    (R.srem if R.sismember(k, cur()) else R.sadd)(k, cur())
    R.zadd("lb:posts:likes", {pid: R.scard(k)})
    return redirect("/")


@app.post("/comment/<pid>")
@login_required
def comment(pid):
    t = request.form["text"].strip()
    if t:
        R.rpush(f"post:{pid}:comments", json.dumps(dict(user_id=cur(), text=t, at=time.time())))
        R.zincrby("lb:commenters", 1, cur())
    return redirect("/")




# ---------------------------------------------------------------- jobs (MySQL)
@app.route("/jobs")
@login_required
def jobs():
    uid = cur()
    rows = sql("""SELECT j.job_id, j.title, c.name AS company, j.department, j.job_type, j.salary,
                  COUNT(js.skill_id) AS req, COUNT(us.skill_id) AS have,
                  GROUP_CONCAT(CASE WHEN us.skill_id IS NULL THEN s.name END SEPARATOR ', ') AS missing
                  FROM job j JOIN company c ON c.company_id = j.company_id
                  JOIN job_skill js ON js.job_id = j.job_id JOIN skill s ON s.skill_id = js.skill_id
                  LEFT JOIN user_skill us ON us.skill_id = js.skill_id AND us.user_id = %s
                  GROUP BY j.job_id, c.name""", (uid,))
    for r in rows:
        r["pct"] = round(100 * r["have"] / r["req"])
        if isinstance(r["missing"], (bytes, bytearray)):
            r["missing"] = r["missing"].decode()
    rows.sort(key=lambda r: -r["pct"])
    applied = {r["job_id"]: r["status"] for r in sql("SELECT job_id, status FROM application WHERE user_id=%s", (uid,))}
    return render_template("jobs.html", jobs=rows, applied=applied)


@app.post("/apply/<int:job_id>")
@login_required
def apply(job_id):
    sql("INSERT IGNORE INTO application(job_id, user_id, status, applied_on) VALUES (%s, %s, 'applied', CURDATE())",
        (job_id, cur()))
    return redirect("/jobs")


# ---------------------------------------------------------------- reports (Neo4j)
@app.route("/reports")
@admin_required
def reports():
    plist = sql("SELECT user_id, name FROM users WHERE is_admin=0 ORDER BY name")
    ids = [p["user_id"] for p in plist]
    uid = int(request.args.get("u", ids[0] if ids else 0))
    a = int(request.args.get("a", uid))
    b = int(request.args.get("b", ids[-1] if ids else 0))
    ctx = dict(Q=Q, a=a, b=b, uid=uid, plist=plist)
    try:
        ctx["stats"] = cypher(Q["stats"])[0]
        ctx["top"] = cypher(Q["top"])
        ctx["maxdeg"] = max([r["degree"] for r in ctx["top"]] or [1]) or 1
        ctx["pymk"] = cypher(Q["pymk"], uid=uid)
        ctx["path"] = cypher(Q["path"], a=a, b=b)[:1] if a != b else []
        ctx["flow"] = cypher(Q["flow"])
        ctx["pairs"] = cypher(Q["pairs"])
        ctx["homo"] = cypher(Q["homo"])[0]
    except Exception as e:
        ctx["err"] = str(e)
    return render_template("reports.html", **ctx)


@app.route("/api/graph")
@admin_required
def graph():
    uid = int(request.args.get("uid", cur()))
    depth = min(max(int(request.args.get("depth", 2)), 1), 3)
    rows = cypher(f"""MATCH p = (me:User {{id:$uid}})-[:CONNECTED_TO*1..{depth}]-(:User)
        UNWIND relationships(p) AS r WITH DISTINCT r
        RETURN startNode(r).id AS a, startNode(r).name AS an, startNode(r).school AS asch,
               endNode(r).id AS b, endNode(r).name AS bn, endNode(r).school AS bsch""", uid=uid)
    nodes, edges = {}, []
    for r in rows:
        nodes[r["a"]] = dict(id=r["a"], label=r["an"].split()[0], title=f'{r["an"]} · {r["asch"] or "no school listed"}', group=r["asch"])
        nodes[r["b"]] = dict(id=r["b"], label=r["bn"].split()[0], title=f'{r["bn"]} · {r["bsch"] or "no school listed"}', group=r["bsch"])
        edges.append({"from": r["a"], "to": r["b"]})
    if uid not in nodes:
        nodes[uid] = dict(id=uid, label=people()[uid]["name"].split()[0])
    nodes[uid].update(size=26, borderWidth=4)
    return jsonify(nodes=list(nodes.values()), edges=edges)


@app.post("/sync")
@admin_required
def sync():
    try:
        flash("Graph rebuilt from MySQL: " + str(seed_neo4j.sync()))
    except Exception as e:
        flash(f"Could not rebuild graph: {e}")
    return redirect("/reports")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
