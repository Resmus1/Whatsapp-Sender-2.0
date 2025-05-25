import os
import atexit
from pathlib import Path

from flask import Flask, render_template,  request, url_for, g, session
from playwright.sync_api import sync_playwright

from config import Config
from database import db

from logger import logger
from sender import open_whatsapp, send_message
import utils


app = Flask(__name__)
app.config.from_object(Config)


os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.before_request
def before_request():
    utils.init_session()
    logger.debug(f"Обработка запроса: {request.method} {request.path}")


@atexit.register
def on_exit():
    db.reset_sent_statuses()


@app.route("/reset_statuses", methods=["GET"])
def reset_statuses():
    logger.info("Сброс статусов пользователей")
    db.reset_sent_statuses()
    g.data = db.get_all_users()
    session["statuses"] = utils.counter_statuses(g.data)
    session.pop("text_message", None)
    session.pop("image_path", None)

    return utils.go_home_page("Статусы сброшены, сообщение удалено")


@app.route('/', methods=['GET', 'POST'])
def index():
    logger.debug("Отрисовка главной страницы")
    message = request.args.get("message")
    if message:
        logger.debug(f"[UI MESSAGE] {message}")

    categories = db.get_image_categories()
    selected_category = session.get('selected_category')
    current_image_url = session.get('current_image_url')

    return render_template(
        'index.html',
        categories=categories,
        message=message,
        selected_category=selected_category,
        current_image_url=current_image_url,
        image_directory_path=session["image_directory_path"],
        length=session["length"],
        sent_message=session.get("text_message"),
        numbers=utils.get_display_numbers(g.data),
        **session["statuses"],
    )


@app.route("/start")
def start():
    with sync_playwright() as playwright:
        page = open_whatsapp(playwright)
        try:
            logger.info("Начало отправки сообщений через WhatsApp")
            search_box = page.get_by_role(
                "textbox", name="Текстовое поле поиска")
            search_box.wait_for(timeout=15000)
            picture_path = Path(app.config["UPLOAD_FOLDER"]) / "picture.jpg"

            if all(contact.status == "sent" for contact in g.data):
                return utils.go_home_page("Нет ожидающих контактов для отправки сообщений")

            for contact in g.data[:2]:
                logger.debug(f"Отправка сообщения контакту: {contact.phone}")
                if contact.status == "pending":
                    send_message(
                        contact,
                        picture_path,
                        session["text_message"],
                        search_box, page
                    )

            g.data = db.get_all_users()
            if all(contact.status == "sent" for contact in g.data):
                return utils.go_home_page("Все сообщения отправлены")

            return utils.go_home_page("Messages sent", **session["statuses"])

        except Exception as e:
            logger.exception(f"Ошибка загрузки чатов: {e}")
            qr = "canvas[aria-label*='Scan this QR code']"
            try:
                page.wait_for_selector(qr, timeout=15000)
            except:
                pass

    return utils.go_home_page("Unknown error")


@app.route("/upload", methods=["POST"])
def upload():
    upload_file = request.files.get("file")
    if not upload_file:
        logger.warning("Файл не был передан пользователем")
        return utils.go_home_page("Файл не выбран")

    logger.info(f"Загрузка файла: {upload_file.filename}")
    status = utils.file_processing(upload_file)

    return utils.go_home_page(status)


@app.route("/text", methods=["POST"])
def text():
    logger.info("Пользователь задал текст сообщения")
    session["text_message"] = request.form.get("text") or ""
    return utils.go_home_page("Текст сообщения сохранен")


@app.route("/next", methods=["GET"])
def next_image():
    logger.debug("Переход к следующему изображению")
    session['current_image_url'] = utils.select_next_image(
        session.get('selected_category'),
        session.get('current_image_url')
    )
    return utils.go_home_page("Следующее изображение")


@app.route("/set_category", methods=["POST"])
def set_category():
    selected = request.form.get("category")
    logger.info(f"Выбрана категория: {selected}")
    if selected:
        session["selected_category"] = selected
    return utils.go_home_page("Категория изменена")


@app.route('/save_image', methods=['POST'])
def save_image():
    logger.info(f"Сохранено изображение: {session.get('current_image_url')}")
    utils.save_image_from_url(session.get('current_image_url'))
    return utils.go_home_page("Изображение сохранено")


@app.route('/delete_image', methods=['POST'])
def delete_image():
    current_url = session.get('current_image_url')
    logger.info(f"Удалено изображение: {current_url}")
    if current_url:
        utils.delete_image(current_url)
    session['current_image_url'] = utils.select_next_image(
        session.get('selected_category'),
        current_url
    )
    utils.update_image_length()
    return utils.go_home_page("Изображение удалено")


@app.route('/change_status', methods=['POST'])
def change_status_route():
    phone = request.form.get('phone')
    status = request.form.get('status')
    logger.info(f"Статус изменён: {phone} → {status}")
    utils.change_status(phone, status)
    return utils.go_home_page(f"Статус {phone} изменен.")


@app.route('/delete_number', methods=['POST'])
def delete_number_route():
    phone = request.form.get('phone')
    logger.info(f"Удалён номер: {phone}")
    utils.delete_number(phone)
    return utils.go_home_page(f"{phone} удален.")


@app.route("/add_number", methods=["POST"])
def add_number():
    phone = utils.process_phone_number(request.form.get("phone"))
    logger.info(f"Добавлен номер: {phone}")
    if not phone.isdigit() or len(phone) != 10:
        return utils.go_home_page(f"Введите 10 цифр после +7 (например, 7011234567)")
    utils.add_number_to_db(phone)
    return utils.go_home_page(f"{phone} добавлен.")


if __name__ == "__main__":
    logger.info("Запуск Flask-приложения")
    app.run(debug=True)
