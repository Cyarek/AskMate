HELLO!!!

*  ********************  *
*  ********************  *
*  **  ---------   ****  *
*  ** | Ask-mate | ****  *
*  **  ---------   ****  *
*  ********************  *
*  ********************  *

SQL for creating new tables and altering the old ones.

************************************** create the table for users *********************************************
CREATE TABLE users(
	user_id SERIAL PRIMARY KEY,
	user_name VARCHAR(20) UNIQUE NOT NULL,
	password VARCHAR(150) NOT NULL,
	email_address VARCHAR(60) UNIQUE NOT NULL,
	registration_date TIMESTAMP NOT NULL
)

************************************** insert something into that table  *********************************************
INSERT INTO users(user_name, password, email_address, registration_date)
VALUES
('quanti', 'abcdq', 'quanti@ww.gg', CURRENT_TIMESTAMP)


************************************** changing table comments  *********************************************
ALTER TABLE comment
ADD COLUMN vote_number INTEGER

************************************** adding column to table `question` *********************************************
ALTER TABLE question
ADD COLUMN user_id INTEGER NOT NULL DEFAULT 0

************************************** adding foreign key in `question` for `user_id` *********************************************
ALTER TABLE question
    ADD CONSTRAINT fk_question_users FOREIGN KEY (user_id) REFERENCES users (user_id);


new ones

************************************** change table `answer` by adding column `user_id` *********************************************
ALTER TABLE answer
ADD COLUMN user_id INTEGER NOT NULL DEFAULT 0 REFERENCES users(user_id)


************************************** change table `comment` by adding column `user_id` *********************************************
ALTER TABLE comment
ADD COLUMN user_id INTEGER NOT NULL DEFAULT 0 REFERENCES users(user_id)


newer ones
************************************** create table `vote` *********************************************
CREATE TABLE vote(
	vote_id SERIAL PRIMARY KEY,
	question_id INTEGER REFERENCES question(id),
	answer_id INTEGER REFERENCES answer(id),
	comment_id INTEGER REFERENCES comment(id),
	voted_up, INTEGER DEFAULT 0,
	voted_down, INTEGER DEFAULT 0,
	
)


**************************************  change table `users`  *********************************************
ALTER TABLE users
ADD COLUMN reputation_points INTEGER DEFAULT 0

new
**************************************  change table `users`  *********************************************
ALTER TABLE vote
ADD COLUMN temp VARCHAR(2)