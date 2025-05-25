import os
import random
import requests
from flask import url_for, redirect, current_app, session, g
from database import db
from models import Contact, Image
from collections import Counter


def file_processing(file):
    ext = file.filename.rsplit('.')[-1].lower()

    if ext == "txt":
        file_name = os.path.basename(file.filename).split('.')[0]
        file_content = file.read().decode("utf-8")
        file_content = [row.strip()
                        for row in file_content.split('\n') if row.strip()]
        if all(row.isdigit() for row in file_content):
            status = save_numbers(file_content)
        if all(row.startswith("http") for row in file_content):
            status = save_images(file_content, file_name)
    elif ext == "jpg":
        status = save_image(file)
    else:
        return "Unsupported file type."
    return status


def save_image_to_disk(image_bytes):
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    image_filename = "picture.jpg"
    image_path = os.path.join(upload_folder, image_filename)

    with open(image_path, "wb") as f:
        f.write(image_bytes)

    session["image_path"] = url_for(
        "static", filename=f"uploads/{image_filename}")
    return "Image uploaded."


def save_image(file):
    return save_image_to_disk(file.read())


def save_image_from_url(current_image_url):
    response = requests.get(current_image_url)
    if response.status_code == 200:
        return save_image_to_disk(response.content)
    else:
        raise Exception(
            f"Не удалось скачать изображение: HTTP {response.status_code}")


def save_images(file_content, file_name):
    added, skipped = 0, 0
    for link_image in file_content:
        image = Image(url=link_image.strip(), category=file_name)
        if db.add_image(image):
            added += 1
        else:
            skipped += 1
    return f"Loaded {added} new images. {skipped} already existing."


def save_numbers(numbers):
    added, skipped = 0, 0

    for phone_number in numbers:
        contact = Contact(phone=phone_number)
        if db.add_user(contact):
            added += 1
        else:
            skipped += 1

    return f"Loaded {added} new numbers. {skipped} already existing."


def read_image():
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    image_path = os.path.join(upload_folder, "picture.jpg")

    if os.path.exists(image_path):
        return url_for("static", filename="uploads/picture.jpg")
    return None



def delete_image(url):
    db.delete_image(url)


def process_text_message(text_message, page):
    text_field = page.get_by_role("textbox", name="Добавьте подпись")
    text_field.click()
    lines = text_message.split("\\n")

    if len(text_message) > 1:
        for line in lines:
            if line and line != lines[-1]:
                text_field.type(line)
                page.keyboard.press("Shift+Enter")
            else:
                text_field.type(line)
    else:
        text_field.fill(text_message)


def get_display_numbers(users):
    return [
        {
            "number": getattr(user, "phone"),
            "name": getattr(user, "name"),
            "status": getattr(user, "status"),
        }
        for user in users
    ]


def counter_statuses(contacts):
    if not contacts:
        return {}
    return dict(Counter([contact.status for contact in contacts if contact.status is not None]))


def select_next_image(selected_category, current_url=None):
    images = db.get_images_by_category(
        selected_category) if selected_category else db.get_all_images()
    if not images:
        return None

    if current_url:
        filtered_images = [img for img in images if img.url != current_url]
        if filtered_images:
            return random.choice(filtered_images).url
        else:
            return current_url
    else:
        return random.choice(images).url


def update_image_length():
    selected_category = session.get("selected_category")
    if selected_category:
        length = len(db.get_images_by_category(selected_category))
    else:
        length = 0
    return length


def init_session():
    session["image_directory_path"] = read_image()
    session["text_message"] = session.get("text_message", "")
    session["selected_category"] = session.get("selected_category", None)
    g.data = db.get_all_users() or []
    session["statuses"] = counter_statuses(g.data)
    session["categories"] = db.get_image_categories()
    session["length"] = update_image_length()


def change_status(phone, status):
    db.update_status(phone, status)
    session["statuses"] = counter_statuses(g.data)


def delete_number(phone):
    db.delete_user(phone)
    session["statuses"] = counter_statuses(g.data)


def add_number_to_db(phone):
    contact = Contact(phone=phone)
    db.add_user(contact)
    session["statuses"] = counter_statuses(g.data)


def process_phone_number(phone):
    cleaned = phone.replace(" ", "").replace(
        "-", "").replace("(", "").replace(")", "").replace(".", "").strip()
    if cleaned.startswith("+7"):
        cleaned = cleaned[2:]
    elif cleaned.startswith("8"):
        cleaned = cleaned[1:]
    return cleaned


def go_home_page(message):
    return redirect(url_for('index', message=message))
