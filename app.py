from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import os
from PIL import Image, ImageStat
import zipfile
import random

app = Flask(__name__)

#  BASE PATH (correct path laga)
BASE_PANEL_PATH = r"C:\Users\TARUN KANTIWAL\Desktop\AI-Automation\Project\static\assets\Dealership-panels"

# account mapping
account_map = {
    "1": "Tata-dealers",
    "2": "VW-dealers"
}

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# ---------------- DB ----------------
def get_db():
    return sqlite3.connect("database.db")


# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/accounts")
def accounts():
    db = get_db()
    rows = db.execute("SELECT * FROM accounts").fetchall()
    return jsonify([{"id": r[0], "name": r[1]} for r in rows])


@app.route("/dealers/<int:account_id>")
def dealers(account_id):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM dealerships WHERE account_id=?",
        (account_id,)
    ).fetchall()

    return jsonify([{"id": r[0], "name": r[1]} for r in rows])


# -------- GET AVAILABLE LOGOS --------
@app.route("/logos/<int:dealer_id>")
def get_logos(dealer_id):
    db = get_db()
    
    # Get dealer name and account
    dealer = db.execute(
        "SELECT name, account_id FROM dealerships WHERE id=?",
        (dealer_id,)
    ).fetchone()
    
    if not dealer:
        return jsonify([]), 400
    
    dealer_name, account_id = dealer
    company_folder = account_map.get(str(account_id))
    
    if not company_folder:
        return jsonify([]), 400
    
    dealer_folder = os.path.join(BASE_PANEL_PATH, company_folder, dealer_name)
    
    logos = []
    
    if os.path.exists(dealer_folder):
        for file in os.listdir(dealer_folder):
            if file.startswith("logo-") and file.endswith(".png"):
                logos.append(file)
    
    return jsonify(logos)


# -------- GET AVAILABLE PANELS --------
@app.route("/panels/<int:dealer_id>")
def get_panels(dealer_id):
    db = get_db()
    
    # Get dealer name and account
    dealer = db.execute(
        "SELECT name, account_id FROM dealerships WHERE id=?",
        (dealer_id,)
    ).fetchone()
    
    if not dealer:
        return jsonify([]), 400
    
    dealer_name, account_id = dealer
    company_folder = account_map.get(str(account_id))
    
    if not company_folder:
        return jsonify([]), 400
    
    dealer_folder = os.path.join(BASE_PANEL_PATH, company_folder, dealer_name)
    
    panels = []
    
    if os.path.exists(dealer_folder):
        for file in os.listdir(dealer_folder):
            if "template" in file.lower() and file.endswith(".png"):
                panels.append(file)
    
    return jsonify(panels)


# -------- SAVE DEALER SELECTIONS --------
@app.route("/save_selection", methods=["POST"])
def save_selection():
    data = request.get_json()
    dealer_id = data.get("dealer_id")
    selected_logo = data.get("logo")
    selected_panel = data.get("panel")
    
    if not dealer_id:
        return jsonify({"error": "Missing dealer_id"}), 400
    
    db = get_db()
    
    # Insert or update
    db.execute(
        """INSERT OR REPLACE INTO dealer_selections 
           (dealer_id, selected_logo, selected_panel) 
           VALUES (?, ?, ?)""",
        (dealer_id, selected_logo, selected_panel)
    )
    
    db.commit()
    
    return jsonify({"success": True})


# -------- GET DEALER SELECTIONS --------
@app.route("/get_selection/<int:dealer_id>")
def get_selection(dealer_id):
    db = get_db()
    
    row = db.execute(
        "SELECT selected_logo, selected_panel FROM dealer_selections WHERE dealer_id=?",
        (dealer_id,)
    ).fetchone()
    
    if row:
        return jsonify({"logo": row[0], "panel": row[1]})
    
    return jsonify({"logo": None, "panel": None})


# ---------------- IMAGE HELPERS ----------------
def resize_cover(img, target_size):
    target_w, target_h = target_size
    img_ratio = img.width / img.height
    target_ratio = target_w / target_h

    if img_ratio > target_ratio:
        new_height = target_h
        new_width = int(new_height * img_ratio)
    else:
        new_width = target_w
        new_height = int(new_width / img_ratio)

    img = img.resize((new_width, new_height))

    left = (new_width - target_w) // 2
    top = (new_height - target_h) // 2

    return img.crop((left, top, left + target_w, top + target_h))


def get_brightness(img):
    gray = img.convert("L")
    stat = ImageStat.Stat(gray)
    return stat.mean[0]


def get_best_logo_position(bg, logo_w, logo_h):
    w, h = bg.size
    margin = int(w * 0.02)

    positions = [
        (margin, margin),
        (w - logo_w - margin, margin),
        (margin, h - logo_h - margin),
        (w - logo_w - margin, h - logo_h - margin)
    ]

    best_pos = positions[0]
    best_score = -1

    for (x, y) in positions:
        box = (x, y, x + logo_w, y + logo_h)
        region = bg.crop(box)
        b = get_brightness(region)
        score = abs(b - 128)

        if score > best_score:
            best_score = score
            best_pos = (x, y)

    return best_pos


