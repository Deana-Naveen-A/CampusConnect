USE mini_linkedin;
INSERT INTO users(name,email,headline,location) VALUES
('Aarav Shah','aarav.shah@example.com','DevOps Engineer','Hyderabad'),
('Bhoomika K','bhoomika.k@example.com','Product Analyst','Bangalore'),
('Charan Reddy','charan.reddy@example.com','Backend Developer','Mumbai'),
('Diya Nair','diya.nair@example.com','Backend Developer','Pune'),
('Eshan Rao','eshan.rao@example.com','ML Engineer','Mumbai'),
('Fatima Khan','fatima.khan@example.com','Frontend Developer','Bangalore'),
('Gautam Iyer','gautam.iyer@example.com','Backend Developer','Chennai'),
('Harini S','harini.s@example.com','Product Analyst','Bangalore'),
('Ishaan Mehta','ishaan.mehta@example.com','Frontend Developer','Bangalore'),
('Jaya Menon','jaya.menon@example.com','Product Analyst','Bangalore'),
('Kabir Singh','kabir.singh@example.com','Backend Developer','Hyderabad'),
('Lakshmi P','lakshmi.p@example.com','ML Engineer','Mumbai'),
('Manav Joshi','manav.joshi@example.com','Product Analyst','Bangalore'),
('Nisha Patel','nisha.patel@example.com','Frontend Developer','Bangalore'),
('Omkar Desai','omkar.desai@example.com','Data Analyst','Pune'),
('Priya Sharma','priya.sharma@example.com','Product Analyst','Hyderabad'),
('Rohan Gupta','rohan.gupta@example.com','Backend Developer','Mumbai'),
('Sneha Kulkarni','sneha.kulkarni@example.com','Student at PES University','Mumbai'),
('Tanvi Bhat','tanvi.bhat@example.com','Data Analyst','Bangalore'),
('Varun Hegde','varun.hegde@example.com','Frontend Developer','Pune');
INSERT INTO company(name,industry) VALUES ('Infosys','IT Services'),('Flipkart','E-commerce'),('Razorpay','Fintech'),('Bosch','Engineering'),('Swiggy','Food Tech'),('Zoho','Software');
INSERT INTO skill(name) VALUES ('Python'),('SQL'),('Java'),('Machine Learning'),('React'),('MongoDB'),('Docker'),('Data Analysis'),('C++'),('AWS');
INSERT INTO experience(user_id,company_id,title,start_date,end_date) VALUES
(2,4,'Developer','2019-06-01',NULL),
(2,3,'Software Engineer','2022-03-01','2023-08-28'),
(3,5,'Developer','2020-06-01','2021-02-28'),
(3,1,'Developer','2022-03-01',NULL),
(4,1,'Intern','2020-09-01','2021-08-28'),
(5,5,'Developer','2021-08-01','2022-06-28'),
(5,4,'Intern','2019-01-01','2020-02-28'),
(6,6,'Developer','2021-06-01','2022-08-28'),
(6,2,'Intern','2019-08-01','2020-08-28'),
(9,4,'Developer','2020-02-01','2021-04-28'),
(11,2,'Developer','2022-09-01','2023-09-28'),
(12,2,'Software Engineer','2022-02-01','2023-06-28'),
(16,5,'Software Engineer','2020-05-01','2021-01-28'),
(16,4,'Analyst','2021-06-01',NULL),
(18,6,'Developer','2023-07-01','2024-01-28'),
(18,4,'Developer','2022-01-01',NULL);
INSERT INTO education(user_id,school,degree,grad_year) VALUES
(1,'RVCE','M.Tech',2025),
(2,'PES University','M.Tech',2028),
(3,'PES University','B.Tech',2024),
(4,'NIT Surathkal','B.Tech',2028),
(5,'PES University','M.Tech',2028),
(6,'PES University','B.Tech',2025),
(7,'NIT Surathkal','M.Tech',2025),
(8,'BMSCE','M.Tech',2028),
(9,'BMSCE','M.Tech',2024),
(10,'PES University','M.Tech',2027),
(11,'IIIT Hyderabad','M.Tech',2026),
(12,'PES University','B.Tech',2024),
(13,'BMSCE','BCA',2026),
(14,'IIIT Hyderabad','BCA',2025),
(15,'NIT Surathkal','B.Tech',2025),
(16,'NIT Surathkal','M.Tech',2025),
(17,'NIT Surathkal','B.Tech',2028),
(18,'BMSCE','BCA',2024),
(19,'BMSCE','BCA',2026),
(20,'RVCE','M.Tech',2025);
INSERT INTO user_skill(user_id,skill_id) VALUES (1,2),(1,6),(1,8),(1,9),(1,10),(2,2),(2,4),(2,6),(2,7),(2,10),(3,6),(3,8),(3,9),(4,1),(4,3),(4,4),(4,5),(4,10),(5,6),(5,8),(5,10),(6,1),(6,2),(6,6),(6,8),(6,10),(7,4),(7,6),(7,8),(8,1),(8,8),(8,10),(9,2),(9,4),(9,6),(9,9),(9,10),(10,3),(10,7),(10,8),(11,2),(11,4),(11,6),(11,7),(11,8),(12,1),(12,2),(12,3),(12,9),(12,10),(13,3),(13,8),(13,10),(14,2),(14,5),(14,6),(14,8),(14,10),(15,1),(15,3),(15,6),(15,7),(15,9),(16,2),(16,3),(16,4),(16,9),(16,10),(17,1),(17,4),(17,5),(18,3),(18,4),(18,6),(18,9),(19,1),(19,3),(19,6),(19,7),(19,9),(20,7),(20,8),(20,9),(20,10);
INSERT INTO endorsement(user_skill_id,endorser_id) VALUES (1,5),(3,13),(3,15),(6,4),(6,6),(8,8),(8,11),(9,15),(10,8),(14,3),(14,18),(15,8),(16,5),(16,13),(16,18),(18,14),(18,15),(19,9),(21,8),(21,14),(23,5),(24,20),(25,9),(26,12),(26,15),(28,10),(29,4),(32,17),(34,18),(35,5),(36,15),(41,3),(42,3),(42,20),(43,17),(44,14),(44,18),(47,1),(51,16),(52,5),(55,3),(55,9),(57,11),(61,20),(62,17),(65,5),(65,15),(65,20),(66,3),(66,7),(66,13),(66,18),(67,17),(68,17),(69,5),(72,1),(72,16),(74,16),(80,10),(83,12);
INSERT INTO connection(requester_id,receiver_id,status) VALUES (1,3,'accepted'),(1,11,'accepted'),(1,20,'accepted'),(2,3,'accepted'),(2,6,'accepted'),(2,17,'accepted'),(3,5,'pending'),(3,9,'accepted'),(3,16,'pending'),(4,15,'pending'),(5,1,'accepted'),(5,13,'accepted'),(6,1,'rejected'),(6,9,'accepted'),(6,14,'pending'),(7,8,'accepted'),(7,10,'accepted'),(7,12,'pending'),(7,17,'pending'),(8,4,'accepted'),(9,2,'pending'),(9,5,'pending'),(9,12,'accepted'),(9,17,'accepted'),(10,2,'accepted'),(10,8,'pending'),(10,17,'pending'),(11,7,'pending'),(11,8,'accepted'),(11,13,'pending'),(11,18,'accepted'),(12,1,'accepted'),(12,2,'accepted'),(13,17,'accepted'),(13,19,'accepted'),(14,16,'accepted'),(15,1,'accepted'),(15,6,'pending'),(15,17,'accepted'),(16,8,'accepted'),(17,1,'accepted'),(17,18,'accepted'),(18,13,'accepted'),(18,14,'accepted'),(20,8,'pending');
INSERT INTO job(company_id,title,department,job_type,salary,posted_date) VALUES
(5,'Backend Developer','Engineering','full-time',26.0,'2026-10-03'),
(1,'ML Engineer','Data Science','full-time',23.8,'2026-10-24'),
(1,'Data Analyst','Data Science','full-time',19.4,'2026-09-08'),
(2,'UI Developer','Design','full-time',25.5,'2026-08-24'),
(4,'Product Manager','Product','full-time',23.6,'2026-09-28'),
(4,'DevOps Engineer','Engineering','full-time',17.2,'2026-10-10'),
(5,'Research Intern','Engineering','internship',7.1,'2026-10-21'),
(5,'Data Engineer','Data Science','full-time',12.8,'2026-08-11'),
(6,'QA Engineer','Engineering','full-time',14.1,'2026-10-10'),
(2,'Full Stack Developer','Engineering','full-time',22.9,'2026-08-16');
INSERT INTO job_skill(job_id,skill_id) VALUES (1,2),(1,5),(1,8),(2,5),(2,8),(2,9),(3,2),(3,5),(3,8),(3,10),(4,2),(4,5),(4,8),(5,2),(5,5),(5,8),(6,2),(6,4),(6,5),(6,7),(7,2),(7,3),(7,10),(8,1),(8,3),(8,5),(8,6),(9,4),(9,8),(9,9),(9,10),(10,1),(10,3),(10,8);
INSERT INTO application(job_id,user_id,status,applied_on) VALUES (1,9,'hired','2026-10-05'),(1,10,'shortlisted','2026-10-08'),(1,11,'applied','2026-10-06'),(1,13,'rejected','2026-10-18'),(1,14,'applied','2026-10-11'),(2,2,'shortlisted','2026-10-12'),(2,6,'rejected','2026-10-19'),(2,7,'shortlisted','2026-10-01'),(2,11,'hired','2026-10-13'),(2,12,'hired','2026-10-17'),(2,13,'shortlisted','2026-10-13'),(3,3,'rejected','2026-10-11'),(3,10,'applied','2026-10-16'),(3,16,'rejected','2026-10-19'),(4,3,'rejected','2026-10-05'),(4,9,'shortlisted','2026-10-03'),(4,15,'rejected','2026-10-08'),(4,17,'hired','2026-10-13'),(5,5,'hired','2026-10-14'),(5,9,'rejected','2026-10-01'),(5,10,'shortlisted','2026-10-02'),(5,12,'hired','2026-10-23'),(5,16,'hired','2026-10-19'),(6,7,'hired','2026-10-01'),(6,13,'applied','2026-10-13'),(6,14,'hired','2026-10-15'),(6,15,'shortlisted','2026-10-04'),(7,8,'shortlisted','2026-10-05'),(7,9,'shortlisted','2026-10-17'),(7,11,'applied','2026-10-23'),(7,12,'hired','2026-10-03'),(7,17,'applied','2026-10-01'),(7,19,'shortlisted','2026-10-08'),(8,2,'applied','2026-10-21'),(8,13,'rejected','2026-10-05'),(8,18,'rejected','2026-10-17'),(8,20,'hired','2026-10-23'),(9,5,'applied','2026-10-04'),(9,13,'applied','2026-10-10'),(9,18,'shortlisted','2026-10-13');
