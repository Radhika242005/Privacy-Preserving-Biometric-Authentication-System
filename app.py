from flask import Flask, render_template, request, redirect, url_for, session
from deepface import DeepFace
import numpy as np
import os, pickle
import json
from datetime import datetime

from cryptography.fernet import Fernet
import base64
from PIL import Image
from io import BytesIO

# =====================================================
# FLASK SETUP
# =====================================================
app = Flask(__name__)
app.secret_key = "super_secret_key"

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "temp")
DATA_FOLDER = os.path.join(PROJECT_ROOT, "..", "data", "users")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

MAX_IMAGES = 3
THRESHOLD = 0.40
EMB_SIZE = 128

# =====================================================
# ADMIN LOGIN CREDENTIALS
# =====================================================
#ADMIN_USERNAME = "admin"
#ADMIN_PASSWORD = "admin123"

# =====================================================
# LOGIN HISTORY FILE
# =====================================================
LOGIN_FILE = os.path.join(DATA_FOLDER, "logins.json")

if not os.path.exists(LOGIN_FILE):
    with open(LOGIN_FILE, "w") as f:
        json.dump({}, f)


def load_logins():
    with open(LOGIN_FILE, "r") as f:
        return json.load(f)


def save_logins(data):
    with open(LOGIN_FILE, "w") as f:
        json.dump(data, f, indent=4)


# =====================================================
# AES KEY SETUP
# =====================================================
KEY_FILE = os.path.join(PROJECT_ROOT, "aes.key")

if not os.path.exists(KEY_FILE):
    with open(KEY_FILE, "wb") as f:
        f.write(Fernet.generate_key())

with open(KEY_FILE, "rb") as f:
    AES_KEY = f.read()

cipher = Fernet(AES_KEY)


def encrypt_embedding(embedding):
    return cipher.encrypt(embedding.tobytes())


def decrypt_embedding(enc_data):
    raw = cipher.decrypt(enc_data)
    return np.frombuffer(raw, dtype=np.float64)


# =====================================================
# COSINE DISTANCE
# =====================================================
def cosine_distance(a, b):
    return 1 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


# =====================================================
# SAVE WEBCAM IMAGE
# =====================================================
def save_webcam_image(image_data):
    image_data = image_data.split(",")[1]
    decoded = base64.b64decode(image_data)

    img = Image.open(BytesIO(decoded))
    path = os.path.join(UPLOAD_FOLDER, "webcam.png")
    img.save(path)

    return path


# =====================================================
# RULE 1: SINGLE FACE ONLY
# =====================================================
def single_face_only(img_path):
    try:
        faces = DeepFace.extract_faces(
            img_path=img_path,
            detector_backend="retinaface",
            enforce_detection=True
        )
        return len(faces) == 1
    except:
        return False


# =====================================================
# EMBEDDING FUNCTION
# =====================================================
def get_embedding(img_path):
    rep = DeepFace.represent(
        img_path=img_path,
        model_name="Facenet512",
        detector_backend="retinaface",
        enforce_detection=True
    )
    emb = np.array(rep[0]["embedding"])
    vec = emb[:EMB_SIZE]
    vec = vec / np.linalg.norm(vec)
    return vec



# =====================================================
# RULE 2: SAME FACE CANNOT USE MULTIPLE USERNAMES
# =====================================================
def face_already_registered(new_emb, username):

    all_users = [
        u for u in os.listdir(DATA_FOLDER)
        if os.path.isdir(os.path.join(DATA_FOLDER, u))
    ]

    for other_user in all_users:

        if other_user == username:
            continue

        other_dir = os.path.join(DATA_FOLDER, other_user)
        files = [f for f in os.listdir(other_dir) if f.endswith(".bin")]

        for file in files:
            with open(os.path.join(other_dir, file), "rb") as f:
                enc = f.read()

            stored_emb = decrypt_embedding(enc)
            dist = cosine_distance(new_emb, stored_emb)

            if dist < THRESHOLD:
                return other_user

    return None


# =====================================================
# RULE 3: SAME USERNAME CANNOT STORE DIFFERENT PERSONS
# =====================================================
def username_consistency_check(new_emb, user_dir):

    files = [f for f in os.listdir(user_dir) if f.endswith(".bin")]

    if len(files) == 0:
        return True

    distances = []

    for file in files:
        with open(os.path.join(user_dir, file), "rb") as f:
            enc = f.read()

        stored_emb = decrypt_embedding(enc)
        dist = cosine_distance(new_emb, stored_emb)
        distances.append(dist)

    # If new face is too different → Reject
    if min(distances) > THRESHOLD:
        return False

    return True


# =====================================================
# HOME PAGE
# =====================================================
@app.route("/")
def home():
    return render_template("index.html")


