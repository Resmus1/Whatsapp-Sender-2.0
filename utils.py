import os
import io
import random
import requests
from flask import url_for, current_app, redirect, session, g
from playwright.sync_api import Playwright, sync_playwright
from database import get_all_users, add_user, update_status, update_name, add_image, delete_db_image, get_images_by_category, get_all_images, get_image_categories, delete_db_user
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
        return ext, "Unsupported file type."
    return ext, status


def save_image(file):
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    image_filename = "picture.jpg"
    image_path = os.path.join(upload_folder, image_filename)
    file.save(image_path)
    session["image_path"] = url_for(
        "static", filename=f"uploads/{image_filename}")
    return "Image uploaded."


def save_image_from_url(current_image_url):
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    image_filename = "picture.jpg"
    image_path = os.path.join(upload_folder, image_filename)

    response = requests.get(current_image_url)
    if response.status_code == 200:
        with open(image_path, "wb") as f:
            f.write(response.content)
    else:
        raise Exception(
            f"Не удалось скачать изображение: HTTP {response.status_code}")

    return url_for("static", filename=f"uploads/{image_filename}")


def save_images(file_content, file_name):
    added, skipped = 0, 0
    for link_image in file_content:
        image = Image(url=link_image.strip(), category=file_name)
        if add_image(image):
            added += 1
        else:
            skipped += 1
    return f"Loaded {added} new images. {skipped} already existing."


def save_numbers(numbers):
    added, skipped = 0, 0

    for phone_number in numbers:
        contact = Contact(phone=phone_number)
        if add_user(contact):
            added += 1
        else:
            skipped += 1

    return f"Loaded {added} new numbers. {skipped} already existing."


def read_image():
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    image_path = os.path.join(upload_folder, "picture.jpg")
    return url_for("static", filename="uploads/picture.jpg") if os.path.exists(image_path) else None


def delete_image(url):
    delete_db_image(url)


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


def send_message(contact, picture_path, text_message, search_box, page):
    search_box.click()
    search_box.fill(contact.phone)
    search_box.press("Enter")

    if contact.name == None:
        try:
            name = page.locator(
                '//*[@id="main"]/header/div[2]/div/div/div/div/span').text_content()
            update_name(contact.phone, name)
        except Exception as e:
            print(f"Ошибка при получении имени контакта {contact.phone}: {e}")
            update_status(contact.phone, "error")
            return False

    page.get_by_role("button", name="Прикрепить").click()
    page.locator("(//input[@type='file'])[2]").set_input_files(picture_path)

    process_text_message(text_message, page)

    page.get_by_role("button", name="Отправить").click()
    page.wait_for_timeout(1000)
    update_status(contact.phone, "sent")


def open_whatsapp(playwright: Playwright):
    context = playwright.chromium.launch_persistent_context(
        user_data_dir="profile",
        headless=False,
        args=[
            "--disable-application-cache",
            "--disk-cache-size=1",
            "--start-maximized"
        ]
    )
    page = context.new_page()
    page.goto("https://web.whatsapp.com/")
    return page


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
    images = get_images_by_category(
        selected_category) if selected_category else get_all_images()
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
        length  = len(get_images_by_category(selected_category))
    else:
        length  = 0
    return length

def init_session():
    if "image_directory_path" not in session:
        session["image_directory_path"] = read_image()
    session["image_path"] = session.get("image_path", None)
    session["text_message"] = session.get("text_message", "")
    g.data = get_all_users() or []
    session["statuses"] = counter_statuses(g.data)
    session["categories"] = get_image_categories()
    session["length"] = update_image_length()


def change_status(phone, status):
    update_status(phone, status)
    session["statuses"] = counter_statuses(g.data)

def delete_number(phone):
    delete_db_user(phone)
    session["statuses"] = counter_statuses(g.data)