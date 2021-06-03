import connection
import util
from flask import session
import re

DATA_HEADER = ['id',
               'submission_time',
               'view_number',
               'vote_number',
               'title',
               'message',
               'image']


def get_headers():
    headers = []
    for header in DATA_HEADER:
        headers.append(header.replace('_', ' ').capitalize())
    return headers


@connection.connection_handler
def get_all_questions(cursor):
    cursor.execute("""
                        SELECT  id,
                                submission_time,
                                view_number,
                                vote_number,
                                title,
                                message,
                                image,
                                user_name
                        FROM question
                        INNER JOIN users
                        ON question.user_id = users.user_id
                        ORDER BY id
                        LIMIT 5
                       """)
    return cursor.fetchall()


@connection.connection_handler
def get_question_by_id(cursor, question_id):
    cursor.execute("""
                        SELECT  id,
                                submission_time,
                                view_number,
                                vote_number,
                                title,
                                message,
                                image,
                                user_name
                        FROM question
                        INNER JOIN users
                        ON question.user_id = users.user_id
                        WHERE id=%(id)s
                       """, {'id': question_id})
    return cursor.fetchone()


@connection.connection_handler
def get_latest_question(cursor):
    cursor.execute("""
                        SELECT * FROM question
                        ORDER BY id DESC
                        LIMIT 1
                        """)
    return cursor.fetchone()


@connection.connection_handler
def get_question_with_answers(cursor, question_id: int):
    query = """
                SELECT question.id as question_id,
                        question.view_number as question_view_number,
                        question.title as question_title,
                        question.message as question_message,
                        question.user_id as question_user_id,
                        answer.id as answer_id,
                        answer.message as answer_message
                FROM question
                INNER JOIN answer
                ON question.id = question_id
                WHERE question.id = %(question_id)s
        """
    cursor.execute(query, {'question_id': question_id})
    return cursor.fetchmany()


@connection.connection_handler
def add_question(cursor, title: str, message: str, user_id: int, image='') -> bool:
    submission_time = str(util.get_timestamp())
    image = image

    query = """
                    INSERT INTO question (
                    submission_time,
                    view_number,
                    vote_number,
                    title,
                    message,
                    image,
                    user_id)
                    VALUES (
                    %(submission_time)s,
                    %(view_number)s,
                    %(vote_number)s,
                    %(title)s,
                    %(message)s,
                    %(image)s,
                    %(user_id)s)
                               """

    cursor.execute(query, {'submission_time': submission_time,
                           'view_number': 0,
                           'vote_number': 0,
                           'title': title,
                           'message': message,
                           'image': image,
                           'user_id': user_id})
    # cursor.lastrowid
    return True


@connection.connection_handler
def add_question_vote(cursor, question_id: int) -> bool:
    """
    Fill table vote for brand new question.

    :param cursor:
    :param question_id: id of the just added question
    """
    query = """
                    INSERT INTO vote(
                    question_id,
                    voted_up,
                    voted_down)
                    VALUES (
                    %(question_id)s,
                    0,
                    0)
                               """

    cursor.execute(query, {'question_id': question_id})
    return True


@connection.connection_handler
def edit_question(cursor, question_id, new_title, new_message, new_image):
    query = """
            UPDATE question
            SET title = %(new_title)s,
                message = %(new_message)s,
                image= %(new_image)s
            WHERE id = %(question_id)s        
    """

    cursor.execute(query, {'question_id': question_id,
                           'new_title': new_title,
                           'new_message': new_message,
                           'new_image': new_image})


@connection.connection_handler
def delete_question(cursor, id: int):
    query = """
            DELETE FROM question
            WHERE id=%(id)s
                       """

    cursor.execute(query, {'id': id})

    return True


@connection.connection_handler
def get_all_answers(cursor):
    cursor.execute("""
                        SELECT * FROM answer
                       """)
    return cursor.fetchall()


@connection.connection_handler
def get_answer_by_id(cursor, answer_id):
    cursor.execute("""
                        SELECT * FROM answer
                        WHERE id=%(id)s
                       """, {'id': answer_id})
    return cursor.fetchone()


@connection.connection_handler
def get_answers_for_question(cursor, question_id):
    cursor.execute("""
                        SELECT  id,
                                submission_time,
                                vote_number,
                                message,
                                image,
                                user_name
                        FROM answer
                        INNER JOIN users
                        ON answer.user_id = users.user_id
                        WHERE question_id=%(id)s
                        ORDER BY id
                       """, {'id': question_id})
    return cursor.fetchall()