# =====================================================
# REGISTER USER
# =====================================================
@app.route("/register", methods=["POST"])
def register():

    username = request.form.get("username")
    image_data = request.form.get("imageData")

    if not username or not image_data:
        return render_template("index.html", result="❌ Username & Face Required")

    user_dir = os.path.join(DATA_FOLDER, username)
    os.makedirs(user_dir, exist_ok=True)

    stored_files = [f for f in os.listdir(user_dir) if f.endswith(".bin")]

    if len(stored_files) >= MAX_IMAGES:
        return render_template("index.html", result="✅ Already Registered 3 Images")

    temp_path = save_webcam_image(image_data)

    # RULE 1: Only ONE Face Allowed
    if not single_face_only(temp_path):
        os.remove(temp_path)
        return render_template("index.html",
                               result="❌ Only ONE Face Allowed (No Group Photo)")

    new_emb = get_embedding(temp_path)
    os.remove(temp_path)

    # RULE 2: Same Face Cannot Use Another Username
    duplicate_user = face_already_registered(new_emb, username)

    if duplicate_user:
        return render_template("index.html",
                               result=f"❌ Face Already Registered as {duplicate_user}")

    # RULE 3: Same Username Cannot Store Different Person
    if not username_consistency_check(new_emb, user_dir):
        return render_template("index.html",
                               result="❌ Different Person Detected for Same Username!")

    # SAVE EMBEDDING
    encrypted_emb = encrypt_embedding(new_emb)

    save_path = os.path.join(user_dir, f"embedding_{len(stored_files)+1}.bin")

    with open(save_path, "wb") as f:
        f.write(encrypted_emb)

    return render_template("index.html",
                           result=f"✅ Registered {len(stored_files)+1}/3 Successfully")


# =====================================================
# LOGIN USER
# =====================================================
@app.route("/authenticate", methods=["POST"])
def authenticate():

    username = request.form.get("username")
    image_data = request.form.get("imageData")

    user_dir = os.path.join(DATA_FOLDER, username)

    if not os.path.exists(user_dir):
        return render_template("index.html", result="❌ User Not Found")

    files = [f for f in os.listdir(user_dir) if f.endswith(".bin")]

    if len(files) < 3:
        return render_template("index.html", result="❌ Register 3 Images First")

    temp_path = save_webcam_image(image_data)

    # RULE 1: Only ONE Face Allowed
    if not single_face_only(temp_path):
        os.remove(temp_path)
        return render_template("index.html",
                               result="❌ Only ONE Face Allowed for Login!")

    login_emb = get_embedding(temp_path)
    os.remove(temp_path)

    matches = 0

    for file in files:
        with open(os.path.join(user_dir, file), "rb") as f:
            enc = f.read()

        stored_emb = decrypt_embedding(enc)
        dist = cosine_distance(login_emb, stored_emb)

        if dist < THRESHOLD:
            matches += 1

    if matches >= 2:

        session["user"] = username

        # LOGIN HISTORY UPDATE
        logins = load_logins()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if username not in logins:
            logins[username] = {"count": 0, "history": []}

        logins[username]["count"] += 1
        logins[username]["history"].append(now)

        save_logins(logins)

        return redirect(url_for("dashboard"))

    return render_template("index.html", result="❌ Face Match Failed")


# =====================================================
# USER DASHBOARD
# =====================================================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("home"))

    return render_template("dashboard.html", user=session["user"])


# =====================================================
# USER LOGOUT
# =====================================================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# =====================================================
# ADMIN LOGIN
# =====================================================
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        admin_user = request.form.get("admin_username")
        admin_pass = request.form.get("admin_password")

        if admin_user == ADMIN_USERNAME and admin_pass == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))

        return render_template("admin_login.html",
                               error="❌ Invalid Admin Credentials")

    return render_template("admin_login.html")


# =====================================================
# ADMIN DASHBOARD
# =====================================================
@app.route("/admin_dashboard")
def admin_dashboard():

    if "admin" not in session:
        return redirect(url_for("admin_login"))

    users = [
        u for u in os.listdir(DATA_FOLDER)
        if os.path.isdir(os.path.join(DATA_FOLDER, u))
    ]

    logins = load_logins()
    user_data = []

    for user in users:

        user_dir = os.path.join(DATA_FOLDER, user)
        emb_files = [f for f in os.listdir(user_dir) if f.endswith(".bin")]

        login_info = logins.get(user, {"count": 0, "history": []})

        user_data.append({
            "username": user,
            "embeddings": len(emb_files),
            "logins": login_info["count"],
            "history": login_info["history"]
        })

    return render_template("admin.html", user_data=user_data)


# =====================================================
# ADMIN LOGOUT → INDEX PAGE
# =====================================================
@app.route("/admin_logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("home"))


# =====================================================
# RUN SERVER
# =====================================================
if __name__ == "__main__":
    app.run(debug=True)
