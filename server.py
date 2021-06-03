from flask import Flask, render_template, url_for, redirect, request, session
import os
import data_handler as dh
import logging
from werkzeug.utils import secure_filename
import util
from werkzeug.security import generate_password_hash, check_password_hash
import string
import random

app = Flask(__name__)

UPLOAD_FOLDER = './static/'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = ''.join(random.choices(string.ascii_uppercase
                                                  + string.digits
                                                  + string.ascii_lowercase
                                                  + string.punctuation, k=100))


@app.route("/")
@app.route('/index')
def index():
    user = dh.get_logged_in_user()

    return render_template('index.html', user=user)


@app.route('/questions', methods=['GET', 'POST'])
def questions():
    user = dh.get_logged_in_user()

    questions_data = dh.get_all_questions()

    return render_template('questions.html',
                           questions_data=questions_data, user=user)


@app.route('/sort_questions', methods=['POST'])
def sort_questions():
    sort_by = request.form['sort_question']
    by_order = request.form['by_order']
    print(sort_by, by_order)

    return redirect(url_for('questions'))


def append_count_to_users_data(dictionary_main: dict,
                               dictionary_secondary: dict,
                               q_a_c):
    """
    Function created purely for function `users()`.
    It reduces length of code in there by calling for loop
    with passed arguments.

    :return: dictionary with appended data
    """
    variety = {'q': 'count_question',
               'a': 'count_answer',
               'c': 'count_comment'}
    for record in dictionary_main:
        record.update([(variety[q_a_c], 0)])
        for rec in dictionary_secondary:
            if record['user_name'] == rec['user_name']:
                record.update([(variety[q_a_c], rec['count'])])
    return dictionary_main


@app.route('/user_page/<user_id>')
def user_page(user_id: int):
    user = dh.get_logged_in_user()
    return render_template('user_page.html',
                           user_data=user)


@app.route('/users')
def users():
    """
    Get all users' data and pass it to html to fill the required table.

    :return: users' data
    """
    user = dh.get_logged_in_user()

    """ Reputation. get data of all users, secondly iterate over them to get
        voted_up and voted_down."""
    """ voted_up and voted_down from table `users` will be stored in dictionary
        below, if no data for particular user it will be filled with zeros,
        user_id will be stored too but with no reason( just training GROUP BY)"""
    v_up_down_dict = {}
    users_data = dh.get_all_users()
    for row in users_data:
        v_up_down_dict[row['user_id']] = dh.get_vote_numbers(user_id=row['user_id'])
        if v_up_down_dict[row['user_id']] is None:
            v_up_down_dict[row['user_id']] = {'voted_up': 0, 'voted_down': 0}
    """ calculate reputation points for each user by adding columns voted_up
        and voted_down """
    users_reputation = {}
    for record in v_up_down_dict:
        users_reputation[record] = (v_up_down_dict[record]['voted_up'] * 5) - \
                                   (v_up_down_dict[record]['voted_down'] * 2)

    count_q, count_a, count_c = dh.get_count_q_a_c_grouped()

    # count is questions, answers and comments counted
    append_count_to_users_data(users_data, count_q, 'q')
    append_count_to_users_data(users_data, count_a, 'a')
    append_count_to_users_data(users_data, count_c, 'c')

    """ append reputation to `users_data` """
    for row in users_data:
        row.update([('reputation', 0)])
        for rec in users_reputation:
            if row['user_id'] == rec:
                row.update([('reputation', users_reputation[rec])])

    return render_template('users.html',
                           users_data=users_data,
                           user=user)


