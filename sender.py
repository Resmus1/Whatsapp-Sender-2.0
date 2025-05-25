from playwright.sync_api import Playwright
from database import db
from utils import process_text_message


def open_whatsapp(playwright: Playwright):
    browser = playwright.chromium.launch_persistent_context(
        user_data_dir="profile",
        headless=False,
        args=[
            "--disable-application-cache",
            "--disk-cache-size=1",
            "--start-maximized"
        ]
    )
    page = browser.pages[0] if browser.pages else browser.new_page()
    page.goto("https://web.whatsapp.com/")
    return page


def send_message(contact, picture_path, text_message, search_box, page):
    search_box.click()
    search_box.fill(contact.phone)
    search_box.press("Enter")

    if contact.name == None:
        try:
            name = page.locator(
                '//*[@id="main"]/header/div[2]/div/div/div/div/span').text_content()
            db.update_name(contact.phone, name)
        except Exception as e:
            print(f"Ошибка при получении имени контакта {contact.phone}: {e}")
            db.update_status(contact.phone, "error")
            return False

    page.get_by_role("button", name="Прикрепить").click()
    page.locator("(//input[@type='file'])[2]").set_input_files(picture_path)

    process_text_message(text_message, page)

    page.get_by_role("button", name="Отправить").click()
    page.wait_for_timeout(1000)
    db.update_status(contact.phone, "sent")


def close_browser(playwright):
    playwright.stop()