@connection.connection_handler
def add_answer(cursor,
               message: str,
               question_id: int,
               image,
               user_id) -> bool:
    submission_time = str(util.get_timestamp())
    query = """
                INSERT INTO answer(
                            submission_time,
                            vote_number,
                            question_id,
                            message,
                            image,
                            user_id)
                VALUES (
                %(submission_time)s,
                %(vote_number)s,
                %(question_id)s,
                %(message)s,
                %(image)s,
                %(user_id)s
                )
            """
    cursor.execute(query, {'submission_time': submission_time,
                           'vote_number': 0,
                           'question_id': question_id,
                           'message': message,
                           'image': image,
                           'user_id': user_id})

    return True


@connection.connection_handler
def edit_answer(cursor, answer_id: int, new_message: str, new_image):
    if new_image != '':
        query = """
                UPDATE answer
                SET message = %(new_message)s, image= %(new_image)s
                WHERE id = %(answer_id)s        
        """
    else:
        query = """
                UPDATE answer
                SET message = %(new_message)s
                WHERE id = %(answer_id)s        
        """
    cursor.execute(
        query,
        {'new_message': new_message,
         'answer_id': answer_id,
         'new_image': new_image})


@connection.connection_handler
def delete_answer(cursor, answer_id: int) -> bool:
    query = """
            DELETE FROM answer
            WHERE id=%(answer_id)s
                       """

    cursor.execute(query, {'answer_id': answer_id})

    return True


@connection.connection_handler
def get_comments_for_question(cursor, question_id):
    query = """
            SELECT  id,
                    submission_time,
                    vote_number,
                    message,
                    user_name
            FROM comment
            INNER JOIN users
            ON comment.user_id = users.user_id
            WHERE question_id=%(question_id)s
            ORDER BY id
        """
    cursor.execute(query, {'question_id': question_id})
    return cursor.fetchall()


@connection.connection_handler
def get_comments_for_answer(cursor, answer_id):
    query = """
            SELECT  id,
                    submission_time,
                    vote_number,
                    message,
                    user_name 
            FROM comment
            INNER JOIN users
            ON comment.user_id = users.user_id
            WHERE answer_id=%(answer_id)s
            ORDER BY id
        """
    cursor.execute(query, {'answer_id': answer_id})
    return cursor.fetchall()


@connection.connection_handler
def get_comment_by_id(cursor, comment_id):
    query = """
            SELECT * FROM comment
            WHERE comment.id=%(comment_id)s
    """
    cursor.execute(query, {'comment_id': comment_id})

    return cursor.fetchone()


@connection.connection_handler
def get_question_id_using_comment(cursor, comment_id: int):
    """
    Get id of the question having only data from comment for answer, which means
    we have to double inner join to retrieve it, because comment doesn't have it
    but question do.

    :param cursor:
    :param comment_id: id of the given comment
    :return: desired id of the question
    """
    query = """
                SELECT question.id FROM question
                INNER JOIN answer
                ON question.id = answer.question_id
                INNER JOIN comment
                ON answer.id = comment.answer_id
                WHERE comment.id = %(comment_id)s
        """
    cursor.execute(query, {'comment_id': comment_id})

    return cursor.fetchone()


@connection.connection_handler
def add_comment_for_question(cursor, message, question_id, user_id):
    submission_time = util.get_timestamp()
    query = """
            INSERT INTO comment (
            question_id,
            message,
            submission_time,
            vote_number,
            user_id
            )
            VALUES (
            %(question_id)s,
            %(message)s,
            %(submission_time)s,
            %(vote_number)s,
            %(user_id)s
            )          
    """
    cursor.execute(query,
                   {'question_id': question_id,
                    'message': message,
                    'submission_time': submission_time,
                    'vote_number': 0,
                    'user_id': user_id
                    })
    return True


@connection.connection_handler
def add_comment_for_answer(cursor,
                           message: str,
                           answer_id: int,
                           user_id: int):
    submission_time = util.get_timestamp()

    query_for_answer = """
                    INSERT INTO comment (
                    answer_id,
                    message,
                    submission_time,
                    vote_number,
                    user_id
                    )
                    VALUES (
                    %(answer_id)s,
                    %(message)s,
                    %(submission_time)s,
                    %(vote_number)s,
                    %(user_id)s
                    )          
            """
    cursor.execute(query_for_answer,
                   {'answer_id': answer_id,
                    'message': message,
                    'submission_time': submission_time,
                    'vote_number': 0,
                    'user_id': user_id})
    return True


@connection.connection_handler
def edit_comment(cursor, comment_id, message):
    query = """
            UPDATE comment
            SET message = %(message)s, edited_count=COALESCE(edited_count, 0) + 1
            WHERE id=%(comment_id)s
    """
    cursor.execute(query, {'message': message, 'comment_id': comment_id})

    return True


@connection.connection_handler
def delete_comment(cursor, comment_id):
    query = """
            DELETE FROM comment
            WHERE id=%(id)s   
    """
    cursor.execute(query, {'id': comment_id})

    return True


