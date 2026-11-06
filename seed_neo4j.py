"""Builds the Neo4j graph from MySQL (MySQL stays the source of truth).   Run:  python seed_neo4j.py"""
from db import NEO, ensure_auth_columns, sql


def sync():
    ensure_auth_columns()
    users = sql("SELECT u.user_id AS id, u.name, u.headline, u.location, "
                "(SELECT e.school FROM education e WHERE e.user_id=u.user_id ORDER BY e.grad_year LIMIT 1) AS school FROM users u WHERE u.is_admin = 0")
    companies = sql("SELECT company_id AS id, name, industry FROM company")
    skills = sql("SELECT skill_id AS id, name FROM skill")
    schools = [{"name": n} for n in sorted({r["school"] for r in sql("SELECT school FROM education")})]
    jobs = [dict(r, salary=float(r["salary"])) for r in
            sql("SELECT job_id AS id, company_id, title, department, job_type AS type, salary FROM job")]
    links = sql("SELECT requester_id AS a, receiver_id AS b, status FROM connection")
    exp = [dict(r, started=str(r["started"]), ended=str(r["ended"]) if r["ended"] else None) for r in
           sql("SELECT user_id AS u, company_id AS c, title, start_date AS started, end_date AS ended FROM experience")]
    edu = sql("SELECT user_id AS u, school, degree, grad_year AS yr FROM education")
    uskill = sql("SELECT user_id AS u, skill_id AS k FROM user_skill")
    endorse = sql("SELECT e.endorser_id AS a, us.user_id AS b, s.name AS skill FROM endorsement e "
                  "JOIN user_skill us ON us.user_skill_id=e.user_skill_id JOIN skill s ON s.skill_id=us.skill_id")
    jskill = sql("SELECT job_id AS j, skill_id AS k FROM job_skill")
    apps = [dict(r, applied=str(r["applied"])) for r in
            sql("SELECT user_id AS u, job_id AS j, status, applied_on AS applied FROM application")]

    steps = [
        ("UNWIND $rows AS r CREATE (:User {id:r.id, name:r.name, headline:r.headline, location:r.location, school:r.school})", users),
        ("UNWIND $rows AS r CREATE (:Company {id:r.id, name:r.name, industry:r.industry})", companies),
        ("UNWIND $rows AS r CREATE (:Skill {id:r.id, name:r.name})", skills),
        ("UNWIND $rows AS r CREATE (:School {name:r.name})", schools),
        ("UNWIND $rows AS r CREATE (:Job {id:r.id, title:r.title, department:r.department, type:r.type, salary:r.salary})", jobs),
        ("UNWIND $rows AS r MATCH (c:Company {id:r.company_id}), (j:Job {id:r.id}) CREATE (c)-[:POSTED]->(j)", jobs),
        ("UNWIND $rows AS r MATCH (a:User {id:r.a}), (b:User {id:r.b}) WHERE r.status = 'accepted' CREATE (a)-[:CONNECTED_TO]->(b)", links),
        ("UNWIND $rows AS r MATCH (a:User {id:r.a}), (b:User {id:r.b}) WHERE r.status = 'pending' CREATE (a)-[:REQUESTED]->(b)", links),
        ("UNWIND $rows AS r MATCH (u:User {id:r.u}), (c:Company {id:r.c}) CREATE (u)-[:WORKED_AT {title:r.title, started:r.started, ended:r.ended}]->(c)", exp),
        ("UNWIND $rows AS r MATCH (u:User {id:r.u}), (s:School {name:r.school}) CREATE (u)-[:STUDIED_AT {degree:r.degree, grad_year:r.yr}]->(s)", edu),
        ("UNWIND $rows AS r MATCH (u:User {id:r.u}), (k:Skill {id:r.k}) CREATE (u)-[:HAS_SKILL]->(k)", uskill),
        ("UNWIND $rows AS r MATCH (a:User {id:r.a}), (b:User {id:r.b}) CREATE (a)-[:ENDORSED {skill:r.skill}]->(b)", endorse),
        ("UNWIND $rows AS r MATCH (j:Job {id:r.j}), (k:Skill {id:r.k}) CREATE (j)-[:REQUIRES]->(k)", jskill),
        ("UNWIND $rows AS r MATCH (u:User {id:r.u}), (j:Job {id:r.j}) CREATE (u)-[:APPLIED_TO {status:r.status, on_date:r.applied}]->(j)", apps),
    ]
    with NEO.session() as s:
        s.run("MATCH (n) DETACH DELETE n").consume()
        for lbl in ("User", "Company", "Skill", "Job"):
            s.run(f"CREATE CONSTRAINT {lbl.lower()}_id IF NOT EXISTS FOR (n:{lbl}) REQUIRE n.id IS UNIQUE").consume()
        for q, rows in steps:
            s.run(q, rows=rows).consume()
        return s.run("MATCH (n) WITH count(n) AS nodes MATCH ()-[r]->() RETURN nodes, count(r) AS relationships").single().data()


if __name__ == "__main__":
    print("Neo4j graph built:", sync())
