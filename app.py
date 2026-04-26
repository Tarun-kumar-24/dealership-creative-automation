from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image, ImageStat
import sqlite3, os, zipfile

app = Flask(__name__)

# ---------------- CONFIG ----------------
BASE_PANEL_PATH = r"C:\Users\TARUN KANTIWAL\Desktop\AI-Automation\Project\static\assets\Dealership-panels"

ACCOUNT_MAP = {
    "1": "Tata-dealers",
    "2": "VW-dealers"
}

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
    os.makedirs(folder, exist_ok=True)


# ---------------- DB ----------------
def get_db():
    return sqlite3.connect("database.db")


def fetch_one(query, params=()):
    db = get_db()
    return db.execute(query, params).fetchone()


def fetch_all(query, params=()):
    db = get_db()
    return db.execute(query, params).fetchall()


# ---------------- HELPERS ----------------
def dealer_info(dealer_id):
    row = fetch_one(
        "SELECT name, account_id FROM dealerships WHERE id=?",
        (dealer_id,)
    )
    if not row:
        return None, None, None

    dealer_name, account_id = row
    company = ACCOUNT_MAP.get(str(account_id))
    if not company:
        return None, None, None

    folder = os.path.join(BASE_PANEL_PATH, company, dealer_name)
    return dealer_name, company, folder


def get_files(folder, check):
    if not os.path.exists(folder):
        return []
    return [f for f in os.listdir(folder) if check(f)]


def brightness(img):
    gray = img.convert("L")
    return ImageStat.Stat(gray).mean[0]


def resize_cover(img, size):
    tw, th = size
    iw, ih = img.size

    scale = max(tw / iw, th / ih)
    nw, nh = int(iw * scale), int(ih * scale)

    img = img.resize((nw, nh))
    left = (nw - tw) // 2
    top = (nh - th) // 2

    return img.crop((left, top, left + tw, top + th))


def create_image(bg_path, panel_path, logo_path, output_path, size):
    bg = resize_cover(Image.open(bg_path).convert("RGBA"), size)
    w, h = size

    # Panel
    panel = Image.open(panel_path).convert("RGBA")
    max_h = int(h * 0.32)

    ratio = min(w / panel.width, max_h / panel.height)
    pw, ph = int(panel.width * ratio), int(panel.height * ratio)

    panel = panel.resize((pw, ph), Image.LANCZOS)
    bg.paste(panel, ((w - pw) // 2, h - ph), panel)

    # Logo
    if logo_path and os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")

        lw = int(w * 0.10)
        ratio = lw / logo.width
        lh = int(logo.height * ratio)

        logo = logo.resize((lw, lh), Image.LANCZOS)

        margin = int(w * 0.03)
        lx = w - lw - margin
        ly = margin

        bg.paste(logo, (lx, ly), logo)

    bg.convert("RGB").save(output_path, quality=95)


def auto_select(bg_path, folder):
    bg_brightness = brightness(Image.open(bg_path))

    dark_logo = "logo-dark.png"
    light_logo = "logo-light.png"

    if bg_brightness > 140:
        logo = dark_logo if os.path.exists(os.path.join(folder, dark_logo)) else light_logo
    else:
        logo = light_logo if os.path.exists(os.path.join(folder, light_logo)) else dark_logo

    panels = get_files(folder, lambda f: "template" in f.lower() and f.endswith(".png"))
    if not panels:
        return None, None

    return logo, panels[0]


# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/accounts")
def accounts():
    rows = fetch_all("SELECT * FROM accounts")
    return jsonify([{"id": r[0], "name": r[1]} for r in rows])


@app.route("/dealers/<int:account_id>")
def dealers(account_id):
    rows = fetch_all(
        "SELECT * FROM dealerships WHERE account_id=?",
        (account_id,)
    )
    return jsonify([{"id": r[0], "name": r[1]} for r in rows])


@app.route("/logos/<int:dealer_id>")
def logos(dealer_id):
    _, _, folder = dealer_info(dealer_id)
    if not folder:
        return jsonify([]), 400

    files = get_files(
        folder,
        lambda f: f.startswith("logo-") and f.endswith(".png")
    )
    return jsonify(files)


@app.route("/panels/<int:dealer_id>")
def panels(dealer_id):
    _, _, folder = dealer_info(dealer_id)
    if not folder:
        return jsonify([]), 400

    files = get_files(
        folder,
        lambda f: "template" in f.lower() and f.endswith(".png")
    )
    return jsonify(files)


@app.route("/save_selection", methods=["POST"])
def save_selection():
    data = request.get_json()

    dealer_id = data.get("dealer_id")
    logo = data.get("logo")
    panel = data.get("panel")

    if not dealer_id:
        return jsonify({"error": "Missing dealer_id"}), 400

    db = get_db()
    db.execute("""
        INSERT OR REPLACE INTO dealer_selections
        (dealer_id, selected_logo, selected_panel)
        VALUES (?, ?, ?)
    """, (dealer_id, logo, panel))
    db.commit()

    return jsonify({"success": True})


@app.route("/get_selection/<int:dealer_id>")
def get_selection(dealer_id):
    row = fetch_one("""
        SELECT selected_logo, selected_panel
        FROM dealer_selections
        WHERE dealer_id=?
    """, (dealer_id,))

    if row:
        return jsonify({"logo": row[0], "panel": row[1]})

    return jsonify({"logo": None, "panel": None})


@app.route("/generate", methods=["POST"])
def generate():
    file = request.files.get("background")
    dealers = request.form.getlist("dealers")
    account = request.form.get("account")

    if not file:
        return "No background uploaded", 400
    if not account:
        return "Account missing", 400
    if not dealers:
        return "No dealers selected", 400

    company = ACCOUNT_MAP.get(str(account))
    if not company:
        return "Invalid account", 400

    bg_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(bg_path)

    sizes = [(1080, 1080), (1080, 1350), (1080, 1920)]
    output_files = []

    for dealer_id in dealers:
        row = fetch_one(
            "SELECT name FROM dealerships WHERE id=?",
            (dealer_id,)
        )
        if not row:
            continue

        dealer_name = row[0]
        folder = os.path.join(BASE_PANEL_PATH, company, dealer_name)

        if not os.path.exists(folder):
            continue

        saved = fetch_one("""
            SELECT selected_logo, selected_panel
            FROM dealer_selections
            WHERE dealer_id=?
        """, (dealer_id,))

        if saved and saved[0] and saved[1]:
            logo, panel = saved
        else:
            logo, panel = auto_select(bg_path, folder)

        if not logo or not panel:
            continue

        logo_path = os.path.join(folder, logo)
        panel_path = os.path.join(folder, panel)

        if not os.path.exists(logo_path) or not os.path.exists(panel_path):
            continue

        for size in sizes:
            name = f"{dealer_name}_{size[0]}x{size[1]}.png"
            output_path = os.path.join(OUTPUT_FOLDER, name)

            create_image(bg_path, panel_path, logo_path, output_path, size)
            output_files.append(output_path)

    if not output_files:
        return "No images generated", 400

    zip_path = os.path.join(OUTPUT_FOLDER, "result.zip")

    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file in output_files:
            zipf.write(file, os.path.basename(file))

    return send_file(zip_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)