@connection.connection_handler
def vote_question(cursor, question_id: int, value: str) -> bool:
    """
    Update row of the given question identified by its id
    with `vote_number` +1 or -1.

    :param cursor:
    :param question_id: id of the question
    :param value: 1 or -1, depends on whether user pressed vote up or vote down
    :return:
    """
    int(value)
    query = """
            UPDATE question
            SET vote_number = vote_number + %(value)s
            WHERE id = %(question_id)s
        """
    cursor.execute(query, {'value': value, 'question_id': question_id})

    return True


@connection.connection_handler
def set_temp_question(cursor, question_id: int, value: str) -> bool:
    """
    Set column `temp` cause it will be needed for CASE in query in function `vote_reputation_question`.

    :param cursor:
    :param question_id: id of the question
    :param value: vote up - 1, vote down - -1
    :return:
    """
    query = """
                    UPDATE vote
                    SET temp = %(value)s
                    WHERE question_id = %(question_id)s
                """
    cursor.execute(query, {'value': value, 'question_id': question_id})
    return True


@connection.connection_handler
def vote_reputation_question(cursor, question_id: int) -> bool:
    """
    Set voted_up and voted_down using column `temp`. These two columns will be needed further
    for calculating reputation points.

    :param cursor:
    :param question_id: id of the question
    """
    query = """
                UPDATE vote SET 
                voted_up = (CASE WHEN temp = '1' 
                            THEN voted_up + 1 
                            ELSE voted_up END),
                voted_down = (CASE WHEN temp = '-1' 
                              THEN voted_down + 1 
                              ELSE voted_down END)
                WHERE question_id = %(question_id)s
            """
    cursor.execute(query, {'question_id': question_id})
    return True


@connection.connection_handler
def vote_answer(cursor, answer_id: int, value: str) -> bool:
    """
    Update row of the given answer identified by its id
    with `vote_number` +1 or -1.

    :param cursor:
    :param answer_id: id of the answer
    :param value: 1 or -1, depends on whether user pressed vote up or vote down
    :return:
    """
    int(value)
    query = """
            UPDATE answer
            SET vote_number = vote_number + %(value)s
            WHERE id = %(answer_id)s
        """
    cursor.execute(query, {'value': value, 'answer_id': answer_id})

    return True


@connection.connection_handler
def vote_comment(cursor, comment_id: int, value: str) -> bool:
    """
    Update row of the given comment identified by its id
    with `vote_number` +1 or -1.

    :param cursor:
    :param comment_id: id of the comment
    :param value: 1 or -1, depends on whether user pressed vote up or vote down
    :return:
    """
    int(value)
    print(comment_id, 'comment id')
    print(value, 'value')
    query = """
            UPDATE comment
            SET vote_number = vote_number + %(value)s
            WHERE id = %(comment_id)s
        """
    cursor.execute(query, {'value': value, 'comment_id': comment_id})

    return True


@connection.connection_handler
def get_vote_numbers(cursor, user_id: int):
    query = """
            SELECT SUM(voted_up) as voted_up,
                    SUM(voted_down) as voted_down,
                    question.user_id
            FROM vote
            INNER JOIN question
            ON vote.question_id = question.id
            GROUP BY question.user_id
            HAVING question.user_id = %(user_id)s
    """
    cursor.execute(query, {'user_id': user_id})
    return cursor.fetchone()


@connection.connection_handler
def get_search_result_question_title(cursor, searched_data: str):
    """
    Get search result for phrase typed by user.

    :param cursor:
    :param searched_data: searched phrase
    :return: search result for searched phrase in title of the question
    """
    search_data_formatted = f"%{searched_data}%"
    query = """
            SELECT * FROM question
            WHERE title ILIKE %(search_data_formatted)s
    """
    cursor.execute(query, {'search_data_formatted': search_data_formatted})

    return cursor.fetchall()


@connection.connection_handler
def get_search_result_question_message(cursor, searched_data: str):
    """
    Get search result for phrase typed by user.

    :param cursor:
    :param searched_data: searched phrase
    :return: search result for searched phrase in message of the question
    """
    search_data_formatted = f"%{searched_data}%"
    query = """
            SELECT * FROM question
            WHERE message ILIKE %(search_data_formatted)s
    """
    cursor.execute(query, {'search_data_formatted': search_data_formatted})

    return cursor.fetchall()


@connection.connection_handler
def get_search_result_answer_message(cursor, searched_data: str):
    """
    Get search result for phrase typed by user.

    :param cursor:
    :param searched_data: searched phrase
    :return: search result for searched phrase in message of the answer
    """
    search_data_formatted = f"%{searched_data}%"
    query = """
            SELECT * FROM answer
            WHERE message ILIKE %(search_data_formatted)s
    """
    cursor.execute(query, {'search_data_formatted': search_data_formatted})

    return cursor.fetchall()


