import os
import io
import csv
import requests
from flask import url_for, current_app, redirect
from playwright.sync_api import Playwright, sync_playwright
from database import add_user, update_status, update_name, add_image
from models import Contact, Image


def get_file_extension(filename):
    ext = filename.rsplit('.', 1)[-1].lower()
    return ext


def save_image(file):
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    image_filename = "picture.jpg"
    image_path = os.path.join(upload_folder, image_filename)
    file.save(image_path)
    return url_for("static", filename=f"uploads/{image_filename}")


def save_image_from_url(image_url):
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    image_filename = "picture.jpg"
    image_path = os.path.join(upload_folder, image_filename)
    response = requests.get(image_url)
    if response.status_code == 200:
        with open(image_path, "wb") as f:
            f.write(response.content)
    else:
        raise Exception(
            f"Не удалось скачать изображение: HTTP {response.status_code}")

    return url_for("static", filename=f"uploads/{image_filename}")


def save_images(file):
    added, skipped = 0, 0
    category_name = os.path.basename(file.filename).split('.')[0]
    print(category_name)
    file_content = file.read().decode("utf-8")
    file_io = io.StringIO(file_content)
    for row in file_io:
        if not row.startswith("http"):
            continue
        image = Image(url=row.strip(), category=category_name)
        if add_image(image):
            added += 1
        else:
            skipped += 1
    return f"Loaded {added} new images. {skipped} already existing."


def save_numbers(file):
    added, skipped = 0, 0
    file_content = file.read().decode("utf-8")
    file_io = io.StringIO(file_content)
    reader = csv.reader(file_io)
    next(reader, None)

    for row in reader:
        if not row or not row[0].strip():
            continue
        phone = row[0].strip()
        contact = Contact(phone=phone)
        if add_user(contact):
            added += 1
        else:
            skipped += 1
    return f"Loaded {added} new numbers. {skipped} already existing."


def read_image():
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    image_path = os.path.join(upload_folder, "picture.jpg")
    return url_for("static", filename="uploads/picture.jpg") if os.path.exists(image_path) else None


def delete_image():
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    image_path = os.path.join(upload_folder, "picture.jpg")
    if os.path.exists(image_path):
        os.remove(image_path)
    return redirect(url_for('index'))


def send_message(contact, picture_path, text_message, search_box, page):
    search_box.click()
    search_box.fill(contact.phone)
    search_box.press("Enter")

    if contact.name == None:
        try:
            name = page.locator(
                '//*[@id="main"]/header/div[2]/div/div/div/div/span').text_content()
            update_name(contact.phone, name)
        except:
            update_status(contact.phone, "error")
            return False

    page.get_by_role("button", name="Прикрепить").click()
    page.locator("(//input[@type='file'])[2]").set_input_files(picture_path)

    text_field = page.get_by_role("textbox", name="Добавьте подпись")
    text_field.click()
    text_field.fill(text_message)

    # page.get_by_role("button", name="Отправить").click()
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


def get_display_numbers(data):
    return [f"[{contact.status.upper()}] {contact.name or 'Без имени'} - {contact.phone}" for contact in data]
