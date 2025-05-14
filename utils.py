import os
import csv
from flask import url_for, current_app
from playwright.sync_api import Playwright, sync_playwright
from database import add_user, get_all_users, get_users_by_status, update_status, update_name
from models import Contact


def allowed_file(filename):
    ext = filename.rsplit('.', 1)[-1].lower()
    allowed = current_app.config["ALLOWED_EXTENSIONS"]
    return ext in allowed, ext


def save_image(file):
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    image_filename = "picture.jpg"
    image_path = os.path.join(upload_folder, image_filename)
    file.save(image_path)
    return url_for("static", filename=f"uploads/{image_filename}")


def save_numbers(file):
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], "numbers.csv")
    file.save(path)

    added, skipped = 0, 0
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
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
    image_url = None
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    image_path = os.path.join(upload_folder, "picture.jpg")

    if os.path.exists(image_path):
        image_url = url_for("static", filename=f"uploads/picture.jpg")

    return image_url


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
            print(f"Failed to get name for {contact.phone}: {e}")

    page.get_by_role("button", name="Прикрепить").click()
    page.locator("(//input[@type='file'])[2]").set_input_files(picture_path)

    text_field = page.get_by_role("textbox", name="Добавьте подпись")
    text_field.click()
    text_field.fill(text_message)
    update_status(contact.phone, "sent")

    # page.get_by_role("button", name="Отправить").click()
    page.wait_for_timeout(2000)


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
    return [f"{contact.status}  {contact.name} - {contact.phone}" for contact in data]