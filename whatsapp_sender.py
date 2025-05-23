import os
from playwright.sync_api import sync_playwright
from database import update_name, update_status
from utils import process_text_message


def open_whatsapp(playwright):
    browser = playwright.chromium.launch(
        headless=False)  # Запуск браузера с UI
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://web.whatsapp.com")
    print("Откройте WhatsApp Web и просканируйте QR код, если потребуется.")
    return page


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

    # page.get_by_role("button", name="Отправить").click()
    page.wait_for_timeout(1000)
    update_status(contact.phone, "sent")


def close_browser(playwright):
    playwright.stop()
