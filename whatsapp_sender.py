import os
from playwright.sync_api import sync_playwright

def open_whatsapp(playwright):
    browser = playwright.chromium.launch(headless=False)  # Запуск браузера с UI
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://web.whatsapp.com")
    print("Откройте WhatsApp Web и просканируйте QR код, если потребуется.")
    return page

def send_message(contact, picture_path, text_message, search_box, page):
    """
    Отправляет сообщение контактам в WhatsApp.

    contact - объект с info о контакте, должен иметь contact.name и contact.status
    picture_path - путь к файлу изображения
    text_message - текст сообщения
    search_box - элемент поиска на странице WhatsApp
    page - страница Playwright
    """
    # Вводим имя контакта в поиск и выбираем чат
    search_box.fill(contact.name)
    search_box.press("Enter")

    # Ждем, пока чат загрузится
    page.wait_for_selector("div[contenteditable='true'][data-tab='10']")  # Поле ввода текста

    # Если есть текстовое сообщение — вводим
    if text_message:
        message_box = page.locator("div[contenteditable='true'][data-tab='10']")
        message_box.fill(text_message)

    # Прикрепляем и отправляем изображение
    if os.path.exists(picture_path):
        # Нажимаем кнопку "прикрепить"
        page.click("span[data-icon='clip']")
        # Вводим путь к файлу в input[type='file']
        page.set_input_files("input[type='file']", picture_path)
        page.wait_for_timeout(1000)  # Ждем загрузку изображения
        # Отправляем
        page.click("span[data-icon='send']")
    else:
        # Если картинки нет — отправляем только текст
        if text_message:
            page.click("span[data-icon='send']")

    # Обновляем статус контакта (этот код ты должен реализовать в utils или БД)
    contact.status = "sent"
    print(f"Сообщение отправлено: {contact.name}")

def close_browser(playwright):
    playwright.stop()
