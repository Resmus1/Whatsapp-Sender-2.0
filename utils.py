import os
import csv
from flask import url_for, current_app
from playwright.sync_api import Playwright, sync_playwright
from database import add_number, get_all_data, update_name, update_status



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
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    csv_path = os.path.join(upload_folder, "numbers.csv")
    file.save(csv_path)

    added = 0
    skipped = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            number = row[0].strip()
            if not number:
                continue
            if add_number(number):
                added += 1
            else:
                skipped += 1
        return f"Loaded {added} new numbers.The {skipped} already existing."


def read_image():
    image_url = None
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    image_path = os.path.join(upload_folder, "picture.jpg")

    if os.path.exists(image_path):
        image_url = url_for("static", filename=f"uploads/picture.jpg")

    return image_url


def send_message(data, picture_path, text_message, search_button, page):
    search_button.click()
    search_button.fill(data["phone"])
    search_button.press("Enter")
    if data["name"] == None:
        name = page.locator('//*[@id="main"]/header/div[2]/div/div/div/div/span').text_content()
        update_name(data["phone"], name)
    page.get_by_role("button", name="Прикрепить").click()
    page.locator("(//input[@type='file'])[2]").set_input_files(picture_path)

    text_field = page.get_by_role("textbox", name="Добавьте подпись")
    text_field.click()
    text_field.fill(text_message)
    update_status(data["phone"], "sent")

    page.get_by_role("button", name="Отправить").click()

    page.wait_for_timeout(3000)

def open_whatsapp(playwright: Playwright):
    context = playwright.chromium.launch_persistent_context(
        user_data_dir = "profile",
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
