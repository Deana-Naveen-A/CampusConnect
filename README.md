# CampusConnect — MySQL + Redis + Neo4j

A LinkedIn-style campus network. Each database does the job it is best at:

| Store | What it holds | Where you see it |
|---|---|---|
| MySQL | users, jobs, skills, applications, connections (source of truth) | People, Jobs, feed connections |
| Redis | posts, likes, comments, hashtags, leaderboards | Feed, trending |
| Neo4j | the network as a graph (rebuilt from MySQL) | **Reports** page (admin only), "People you may know" |

## Before you start
- Python 3.10+
- MySQL 8 and its root password (the `mysql` command must work, or use MySQL Workbench, see step 2)
- Docker Desktop, running
- Run every command from this project folder (PowerShell on Windows; macOS/Linux commands are given where they differ)

## Setup (once)

**1. Start Redis and Neo4j**

    docker run -d --name cc-redis -p 6379:6379 redis:7
    docker run -d --name cc-neo4j -p 7474:7474 -p 7687:7687 -e "NEO4J_AUTH=neo4j/campusconnect" neo4j:5

If Docker says the name is already in use, the container exists already: `docker start cc-redis cc-neo4j`.
Wait about 30 seconds for Neo4j. Check with `docker ps --filter "name=cc-"` (both should be listed).

**2. Python environment**

    python -m venv .venv
    .venv\Scripts\activate                       (macOS/Linux: source .venv/bin/activate)
    pip install -r requirements.txt
    $env:MYSQL_PASSWORD='your_mysql_root_password'    (macOS/Linux: export MYSQL_PASSWORD='your_mysql_root_password')

Use single quotes so special characters in the password are kept.

**3. Load MySQL.** This erases and recreates the `mini_linkedin` database.

    mysql -u root -p -e "source schema.sql"
    mysql -u root -p -e "source seed.sql"
    mysql -u root -p -e "source reports.sql"

If Windows says `mysql` is not recognised, add it for this window (change the folder to match your install):

    $env:Path += ";C:\Program Files\MySQL\MySQL Server 8.0\bin"

Or skip the command line: in MySQL Workbench connect as root, open each file (File > Open SQL Script) and run it with the lightning-bolt button, in the order above.



**4. Load data and demo logins**

    python seed_redis.py
    python seed_neo4j.py
    python demo_accounts.py
    python create_admin.py

`seed_neo4j.py` should print `Neo4j graph built: {...}`.

**5. Run**

    python app.py

Open http://localhost:5000. (On macOS, if port 5000 is taken, change `port=5000` on the last line of `app.py`.)

## Demo logins (local demo only)

| Role | Email | Password |
|---|---|---|
| Admin (can open Reports) | admin@campusconnect.local | admin1234 |
| Sample user | sneha.kulkarni@example.com | demo1234 |
| Sample user | aarav.shah@example.com | demo1234 |

Every sample user in `seed.sql` uses `demo1234` with their own email. New people can use Sign up. For a private admin login instead, run `python create_admin.py`.
These passwords are public in the repo: never use them on a site other people can reach, and set a `SECRET_KEY` environment variable first.

## Every time you present (new terminal)

    docker start cc-redis cc-neo4j
    .venv\Scripts\activate
    $env:MYSQL_PASSWORD='your_mysql_root_password'
    python seed_neo4j.py
    python app.py

Re-running `seed_neo4j.py` makes sure the graph matches MySQL.

## 2-minute walkthrough
1. Log in as a sample user: open **Feed**, post something with `#dbms`, like and comment (Redis).
2. **People**: send a connection request. Log in as the other user and accept it (MySQL).
3. **Jobs**: show the skill-match percentage and apply (MySQL).
4. Log out, log in as admin, open **Reports**: network explorer, degrees of separation, top connectors, suggested connections, talent flow (Neo4j). Click **View Cypher** on a card.
5. Optional: Neo4j Browser at http://localhost:7474 (neo4j / campusconnect), run `MATCH p=()-[:CONNECTED_TO]->() RETURN p LIMIT 50`.
6. As a normal user, open `/reports`: it is refused. Only admins see analytics.

## Reset to a clean demo
Repeat steps 2 and 4 (MySQL scripts, then `seed_redis.py`, `seed_neo4j.py`, `demo_accounts.py`).

## Graph model

    (User)-[:CONNECTED_TO]->(User)      accepted connections     (User)-[:REQUESTED]->(User)  pending
    (User)-[:WORKED_AT]->(Company)      (User)-[:STUDIED_AT]->(School)
    (User)-[:HAS_SKILL]->(Skill)        (User)-[:ENDORSED {skill}]->(User)
    (Company)-[:POSTED]->(Job)-[:REQUIRES]->(Skill)      (User)-[:APPLIED_TO]->(Job)

How the stores connect: the Flask app (`app.py`) talks to all three through `db.py`, and `user_id` is the shared key
(MySQL `users.user_id`, Redis `user:<id>:posts`, Neo4j `(:User {id})`). MySQL is the source of truth; Neo4j is a copy
rebuilt from it after sign-ups, accepted connections, or the "Rebuild graph from MySQL" button on Reports.

## Troubleshooting
- `mysql` not recognised: see the PATH line in step 2, or use MySQL Workbench.
- `Access denied for user 'root'`: `MYSQL_PASSWORD` is wrong or was set in a different terminal window.
- `Unknown database mini_linkedin`: run step 2. `v_connections doesn't exist`: you skipped `reports.sql`.
- Docker "name already in use": `docker start cc-redis cc-neo4j`.
- Reports shows a Neo4j error: start the container, wait, then `python seed_neo4j.py`.
- "Forbidden" on Reports: you are logged in as a normal user; use the admin login.
- Feed looks empty: that account has no accepted connections yet; use People, or log in as a sample user from `seed.sql`.
