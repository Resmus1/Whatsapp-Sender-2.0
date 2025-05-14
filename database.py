from tinydb import TinyDB, Query

db = TinyDB('database.json')
Number = Query()

def add_number(phone):
    if not db.contains(Number.phone == phone):
        db.insert({'status': 'pending','name':None, 'phone': phone})
        return True
    return False


def get_all_data():
    return db.all()


def get_pending_numbers():
    return db.search(Number.status == 'pending')


def update_status(phone, new_status):
    db.update({'status': new_status}, Number.phone == phone)

def update_name(phone, name):
    db.update({'name': name}, Number.phone == phone)