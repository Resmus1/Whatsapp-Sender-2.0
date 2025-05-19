import os
import atexit
import utils
import random
from whatsapp_sender import open_whatsapp, send_message
from flask import Flask, render_template,  request, url_for, g, session, redirect
from playwright.sync_api import sync_playwright
from config import Config
from database import get_all_users, reset_sent_statuses, get_image_categories, get_images_by_category

app = Flask(__name__)
app.config.from_object(Config)


os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.before_request
def before_request():
    if not g.get("data"):
        g.data = get_all_users()
    if "image_path" not in session:
        session["image_path"] = None
    if "text_message" not in session:
        session["text_message"] = ""
    if "statuses" not in session:
        session["statuses"] = utils.counter_statuses(g.data)
    if "categories" not in session:
        session["categories"] = get_image_categories()


@atexit.register
def on_exit():
    reset_sent_statuses()


@app.route("/reset_statuses", methods=["GET"])
def reset_statuses():
    reset_sent_statuses()
    g.data = get_all_users()
    session["statuses"] = utils.counter_statuses(g.data)
    session.pop("text_message", None)
    session.pop("image_path", None)
    return redirect(url_for('index', message="Reset statuses and message"))


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        selected_category = request.form.get('category')
        session['selected_category'] = selected_category
        session['current_index'] = 0  # сбросим индекс, если меняется категория

        # Перенаправление на GET — хорошая практика (Post/Redirect/Get):
        return redirect(url_for('index'))

    message = request.args.get("message")
    image_path = utils.read_image()
    categories = get_image_categories()
    selected_category = session.get('selected_category')
    current_index = session.get('current_index', 0)
    print(utils.get_display_numbers(g.data))
    return render_template(
        'index.html',
        categories=categories,
        message=message,
        selected_category=selected_category,
        image_url=session.get("image_path") or image_path,
        current_index=current_index,
        sent_message=session.get("text_message"),
        numbers=utils.get_display_numbers(g.data),
        **session["statuses"],
    )


@app.route("/start")
def start():
    with sync_playwright() as p:
        page = utils.open_whatsapp(p)
        try:
            search_box = page.get_by_role("textbox", name="Текстовое поле поиска")
            search_box.wait_for(timeout=15000)
            picture_path = os.path.abspath(os.path.join(app.config["UPLOAD_FOLDER"], "picture.jpg"))

            if all(contact.status == "sent" for contact in g.data):
                return redirect(url_for('index', message="All messages sent"))

            # Отправляем максимум 2 сообщения за раз (пример)
            for contact in g.data[:2]:
                if contact.status == "pending":
                    utils.send_message(contact, picture_path, session["text_message"], search_box, page)

            # Обновляем данные и статусы после отправки
            g.data = get_all_users()
            session["statuses"] = utils.counter_statuses(g.data)

            return redirect(url_for('index', message="Messages sent", **session["statuses"]))

        except Exception as e:
            print(f"Ошибка загрузки чатов: {e}")
            qr = "canvas[aria-label*='Scan this QR code']"
            try:
                page.wait_for_selector(qr, timeout=15000)
            except:
                pass

    return redirect(url_for("index", message="Unknown error"))


@app.route("/upload", methods=["POST"])
def upload():
    upload_file = request.files.get("file")

    ext, status = utils.file_processing(upload_file)
    print(f"File extension: {ext}")
    return redirect(url_for('index', message=status))


@app.route("/text", methods=["POST"])
def text():
    session["text_message"] = request.form.get("text") or ""
    return redirect(url_for('index', message=f"New message: {session['text_message']}"))


@app.route("/next", methods=["GET"])
def next_image():
    selected_category = session.get('selected_category')
    current_index = session.get('current_index')

    images = get_images_by_category(
        selected_category) if selected_category else []
    if images:
        current_index = random.randint(0, len(images) - 1)
        session['current_index'] = current_index
        session["image_path"] = images[current_index].url
    return redirect(url_for('index'))


@app.route("/set_category", methods=["POST"])
def set_category():
    selected = request.form.get("category")
    if selected:
        session["selected_category"] = selected
        session["current_index"] = 0
    return redirect(url_for("index"))


@app.route('/save_image', methods=['POST'])
def save_image():
    utils.save_image_from_url(session["image_path"])
    return redirect(url_for('index'))


@app.route('/delete_image', methods=['POST'])
def delete_image():
    session["image_path"] = None
    utils.delete_image()
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)
