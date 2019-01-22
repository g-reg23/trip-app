import datetime


def has_upper(string):
    return any(elem.isupper() for elem in string)

def has_lower(string):
    return any(elem.islower() for elem in string)

def has_digit(string):
    return any(elem.isdigit() for elem in string)

def check_length_min(string, length):
    if len(string) >= length:
        return True
    else:
        return False

def check_length_max(string, length):
    if len(string) <= length:
        return True
    else:
        return False

def date_check(date_string):
    try:
        date_format = '%Y-%m-%d'
        date_obj = datetime.datetime.strptime(date_string, date_format)
        return True
    except ValueError:
        return False

def dates_are_possible(start_date, end_date):
    if date_in_future(start_date) and date_in_future(end_date) and start_before_end(start_date, end_date):
        return True
    else:
        return False

def date_in_future(date):
    date_format = '%Y-%m-%d'
    today = datetime.datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    if datetime.datetime.strptime(date, date_format) >= today:
        return True
    else:
        return False

def start_before_end(start, end):
    date_format = '%Y-%m-%d'
    if datetime.datetime.strptime(start, date_format) < datetime.datetime.strptime(end, date_format):
        return True
    else:
        return False
