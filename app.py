import os
import atexit
from flask import Flask, render_template, request, url_for, g
from playwright.sync_api import sync_playwright
from utils import allowed_file, read_image, save_image, save_numbers, send_message, open_whatsapp, get_display_numbers
from config import Config
from database import get_all_users, reset_sent_statuses

app = Flask(__name__)
app.config.from_object(Config)


os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.before_request
def before_request():
    if not g.get("data"):
        g.data = get_all_users()
    if not g.get("image_url"):
        g.image_url = read_image()
    if not g.get("text_message"):
        g.text_message = ""


@atexit.register
def on_exit():
    reset_sent_statuses()


@app.route("/reset_statuses", methods=["GET"])
def reset_statuses():
    reset_sent_statuses()
    g.data = get_all_users()
    return render_template("index.html", message="All statuses reset", image_url=g.image_url, numbers=get_display_numbers(g.data))


@app.route("/")
def index():
    return render_template("index.html", message="Old data", image_url=g.image_url, numbers=get_display_numbers(g.data))


@app.route("/start")
def start():
    with sync_playwright() as p:
        page = open_whatsapp(p)

        while True:
            try:
                search_box = page.get_by_role(
                    "textbox", name="Текстовое поле поиска")
                search_box.wait_for(timeout=15000)
                picture_path = os.path.abspath(os.path.join(
                    app.config["UPLOAD_FOLDER"], "picture.jpg"))

                if all(contact.status == "sent" for contact in g.data):
                    return render_template("index.html", message="All messages sent", image_url=g.image_url, numbers=get_display_numbers(g.data))

                for contact in g.data:
                    if contact.status == "pending":
                        send_message(contact, picture_path,
                                     g.text_message, search_box, page)

                g.data = get_all_users()
                return render_template("index.html", image_url=g.image_url,
                                       numbers=get_display_numbers(g.data))

            except Exception as e:
                qr = "canvas[aria-label*='Scan this QR code']"
                print(f"Error: {e}")
                page.wait_for_selector(qr, timeout=15000)
                print("The profile is not authorized, scanning the QR code is required")
                page.wait_for_timeout(10000)

    return render_template("index.html", message="Unknown error")


@app.route("/upload", methods=["POST"])
def upload():
    upload_file = request.files.get("file")

    ext = allowed_file(upload_file.filename)

    if ext == 'jpg':
        g.image_url = save_image(upload_file)
        return render_template("index.html", message="Image uploaded.", image_url=g.image_url, numbers=get_display_numbers(g.data))

    elif ext == "csv":
        status_numbers = save_numbers(upload_file)
        return render_template("index.html", message=status_numbers, image_url=g.image_url, numbers=get_display_numbers(g.data))

    else:
        return render_template("index.html", message="Error: Wrong file type.", image_url=g.image_url, numbers=get_display_numbers(g.data))


@app.route("/text", methods=["POST"])
def text():
    g.text_message = request.form.get("text")
    return render_template("index.html", message=f"{g.text_message}", text_message=g.text_message, image_url=g.image_url, numbers=get_display_numbers(g.data))


if __name__ == "__main__":
    app.run(debug=True)