@connection.connection_handler
def get_search_result_comment_message(cursor, searched_data: str):
    """
    Get search result for phrase typed by user.

    :param cursor:
    :param searched_data: searched phrase
    :return: search result for searched phrase in message of the comment
    """
    search_data_formatted = f"%{searched_data}%"
    query = """
            SELECT * FROM comment
            WHERE message ILIKE %(search_data_formatted)s
    """
    cursor.execute(query, {'search_data_formatted': search_data_formatted})

    return cursor.fetchall()


@connection.connection_handler
def register_user(cursor,
                  user_name: str,
                  password: str,
                  email_address: str,
                  ) -> bool:
    """
    Register new user. User fills the form and the data is passed here to
    be inserted into table `users`.

    :param cursor:
    :param user_name: UNIQUE, NOT NULL, max 20 characters
    :param password: max 150 characters, hashed, NOT NULL
    :param email_address: UNIQUE, NOT NULL
    :return: True if data properly inserted into table users
    """
    query = """
            INSERT INTO users(
            user_name,
            password,
            email_address,
            registration_date
            )
            VALUES(
            %(user_name)s,
            %(password)s,
            lower(%(email_address)s),
            CURRENT_TIMESTAMP
            )
    """
    cursor.execute(query, {'user_name': user_name,
                           'password': password,
                           'email_address': email_address})
    return True


@connection.connection_handler
def get_user_data(cursor, user_name: str):
    """
    Extract user data using `unique` user_name, from database.

    :param cursor
    :param user_name: UNIQUE name provided by user in registration process.
    :return: One row with user data.
    """
    query = """
            SELECT * FROM users
            WHERE user_name = %(user_name)s
    """
    cursor.execute(query, {'user_name': user_name})

    return cursor.fetchone()


def get_logged_in_user():
    """
    Get info about current state of user being logged in. In addition to confirmation that
    user is logged in data of user from the database is returned.

    :return: user data if user is in session and `None` if user is not in session
    """
    user_data = None
    if 'user' in session:
        user = session['user']
        user_data = get_user_data(user_name=user)
    return user_data


def check_mail(mail: str) -> bool:
    """
    Check if email provided by user is a valid one.

    :param mail: email address provided by user
    :return: True or False
    """
    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if re.search(regex, mail):
        return True
    else:
        return False


@connection.connection_handler
def check_if_user_in_db(cursor, user_name: str) -> dict:
    """
    Check if user_name already in database.

    :param cursor:
    :param user_name: name provided by user
    :return: Dict, if empty - no user in db
    """
    query = """
            SELECT * FROM users
            WHERE user_name = %(user_name)s
    """
    cursor.execute(query, {'user_name': user_name})
    return cursor.fetchone()


@connection.connection_handler
def check_if_mail_in_db(cursor, email_address: str) -> dict:
    """
    Check if mail already in database.

    :param cursor:
    :param email_address: mail provided by user
    :return: Dict, if empty - no mail in db
    """
    query = """
            SELECT * FROM users
            WHERE email_address = %(email_address)s
    """
    cursor.execute(query, {'email_address': email_address})
    return cursor.fetchone()


@connection.connection_handler
def get_all_users(cursor):
    """
    Extract from db all users for `users.html` page, where the data will be used
    in the table there.

    :return: all users data
    """
    query = """
            SELECT * FROM users
            ORDER BY user_id
    """
    cursor.execute(query)

    return cursor.fetchall()


@connection.connection_handler
def get_count_questions(cursor):
    """
    Extract from db the count of users' questions.

    :return: count of users' questions
    """
    query = """
            SELECT COUNT(question.id), user_name 
            FROM question
            INNER JOIN users
            ON question.user_id = users.user_id
            GROUP BY user_name
    """
    cursor.execute(query)

    return cursor.fetchall()


@connection.connection_handler
def get_count_answers(cursor):
    """
    Extract from db the count of users' answers.

    :return: count of users' answers
    """
    query = """
            SELECT COUNT(answer.id), user_name 
            FROM answer
            INNER JOIN users
            ON answer.user_id = users.user_id
            GROUP BY user_name
    """
    cursor.execute(query)

    return cursor.fetchall()


@connection.connection_handler
def get_count_comments(cursor):
    """
    Extract from db the count of users' comments.

    :return: count of user's answers
    """
    query = """
            SELECT COUNT(comment.id), user_name 
            FROM comment
            INNER JOIN users
            ON comment.user_id = users.user_id
            GROUP BY user_name
    """
    cursor.execute(query)

    return cursor.fetchall()


def get_count_q_a_c_grouped():
    """
    Grouped functions for getting count od questions, answers and comments
    by user.
    Function created ust for simplification.

    :return: tuple od all data
    """
    return get_count_questions(), get_count_answers(), get_count_comments()
