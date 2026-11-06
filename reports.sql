USE mini_linkedin;

-- helper view: connections as an undirected edge list (both directions)
CREATE OR REPLACE VIEW v_connections AS
  SELECT requester_id AS user_id, receiver_id  AS friend_id FROM connection WHERE status='accepted'
  UNION
  SELECT receiver_id,  requester_id            FROM connection WHERE status='accepted';

-- ===================== REPORTS =====================

-- R1. Average salary per department
SELECT department, COUNT(*) AS openings, ROUND(AVG(salary),2) AS avg_salary_lpa
FROM job GROUP BY department ORDER BY avg_salary_lpa DESC;

-- R2. Departments paying above 12 LPA on average (HAVING)
SELECT department, ROUND(AVG(salary),2) AS avg_salary_lpa
FROM job WHERE job_type='full-time'
GROUP BY department HAVING AVG(salary) > 12;

-- R3. Top 5 most endorsed skills
SELECT s.name AS skill, COUNT(e.endorsement_id) AS endorsements
FROM skill s
JOIN user_skill us ON us.skill_id = s.skill_id
JOIN endorsement e ON e.user_skill_id = us.user_skill_id
GROUP BY s.skill_id ORDER BY endorsements DESC LIMIT 5;

-- R4. Users with most connections
SELECT u.name, COUNT(*) AS connections
FROM v_connections c JOIN users u ON u.user_id = c.user_id
GROUP BY u.user_id ORDER BY connections DESC LIMIT 5;

-- R5. Applications per job (include jobs with zero applications)
SELECT j.title, c.name AS company, COUNT(a.application_id) AS applications
FROM job j JOIN company c ON c.company_id = j.company_id
LEFT JOIN application a ON a.job_id = j.job_id
GROUP BY j.job_id ORDER BY applications DESC;

-- R6. Companies with most job postings
SELECT c.name, COUNT(j.job_id) AS postings
FROM company c LEFT JOIN job j ON j.company_id = c.company_id
GROUP BY c.company_id ORDER BY postings DESC;

-- R7. Mutual connections between user 1 and user 2 (self-join)
SELECT u.name AS mutual_connection
FROM v_connections a
JOIN v_connections b ON a.friend_id = b.friend_id
JOIN users u ON u.user_id = a.friend_id
WHERE a.user_id = 1 AND b.user_id = 2;

-- R8. Hiring funnel: applications by status
SELECT status, COUNT(*) AS total FROM application GROUP BY status;

-- ===================== NOVELTY 1: SKILL-GAP ANALYZER =====================
-- Match % of a user against every job, plus missing skills
DROP PROCEDURE IF EXISTS skill_gap;
DELIMITER //
CREATE PROCEDURE skill_gap(IN p_user INT)
BEGIN
  SELECT j.job_id, j.title, c.name AS company,
         COUNT(js.skill_id) AS required,
         COUNT(us.skill_id) AS you_have,
         ROUND(100 * COUNT(us.skill_id) / COUNT(js.skill_id), 0) AS match_pct,
         GROUP_CONCAT(CASE WHEN us.skill_id IS NULL THEN s.name END SEPARATOR ', ') AS missing_skills
  FROM job j
  JOIN company c   ON c.company_id = j.company_id
  JOIN job_skill js ON js.job_id = j.job_id
  JOIN skill s      ON s.skill_id = js.skill_id
  LEFT JOIN user_skill us ON us.skill_id = js.skill_id AND us.user_id = p_user
  GROUP BY j.job_id
  ORDER BY match_pct DESC, j.job_id;
END //
DELIMITER ;
-- usage:  CALL skill_gap(2);

-- ===================== NOVELTY 2: "PEOPLE YOU MAY KNOW" =====================
-- score = 3 x mutual connections + 1 x shared skills + 2 if same school
DROP PROCEDURE IF EXISTS recommend_connections;
DELIMITER //
CREATE PROCEDURE recommend_connections(IN p_user INT)
BEGIN
  SELECT u.user_id, u.name,
         IFNULL(m.mutual,0)  AS mutual_connections,
         IFNULL(sk.shared,0) AS shared_skills,
         IFNULL(ed.same,0)   AS same_school,
         3*IFNULL(m.mutual,0) + IFNULL(sk.shared,0) + 2*IFNULL(ed.same,0) AS score
  FROM users u
  LEFT JOIN (SELECT b.friend_id AS uid, COUNT(*) AS mutual
             FROM v_connections a JOIN v_connections b ON a.friend_id = b.user_id
             WHERE a.user_id = p_user AND b.friend_id <> p_user
             GROUP BY b.friend_id) m ON m.uid = u.user_id
  LEFT JOIN (SELECT o.user_id AS uid, COUNT(*) AS shared
             FROM user_skill me JOIN user_skill o ON o.skill_id = me.skill_id
             WHERE me.user_id = p_user GROUP BY o.user_id) sk ON sk.uid = u.user_id
  LEFT JOIN (SELECT o.user_id AS uid, 1 AS same
             FROM education me JOIN education o ON o.school = me.school
             WHERE me.user_id = p_user GROUP BY o.user_id) ed ON ed.uid = u.user_id
  WHERE u.user_id <> p_user
    AND u.user_id NOT IN (SELECT friend_id FROM v_connections WHERE user_id = p_user)
  ORDER BY score DESC LIMIT 5;
END //
DELIMITER ;
-- usage:  CALL recommend_connections(2);