def create_image(bg_path, panel_path, logo_path, output_path, size):
    bg = Image.open(bg_path).convert("RGBA")
    bg = resize_cover(bg, size)

    w, h = size

    # ---------------- PANEL FIX (NO OVERFLOW) ----------------
    panel = Image.open(panel_path).convert("RGBA")

    max_panel_h = int(h * 0.32) 

    ratio = min(w / panel.width, max_panel_h / panel.height)

    new_w = int(panel.width * ratio)
    new_h = int(panel.height * ratio)

    panel = panel.resize((new_w, new_h), Image.LANCZOS)

    px = (w - new_w) // 2
    py = h - new_h

    bg.paste(panel, (px, py), panel)

    # ---------------- LOGO FIX (FORCED VISIBILITY) ----------------
    if logo_path and os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")

        logo_w = int(w * 0.10)
        ratio = logo_w / logo.width
        logo_h = int(logo.height * ratio)

        logo = logo.resize((logo_w, logo_h), Image.LANCZOS)

        # 🔥 force top safe area
        margin = int(w * 0.03)

        lx = w - logo_w - margin
        ly = margin

        # extra safety: add alpha check
        if logo.mode != "RGBA":
            logo = logo.convert("RGBA")

        bg.paste(logo, (lx, ly), logo)

    bg = bg.convert("RGB")
    bg.save(output_path, quality=95)
# ---------------- GENERATE ----------------
@app.route("/generate", methods=["POST"])
def generate():

    print("🔥 GENERATE CALLED")

    file = request.files.get("background")
    dealers = request.form.getlist("dealers")
    account = request.form.get("account")

    print("Account:", account)
    print("Dealers:", dealers)

    if not file:
        return "No background uploaded ", 400

    if not account:
        return "Account missing ", 400

    if not dealers:
        return "No dealers selected ", 400

    bg_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(bg_path)

    sizes = [(1080,1080), (1080,1350), (1080,1920)]
    output_files = []

    company_folder = account_map.get(str(account))

    if not company_folder:
        return "Invalid account ", 400

    db = get_db()

    for dealer in dealers:

        #  ID → NAME
        row = db.execute(
            "SELECT name FROM dealerships WHERE id=?",
            (dealer,)
        ).fetchone()

        if not row:
            print(" Dealer not in DB:", dealer)
            continue

        dealer_name = row[0]

        dealer_folder = os.path.join(BASE_PANEL_PATH, company_folder, dealer_name)

        print("Dealer:", dealer_name)
        print("Folder:", dealer_folder)

        if not os.path.exists(dealer_folder):
            print(" Folder not found:", dealer_folder)
            continue

        # -------- GET DEALER SELECTIONS OR AUTO-SELECT --------
        selection = db.execute(
            "SELECT selected_logo, selected_panel FROM dealer_selections WHERE dealer_id=?",
            (dealer,)
        ).fetchone()

        if selection and selection[0] and selection[1]:
            # Use saved selection
            selected_logo, selected_panel = selection
            print("Using saved selection - Logo:", selected_logo, "Panel:", selected_panel)
        else:
            # Auto-select based on background brightness and available files
            print("Auto-selecting logo and panel...")
            
            # Auto-select logo
            brightness = get_brightness(Image.open(bg_path))
            dark_logo = os.path.join(dealer_folder, "logo-dark.png")
            light_logo = os.path.join(dealer_folder, "logo-light.png")
            
            if brightness > 140:
                selected_logo = "logo-dark.png" if os.path.exists(dark_logo) else "logo-light.png"
            else:
                selected_logo = "logo-light.png" if os.path.exists(light_logo) else "logo-dark.png"
            
            # Auto-select panel (first available template)
            templates = [
                f for f in os.listdir(dealer_folder)
                if "template" in f.lower() and f.endswith(".png")
            ]
            
            if not templates:
                print(" No templates found in folder")
                continue
            
            selected_panel = templates[0]
            print("Auto-selected - Logo:", selected_logo, "Panel:", selected_panel)

        # -------- LOGO --------
        logo_path = os.path.join(dealer_folder, selected_logo)

        if not os.path.exists(logo_path):
            print(" Logo not found:", logo_path)
            continue

        # -------- PANEL --------
        panel_path = os.path.join(dealer_folder, selected_panel)

        if not os.path.exists(panel_path):
            print(" Panel not found:", panel_path)
            continue

        # -------- GENERATE --------
        for size in sizes:
            filename = f"{dealer_name}_{size[0]}x{size[1]}.png"
            output_path = os.path.join(OUTPUT_FOLDER, filename)

            create_image(bg_path, panel_path, logo_path, output_path, size)
            output_files.append(output_path)

    if not output_files:
        return "No images generated  (check folders/files)", 400

    # -------- ZIP --------
    zip_path = os.path.join(OUTPUT_FOLDER, "result.zip")

    with zipfile.ZipFile(zip_path, "w") as zipf:
        for f in output_files:
            zipf.write(f, os.path.basename(f))

    return send_file(zip_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)

