import os
import atexit
import utils
import random
from whatsapp_sender import open_whatsapp, send_message
from flask import Flask, render_template,  request, url_for, g, session, redirect
from playwright.sync_api import sync_playwright
from config import Config
from database import get_all_users, reset_sent_statuses, get_image_categories, get_images_by_category, get_all_images

app = Flask(__name__)
app.config.from_object(Config)


os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.before_request
def before_request():
    g.data = get_all_users()
    utils.init_session()


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
    message = request.args.get("message")
    categories = get_image_categories()
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
    with sync_playwright() as p:
        page = utils.open_whatsapp(p)
        try:
            search_box = page.get_by_role(
                "textbox", name="Текстовое поле поиска")
            search_box.wait_for(timeout=15000)
            picture_path = os.path.abspath(os.path.join(
                app.config["UPLOAD_FOLDER"], "picture.jpg"))

            if all(contact.status == "sent" for contact in g.data):
                return redirect(url_for('index', message="All messages sent"))

            for contact in g.data:
                if contact.status == "pending":
                    utils.send_message(contact, picture_path,
                                       session["text_message"], search_box, page)

            g.data = get_all_users()
            if all(contact.status == "sent" for contact in g.data):
                return redirect(url_for('index', message="All messages sent"))

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
    session['current_image_url'] = utils.select_next_image(
        session.get('selected_category'),
        session.get('current_image_url')
    )
    return redirect(url_for('index'))


@app.route("/set_category", methods=["POST"])
def set_category():
    selected = request.form.get("category")
    if selected:
        session["selected_category"] = selected
    return redirect(url_for("index"))


@app.route('/save_image', methods=['POST'])
def save_image():
    utils.save_image_from_url(session.get('current_image_url'))
    return redirect(url_for('index'))


@app.route('/delete_image', methods=['POST'])
def delete_image():
    current_url = session.get('current_image_url')
    if current_url:
        utils.delete_image(current_url)
    session['current_image_url'] = utils.select_next_image(
        session.get('selected_category'),
        current_url
    )
    utils.update_image_length()
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)
