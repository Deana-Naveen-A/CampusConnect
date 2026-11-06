-- Mini LinkedIn: relational part (MySQL 8 / MariaDB)
DROP DATABASE IF EXISTS mini_linkedin;
CREATE DATABASE mini_linkedin;
USE mini_linkedin;

CREATE TABLE users (
  user_id   INT AUTO_INCREMENT PRIMARY KEY,
  name      VARCHAR(100) NOT NULL,
  email     VARCHAR(120) NOT NULL UNIQUE,
  headline  VARCHAR(150),
  location  VARCHAR(80)
);

CREATE TABLE company (
  company_id INT AUTO_INCREMENT PRIMARY KEY,
  name       VARCHAR(100) NOT NULL UNIQUE,
  industry   VARCHAR(80)
);

CREATE TABLE experience (
  exp_id     INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NOT NULL,
  company_id INT NOT NULL,
  title      VARCHAR(100) NOT NULL,
  start_date DATE NOT NULL,
  end_date   DATE,
  FOREIGN KEY (user_id)    REFERENCES users(user_id)     ON DELETE CASCADE,
  FOREIGN KEY (company_id) REFERENCES company(company_id),
  CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE TABLE education (
  edu_id  INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  school  VARCHAR(120) NOT NULL,
  degree  VARCHAR(80),
  grad_year INT,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE skill (
  skill_id INT AUTO_INCREMENT PRIMARY KEY,
  name     VARCHAR(60) NOT NULL UNIQUE
);

-- M:N users <-> skills
CREATE TABLE user_skill (
  user_skill_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id  INT NOT NULL,
  skill_id INT NOT NULL,
  UNIQUE (user_id, skill_id),
  FOREIGN KEY (user_id)  REFERENCES users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (skill_id) REFERENCES skill(skill_id)
);

-- endorsement is tied to one person's claim of one skill
CREATE TABLE endorsement (
  endorsement_id INT AUTO_INCREMENT PRIMARY KEY,
  user_skill_id  INT NOT NULL,
  endorser_id    INT NOT NULL,
  UNIQUE (user_skill_id, endorser_id),
  FOREIGN KEY (user_skill_id) REFERENCES user_skill(user_skill_id) ON DELETE CASCADE,
  FOREIGN KEY (endorser_id)   REFERENCES users(user_id) ON DELETE CASCADE
);

-- self-referencing on users
CREATE TABLE connection (
  connection_id INT AUTO_INCREMENT PRIMARY KEY,
  requester_id  INT NOT NULL,
  receiver_id   INT NOT NULL,
  status ENUM('pending','accepted','rejected') NOT NULL DEFAULT 'pending',
  UNIQUE (requester_id, receiver_id),
  FOREIGN KEY (requester_id) REFERENCES users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (receiver_id)  REFERENCES users(user_id) ON DELETE CASCADE,
  CHECK (requester_id <> receiver_id)
);

CREATE TABLE job (
  job_id      INT AUTO_INCREMENT PRIMARY KEY,
  company_id  INT NOT NULL,
  title       VARCHAR(100) NOT NULL,
  department  VARCHAR(60)  NOT NULL,
  job_type    ENUM('full-time','internship','part-time') NOT NULL,
  salary      DECIMAL(10,2),           -- annual, INR lakhs
  posted_date DATE NOT NULL,
  FOREIGN KEY (company_id) REFERENCES company(company_id) ON DELETE CASCADE
);

-- NOVELTY: skills required by a job
CREATE TABLE job_skill (
  job_id   INT NOT NULL,
  skill_id INT NOT NULL,
  PRIMARY KEY (job_id, skill_id),
  FOREIGN KEY (job_id)   REFERENCES job(job_id)   ON DELETE CASCADE,
  FOREIGN KEY (skill_id) REFERENCES skill(skill_id)
);

CREATE TABLE application (
  application_id INT AUTO_INCREMENT PRIMARY KEY,
  job_id  INT NOT NULL,
  user_id INT NOT NULL,
  status  ENUM('applied','shortlisted','rejected','hired') NOT NULL DEFAULT 'applied',
  applied_on DATE NOT NULL,
  UNIQUE (job_id, user_id),
  FOREIGN KEY (job_id)  REFERENCES job(job_id)   ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_conn_receiver ON connection(receiver_id, status);
CREATE INDEX idx_job_dept ON job(department);
