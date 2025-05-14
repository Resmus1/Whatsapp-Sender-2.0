from tinydb import TinyDB, Query
from models import Contact

db = TinyDB('database.json')
Contacts_db = Query()

def add_user(user):
    if not db.contains(Contacts_db.phone == user.phone):
        db.insert(user.to_dict())
        return True
    return False


def get_all_users():
    return [Contact.from_dict(contact) for contact in db.all()]

def reset_sent_statuses():
    for contact in db.search(Contacts_db.status == 'sent'):
        db.update({'status': 'pending'}, Contacts_db.phone == contact['phone'])


def get_users_by_status(status):
    users_data = db.search(Contacts_db.status == status)
    return [Contact.from_dict(user) for user in users_data]


def update_status(phone, new_status):
    db.update({'status': new_status}, Contacts_db.phone == phone)

def update_name(phone, name):
    db.update({'name': name}, Contacts_db.phone == phone)