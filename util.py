import uuid
from datetime import datetime

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def generate_uuid():
    return uuid.uuid4()


def get_timestamp():
    date_time_formatted = datetime.now().strftime("%d %m %Y %H:%M:%S")
    return date_time_formatted


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