@app.route('/question/<int:question_id>')
def question(question_id: int):
    user = dh.get_logged_in_user()

    if question_id == '':
        return redirect('questions')

    question_data = dh.get_question_by_id(question_id=question_id)
    answers_for_question_data = dh.get_answers_for_question(question_id=question_id)
    comments_for_question_data = dh.get_comments_for_question(question_id=question_id)

    """ testing (to be removed) """
    # my_data_for_question = dh.get_question_with_answers(question_id=question_id)
    # for record in my_data_for_question:
    #     print(record)

    """ get only those comments which have `answer_id`s 
        for the given question, for do do that we need to extract ids 
        of the answers and next pass them as arguments for function responsible 
        for getting comments for answer by `answer_id` of the comment"""
    comments_for_answers_dict = {}
    for answer in answers_for_question_data:
        comments_for_answers_dict[answer['id']] = dh.get_comments_for_answer(
            answer_id=answer['id'])
        if len(comments_for_answers_dict[answer['id']]) == 0:
            del (comments_for_answers_dict[answer['id']])

    return render_template('question.html',
                           question_data=question_data,
                           answers=answers_for_question_data,
                           comments_for_question=comments_for_question_data,
                           comments_for_answers_dict=comments_for_answers_dict,
                           user=user)


def get_image():
    image = ''
    if 'image' in request.files:
        print('FOUND FILE')

        file = request.files['image']
        if file and util.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            return path


@app.route('/new-answer', methods=['GET', 'POST'])
def add_question():
    user = dh.get_logged_in_user()

    if request.method == 'POST':
        title = request.form['title']
        message = request.form['message']
        if not user:
            return '<h2>error</h2>'
        user_id = user['user_id']
        image = get_image()

        dh.add_question(title=title,
                        message=message,
                        user_id=user_id,
                        image=image)
        question_data = dh.get_latest_question()
        dh.add_question_vote(question_id=question_data['id'])

        return redirect(url_for(
            'question',
            question_id=question_data['id']))

    return render_template('add_question.html', user=user)


@app.route('/question/<question_id>/edit', methods=['GET', 'POST'])
def edit_question(question_id):
    user = dh.get_logged_in_user()

    if request.method == 'POST':
        # question_data = data_handler.get_question_by_id(question_id)
        image = get_image()

        new_title = request.form['title']
        new_message = request.form['message']

        dh.edit_question(question_id, new_title, new_message, image)

        return redirect(url_for('question', question_id=question_id))

    question_data = dh.get_question_by_id(question_id)
    return render_template('edit_question.html',
                           question_id=question_id,
                           title=question_data['title'],
                           message=question_data['message'],
                           user=user)


@app.route('/question/<question_id>/delete')
def delete_question(question_id):
    user = dh.get_logged_in_user()

    # TODO delete tags for question ID

    answers = dh.get_answers_for_question(question_id)
    for answer in answers:
        comments_for_answers = dh.get_comments_for_answer(answer['id'],
                                                          'answer')
        for comment in comments_for_answers:
            dh.delete_comment(comment['id'])

        dh.delete_answer(answer['id'])

    comments_for_question = dh.get_comments_for_question(question_id)
    for comment in comments_for_question:
        dh.delete_comment(comment['id'])

    dh.delete_question(question_id)

    return redirect(url_for('questions'))


@app.route('/question/<question_id>/new-answer', methods=['GET', 'POST'])
def add_answer(question_id):
    user = dh.get_logged_in_user()

    if request.method == 'POST':
        message = request.form['message']
        if not user:
            return '<h2>error</h2>'
        user_id = user['user_id']
        image = get_image()

        dh.add_answer(question_id=question_id,
                      message=message,
                      image=image,
                      user_id=user_id)

        return redirect(url_for('question', question_id=question_id))

    question_data = dh.get_question_by_id(question_id=question_id)

    return render_template('add_answer.html', question_dictionary=question_data,
                           user=user)


@app.route('/answer/<answer_id>/edit', methods=['GET', 'POST'])
def edit_answer(answer_id):
    """
    TODO: delete image when uploading new one.
    """
    user = dh.get_logged_in_user()

    answer_data = dh.get_answer_by_id(answer_id)
    question_data = dh.get_question_by_id(question_id=answer_data['question_id'])

    question_id = answer_data['question_id']

    # if there is POST form make an update
    if request.method == 'POST':
        image = get_image()

        new_message = request.form['message']

        dh.edit_answer(answer_id, new_message, image)

        return redirect(url_for('question', question_id=question_id))

    # else show form with answer data
    return render_template('edit_answer.html',
                           answer_data=answer_data,
                           question_dictionary=question_data,
                           user=user)


