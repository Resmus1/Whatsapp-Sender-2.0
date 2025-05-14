#!!! Разбить upload на несколько функций и добавить в них определение по файлу, мне нужно что бы загружало txt номера и jpg и выдавало статус о загрузке перенести разбитое в общие функции что бы здесь они не повторялись
# Добавить таймер на количество попыток входа и возврат в приложение
# Номера добавляются в базу данных и по отправки добавляются именна
# Создание статуса отправки напротив контакта
# Возврат к главной странице лишь с заменой статуса
# Растояние между номерами в спике
# Создание имен на основе имени и фамилии если нет в базе
# Создать кнопку сброса статуса
# Сделать табличку для контактов и галочку для рассылки возможностью добавить номер по отдельности или удалить
# Окошко для messege сделать пошире и комфортнее
# создать опцию выбора готовых картинок, а так же занесение их в базу данных для исключение повтора

import os
from flask import Flask, render_template, request, url_for, g
from playwright.sync_api import sync_playwright
from utils import allowed_file, read_image, save_image, save_numbers, send_message, open_whatsapp
from config import Config
from database import get_all_data


app = Flask(__name__)
app.config.from_object(Config)


os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

text_message = ""


@app.before_request
def before_request():
    g.data = get_all_data()
    g.image_url = read_image()

@app.route("/")
def index():
    return render_template("index.html", message="Old data", image_url=g.image_url, numbers=[f"{item['status']}  {item['name']} - {item['phone']}" for item in g.data])


@app.route("/start")
def start():
    with sync_playwright() as p:
        page = open_whatsapp(p)

        search_button = page.get_by_role(
            "textbox", name="Текстовое поле поиска")
        qr = "canvas[aria-label*='Scan this QR code']"

        while True:
            try:
                search_button.wait_for(timeout=15000)
                picture_path = os.path.abspath(os.path.join(
                    app.config["UPLOAD_FOLDER"], "picture.jpg"))
                
                for data in g.data:
                    if data["status"] == "pending":
                        send_message(data, picture_path,
                                    text_message, search_button, page)
                g.data = get_all_data()
                return render_template("index.html", message="SUCCESS", image_url=g.image_url, numbers=[f"{item['status']}  {item['name']} - {item['phone']}" for item in g.data])

            except Exception as e:
                print(f"Error: {e}")
                page.wait_for_selector(qr, timeout=15000)
                print("The profile is not authorized, scanning the QR code is required")
                page.wait_for_timeout(10000)

    return render_template("index.html", message="Unknown error")


@app.route("/upload", methods=["POST"])
def upload():
    upload_file = request.files.get("file")

    if not upload_file or not upload_file.filename:
        return render_template("index.html", message="No file selected.")

    is_allowed, ext = allowed_file(upload_file.filename)
    if not is_allowed:
        return render_template("index.html", message="Wrong file type.")

    if ext == 'jpg':
        image_url = save_image(upload_file)
        return render_template("index.html", message="Image uploaded.", image_url=image_url)

    elif ext == "csv":
        status_numbers = save_numbers(upload_file)
        return render_template("index.html", message=status_numbers,)

    return render_template("index.html", message="Unknown error when loading.")


@app.route("/text", methods=["POST"])
def text():
    global text_message
    text_message = request.form.get("text")
    return render_template("index.html", message=text_message)


if __name__ == "__main__":
    app.run(debug=True)
