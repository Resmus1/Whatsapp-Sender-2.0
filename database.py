from tinydb import TinyDB, Query
from models import Contact, Image

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


def get_all_users():
    return [Contact.from_dict(contact) for contact in contact_table.all()]


def get_all_images():
    return [Image.from_dict(image) for image in images_table.all()]


def get_image_by_category(category):
    return images_table.search(Images.category == category)


def reset_sent_statuses():
    for contact in db.search(Contacts.status == 'sent'):
        db.update({'status': 'pending'}, Contacts.phone == contact['phone'])


def update_status(phone, new_status):
    db.update({'status': new_status}, Contacts.phone == phone)


def update_name(phone, name):
    db.update({'name': name}, Contacts.phone == phone)