@app.route('/answer/<answer_id>/delete')
def delete_answer(answer_id):
    user = dh.get_logged_in_user()

    question_id = dh.get_answer_by_id(answer_id)['question_id']

    dh.delete_answer(answer_id)

    return redirect(url_for('question', question_id=question_id))


@app.route('/question/<question_id>/new-comment', methods=['GET', 'POST'])
def comment_question(question_id: int):
    user = dh.get_logged_in_user()

    question_data = dh.get_question_by_id(question_id)

    if request.method == 'POST':
        message = request.form['message']
        if not user:
            return '<h2>error</h2>'
        user_id = user['user_id']

        dh.add_comment_for_question(message, question_id, user_id)

        return redirect(url_for('question', question_id=question_id))
    else:
        return render_template('add_comment.html',
                               question_data=question_data,
                               user=user)


@app.route('/answer/<int:answer_id>/new-comment',
           methods=['GET', 'POST'])
def comment_answer(answer_id: int):
    user = dh.get_logged_in_user()

    answer_data = dh.get_answer_by_id(answer_id)
    question_id = answer_data['question_id']
    if not user:
        return '<h2>error</h2>'
    user_id = user['user_id']

    if request.method == 'POST':
        message = request.form['message']
        dh.add_comment_for_answer(message, answer_id, user_id)

        return redirect(url_for('question', question_id=question_id))
    else:
        return render_template('comment_answer.html',
                               answer_data=answer_data,
                               user=user)


@app.route('/q_comment/<comment_id>/edit', methods=['GET', 'POST'])
def edit_comment_for_question(comment_id):
    user = dh.get_logged_in_user()

    comment_data = dh.get_comment_by_id(comment_id)
    question_id = comment_data['question_id']

    if request.method == 'POST':
        message = request.form['message']
        dh.edit_comment(comment_id=comment_id, message=message)

        return redirect(url_for('question', question_id=question_id))

    return render_template('edit_comment_question.html',
                           comment_data=comment_data,
                           user=user)


@app.route('/a_comment/<comment_id>/edit', methods=['GET', 'POST'])
def edit_comment_for_answer(comment_id):
    user = dh.get_logged_in_user()

    comment_data = dh.get_comment_by_id(comment_id)
    question_id = dh.get_question_id_using_comment(comment_id)['id']

    if request.method == 'POST':
        message = request.form['message']
        dh.edit_comment(comment_id=comment_id, message=message)

        return redirect(url_for('question', question_id=question_id))

    return render_template('edit_comment_answer.html',
                           comment_data=comment_data,
                           user=user)


@app.route('/comments/<comment_id>/delete', methods=['GET'])
def delete_comment(comment_id):
    user = dh.get_logged_in_user()

    dh.delete_comment(comment_id=comment_id)

    return redirect(request.referrer)


@app.route('/question/<int:question_id>/<up_or_down>')
def vote_question(question_id: int, up_or_down: str):
    """
    Vote on answer, user presses vote up or down, the value from vote is passed to
    this function and is added to column `vote_number' in `answer` table.

    Set temp column in table `vote` which is needed for reputation.
    `dh.vote_reputation_question` it sets the columns voted_up and voted_down in table `vote`.

    :param question_id: id of the question
    :param up_or_down: 1 or -1, depends on whether pressed vote up or vote down,
            it's a `str`, it only gets converter in `data_handler_function.
    :return: redirect to `question`
    """
    user = dh.get_logged_in_user()

    dh.vote_question(question_id=question_id, value=up_or_down)
    dh.set_temp_question(question_id=question_id, value=up_or_down)
    dh.vote_reputation_question(question_id=question_id)

    return redirect(url_for('question', question_id=question_id))


