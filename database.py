from tinydb import TinyDB, Query
from models import Contact, Image
import json

db = TinyDB('database.json')
contact_table = db.table('contacts')
images_table = db.table('images')

Contacts = Query()
Images = Query()


def add_user(user):
    if not contact_table.contains(Contacts.phone == user.phone):
        contact_table.insert(user.to_dict())
        return True
    return False


def add_image(image):
    if not images_table.contains(Images.url == image.url):
        images_table.insert(image.to_dict())
        return True
    return False


def delete_db_image(url):
    images_table.remove(Images.url == url)


def get_all_users():
    try:
        contacts = contact_table.all()
        return [Contact.from_dict(contact) for contact in contacts]
    except json.JSONDecodeError:
        return []


def delete_db_user(phone):
    contact_table.remove(Contacts.phone == phone)


def get_all_images():
    try:
        images = images_table.all()
        return [Image.from_dict(image) for image in images]
    except json.JSONDecodeError:
        return []


def get_image_categories():
    return list(set(image.category for image in get_all_images()))


def get_images_by_category(category):
    return [image for image in get_all_images() if image.category == category]


def reset_sent_statuses():
    for contact in contact_table.search(Contacts.status == 'sent'):
        contact_table.update({'status': 'pending'},
                             Contacts.phone == contact['phone'])


def update_status(phone, new_status):
    contact_table.update({'status': new_status}, Contacts.phone == phone)


def update_name(phone, name):
    contact_table.update({'name': name}, Contacts.phone == phone)