@app.route('/answer/<int:answer_id>/<int:question_id> <up_or_down>')
def vote_answer(answer_id: int, question_id: int, up_or_down: str):
    """
    Vote on answer, user presses vote up or down, the value from vote is passed to
    this function and is added to column `vote_number' in `answer` table.

    :param answer_id: id of the answer
    :param question_id: id of the answer
    :param up_or_down: 1 or -1, depends on whether pressed vote up or vote down,
            it's a `str`, it only gets converter in `data_handler_function.
    :return: redirect to `question`
    """
    user = dh.get_logged_in_user()

    dh.vote_answer(answer_id=answer_id, value=up_or_down)

    return redirect(url_for('question', question_id=question_id))


@app.route('/comment/<int:comment_id>/<int:question_id> <up_or_down>')
def vote_comment(comment_id: int, question_id: int, up_or_down: str):
    """
    Vote on comment, user presses vote up or down, the value from vote is passed to
    this function and is added to column `vote_number' in `answer` table.

    :param comment_id: id of the comment
    :param question_id: id of the answer
    :param up_or_down: 1 or -1, depends on whether pressed vote up or vote down,
            it's a `str`, it only gets converter in `data_handler_function.
    :return: redirect to `question`
    """
    user = dh.get_logged_in_user()

    dh.vote_comment(comment_id=comment_id, value=up_or_down)

    return redirect(url_for('question', question_id=question_id))


@app.route('/search/')
def search():
    """
    Searching words typed by user.

    :return: GET - Page with type what to search for
             POST - Page with listed questions, answers or
             comments with searched phrase
    """
    user = dh.get_logged_in_user()

    searched_phrase = request.args.get("searched_phrase")
    search_result_question_title = dh.get_search_result_question_title(searched_phrase)
    search_result_question_message = dh.get_search_result_question_message(searched_phrase)
    search_result_answer_message = dh.get_search_result_answer_message(searched_phrase)
    search_result_comment_message = dh.get_search_result_comment_message(searched_phrase)

    return render_template('search.html',
                           searched_phrase=searched_phrase,
                           search_result_question_title=search_result_question_title,
                           search_result_question_message=search_result_question_message,
                           search_result_answer_message=search_result_answer_message,
                           search_result_comment_message=search_result_comment_message,
                           user=user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Create new user. User passes name, mail and password by filling the forms on
    '/register' page.

    :return: for 'GET' method render page with registration forms
            for 'POST' call function for creating new user.
    """
    user = dh.get_logged_in_user()

    if request.method == 'POST':
        user_name = request.form['user_name']
        is_user_in_db = dh.check_if_user_in_db(user_name)
        if is_user_in_db:
            return render_template('register.html',
                                   registration='already_in')

        email_address = request.form['email_address']
        is_mail_correct = dh.check_mail(email_address)
        is_mail_in_db = dh.check_if_mail_in_db(email_address)
        if is_mail_in_db:
            return render_template('register.html',
                                   registration='already_in')

        if not is_mail_correct:
            return render_template('register.html',
                                   registration='incorrect_mail')

        password_hashed = generate_password_hash(request.form['password'],
                                                 method='sha256')

        dh.register_user(user_name=user_name,
                         email_address=email_address,
                         password=password_hashed)

        return render_template('index.html',
                               registration_completed=True)

    return render_template('register.html',
                           user=user,
                           registration=None)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Log in user. Compare data provided by user with matching row in database.
    User is identified by `name`.
    Passwords are compared, if they match `session` is created. If they don't
    match user is notified about failure.

    :return: redirect to start page if user is logged in, render template with logging
            failure info for user.
    """
    user = dh.get_logged_in_user()

    if request.method == 'POST':
        user_name = request.form['user_name']
        is_user_in_db = dh.check_if_user_in_db(user_name)
        if not is_user_in_db:
            return render_template('login.html',
                                   login=0)

        password = request.form['password']
        user_data = dh.get_user_data(user_name=user_name)

        do_passwords_match = check_password_hash(user_data['password'], password)
        if do_passwords_match:
            session['user'] = user_data['user_name']
            return redirect('index')
        else:
            return render_template('index.html',
                                   user=0)

    return render_template('login.html',
                           user=user)


@app.route('/logout')
def logout():
    """
    log out user.

    :return: redirect to start page
    """
    session.pop("user", None)

    return redirect('index')


if __name__ == "__main__":
    app.run(debug=True)
