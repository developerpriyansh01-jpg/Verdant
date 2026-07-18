# ==========================================
# Verdant AI Plant Disease Detection System
# app.py - Flask AI Backend with Rich Metadata
# ==========================================

import os
import datetime
from functools import wraps
import numpy as np
import tensorflow as tf
import jwt
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from tensorflow.keras.preprocessing import image
from pymongo import MongoClient

# ------------------------------------------
# Load Environment Variables from .env
# ------------------------------------------
def load_env():
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

load_env()

app = Flask(__name__)
CORS(app, resources={r"/*": {
    "origins": "*",
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]
}})

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    return response

@app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
@app.route("/<path:path>", methods=["OPTIONS"])
def handle_options(path):
    response = app.make_default_options_response()
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    return response

UPLOAD_FOLDER = "uploads"
PROFILE_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, "profiles")
MODEL_PATH = "model/plant_disease_model.keras"
DATASET_PATH = "dataset/PlantVillage-Dataset-master/PlantVillage-Dataset-master/raw/color"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["PROFILE_UPLOAD_FOLDER"] = PROFILE_UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROFILE_UPLOAD_FOLDER, exist_ok=True)

# ------------------------------------------
# Hybrid Database Connection Layer (MongoDB / SQLite fallback)
# ------------------------------------------
import sqlite3

USE_MONGO = False
users_col = None
DB_FILE = "verdant.db"

try:
    MONGO_URI = os.environ.get("MONGODB_URI", "mongodb+srv://dinesh:mehukon@cluster0.rksaqdu.mongodb.net/?appName=Cluster0")
    # Set a short timeout so that if the IP is not whitelisted or network is down it fails quickly
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000, tlsAllowInvalidCertificates=True)
    # Trigger call to test connection
    client.list_database_names()
    db = client.get_database("VerdantDB")
    users_col = db.users
    USE_MONGO = True
    print("[SUCCESS] Connected to MongoDB Cloud Database")
except Exception as e:
    print(f"[WARNING] MongoDB connection failed: {e}. Falling back to SQLite local database.")
    USE_MONGO = False

def init_sqlite():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            first_name TEXT DEFAULT '',
            last_name TEXT DEFAULT '',
            mobile TEXT DEFAULT '',
            bio TEXT DEFAULT '',
            photo_url TEXT DEFAULT ''
        )
    """)
    conn.commit()
    conn.close()

if not USE_MONGO:
    init_sqlite()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def db_find_user_by_username(username):
    if USE_MONGO:
        try:
            return users_col.find_one({"username": username})
        except Exception:
            pass
    # Fallback/Local
    try:
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print("SQLite read error:", e)
        return None

def db_find_user_by_email(email):
    if USE_MONGO:
        try:
            return users_col.find_one({"email": email})
        except Exception:
            pass
    # Fallback/Local
    try:
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print("SQLite read error:", e)
        return None

def db_find_user_by_username_or_email(identifier):
    if USE_MONGO:
        try:
            return users_col.find_one({
                "$or": [
                    {"username": identifier},
                    {"email": identifier}
                ]
            })
        except Exception:
            pass
    # Fallback/Local
    try:
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM users WHERE username = ? OR email = ?", (identifier, identifier)).fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print("SQLite read error:", e)
        return None

def db_insert_user(user):
    if USE_MONGO:
        try:
            users_col.insert_one(user)
            return
        except Exception:
            pass
    # Fallback/Local
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO users (username, email, password, first_name, last_name, mobile, bio, photo_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user["username"],
        user["email"],
        user["password"],
        user.get("first_name", ""),
        user.get("last_name", ""),
        user.get("mobile", ""),
        user.get("bio", ""),
        user.get("photo_url", "")
    ))
    conn.commit()
    conn.close()

def db_update_user(username, update_fields):
    if USE_MONGO:
        try:
            users_col.update_one({"username": username}, {"$set": update_fields})
            return
        except Exception:
            pass
    # Fallback/Local
    conn = get_db_connection()
    keys = list(update_fields.keys())
    values = list(update_fields.values())
    set_clause = ", ".join([f"{k} = ?" for k in keys])
    conn.execute(f"UPDATE users SET {set_clause} WHERE username = ?", (*values, username))
    conn.commit()
    conn.close()

# ------------------------------------------
# JWT Authentication Decorator
# ------------------------------------------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({"success": False, "error": "Authentication token is missing"}), 401
        
        try:
            secret = os.environ.get("JWT_SECRET", "supersecretkey_ecogarden_ai_2026")
            data = jwt.decode(token, secret, algorithms=["HS256"])
            current_user = db_find_user_by_username(data["username"])
            if not current_user:
                return jsonify({"success": False, "error": "User session invalid"}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({"success": False, "error": "Token has expired. Please login again."}), 401
        except Exception:
            return jsonify({"success": False, "error": "Token is invalid"}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated

def serialize_user(user):
    return {
        "first_name": user.get("first_name", ""),
        "last_name": user.get("last_name", ""),
        "username": user.get("username", ""),
        "email": user.get("email", ""),
        "mobile": user.get("mobile", ""),
        "bio": user.get("bio", ""),
        "photo_url": user.get("photo_url", "")
    }


# ------------------------------------------
# Load TensorFlow Model & Class Names
# ------------------------------------------
try:
    model = tf.keras.models.load_model(MODEL_PATH)
    print("[SUCCESS] TensorFlow Model Loaded Successfully")
except Exception as e:
    print(f"[ERROR] Error loading model: {e}")
    model = None

# Get all disease class folders from dataset
if os.path.exists(DATASET_PATH):
    class_names = sorted([
        folder
        for folder in os.listdir(DATASET_PATH)
        if os.path.isdir(os.path.join(DATASET_PATH, folder))
    ])
    print(f"[SUCCESS] Loaded {len(class_names)} classes from dataset.")
else:
    class_names = []
    print("[WARNING] Dataset path not found. Fallback labels will be used.")

# ------------------------------------------
# Rich Care & Disease Database
# ------------------------------------------
def get_disease_metadata(raw_label: str) -> dict:
    label = raw_label.lower()
    
    # Defaults
    data = {
        "scientific_name": "Solanum lycopersicum",
        "description": "General plant health assessment based on leaf diagnostic models.",
        "symptoms": "Leaf spots, yellowing borders, or mild wilting characteristics.",
        "causes": "Fungal spores, high environmental moisture, or lack of proper soil nutrition.",
        "treatment": "Prune infected leaves, isolate the affected plant, and maintain base watering.",
        "medicines": "Fungicide sprays (Chlorothalonil or Copper-based fungicides if fungal).",
        "organic_solution": "Spray diluted neem oil or baking soda solution weekly.",
        "prevention": "Avoid overhead watering, maintain spacing, and sterilize garden shears.",
        "water": "Water every 2 days at base level in the morning. Avoid leaf wetness.",
        "sunlight": "6-8 hours of direct or filtered sunlight.",
        "temperature": "21°C - 29°C",
        "humidity": "50% - 65%",
        "fertilizer": "Balanced NPK organic compost every 4 weeks.",
        "health_status": "Needs Attention ⚠️",
        "tips": [
            "🍂 Prune yellowing or spotted leaves promptly.",
            "💧 Avoid watering late in the evening to reduce humidity.",
            "🌬️ Space plants to support adequate airflow.",
            "🪴 Add compost to increase soil drainage."
        ]
    }

    # ── Healthy ─────────────────────────────
    if "healthy" in label:
        data.update({
            "scientific_name": "Solanum / Rosa / Aloe (Healthy)",
            "description": "The leaf shows healthy cell structures with uniform chlorophyll distribution. No active infections detected.",
            "symptoms": "None. Leaf is green, turgid, and showing strong structure.",
            "causes": "None. Excellent care and robust growth conditions.",
            "treatment": "Continue standard maintenance. No chemical treatments needed.",
            "medicines": "None required.",
            "organic_solution": "Apply standard seaweed extract as a monthly tonic.",
            "prevention": "Ensure preventive hygiene practices are continued.",
            "water": "Water early in the morning when the top 1 inch of soil is dry.",
            "sunlight": "6-8 hours of bright sunlight daily.",
            "temperature": "20°C - 30°C",
            "humidity": "45% - 60%",
            "fertilizer": "Organic compost once a month.",
            "health_status": "Healthy ✅",
            "tips": [
                "🌱 Check leaf undersides weekly for pests.",
                "💧 Keep watering consistent.",
                "🌞 Rotate potted plants to guarantee even sunlight.",
                "✂️ Wipe leaves clean of dust to optimize photosynthesis."
            ]
        })
        
    # ── Early Blight ────────────────────────
    elif "early_blight" in label or "early blight" in label:
        data.update({
            "scientific_name": "Alternaria solani",
            "description": "Fungal disease that attacks leaves, stems, and fruit. Thrives in warm, humid weather.",
            "symptoms": "Concentric rings (target pattern) on older lower leaves. Leaves turn yellow and drop.",
            "causes": "Alternaria solani spores overwintering in plant debris or soil, splashed by water.",
            "treatment": "Remove lower infected foliage. Apply copper fungicides immediately.",
            "medicines": "Daconil, Copper Fungicide, or Mancozeb.",
            "organic_solution": "Spray baking soda solution (1 tbsp baking soda, 1 tsp liquid soap, 1 gallon water).",
            "prevention": "Crop rotation, mulching base, drip irrigation, and wider plant spacing.",
            "water": "Reduce frequency. Water base only in morning.",
            "sunlight": "6-8 Hours bright sun.",
            "temperature": "24°C - 29°C",
            "humidity": "Above 70% accelerates spread",
            "fertilizer": "High-potassium organic fertilizer to build cell walls.",
            "health_status": "Needs Attention ⚠️",
            "tips": [
                "🍂 Snip off infected lower leaves immediately.",
                "🚫 Never compost infected plant debris.",
                "💧 Use drip hoses instead of overhead sprinklers."
            ]
        })

    # ── Late Blight ─────────────────────────
    elif "late_blight" in label or "late blight" in label:
        data.update({
            "scientific_name": "Phytophthora infestans",
            "description": "Destructive water-mold disease that can rapidly kill mature tomato or potato plants.",
            "symptoms": "Dark, water-soaked spots on leaves. White fungal growth on underside in humid conditions.",
            "causes": "Phytophthora infestans spores transported by wet wind and persistent high humidity.",
            "treatment": "Destroy severely infected plants. Apply preventative copper fungicides on surrounding plants.",
            "medicines": "Copper hydroxide, Chlorothalonil.",
            "organic_solution": "Weekly preventive copper sprays and bio-fungicides containing Bacillus subtilis.",
            "prevention": "Plant resistant cultivars. Avoid overhead watering. Air circulation.",
            "water": "Dramatically restrict watering. Avoid splashing.",
            "sunlight": "Full sun to dry leaves quickly.",
            "temperature": "15°C - 22°C",
            "humidity": "90% - 100% (highly critical)",
            "fertilizer": "Suspend nitrogen; apply light phosphorus to stimulate roots.",
            "health_status": "Critical 🔴",
            "tips": [
                "🚨 Bag and dispose of infected leaves. Do not compost.",
                "📋 Check stems and fruits for brown, greasy lesions.",
                "🧪 Apply protective spray to nearby healthy plants."
            ]
        })

    # ── Leaf Spot / Septoria ─────────────────
    elif "leaf_spot" in label or "septoria" in label or "leaf spot" in label:
        data.update({
            "scientific_name": "Septoria lycopersici",
            "description": "Fungal infection causing extensive leaf spotting and defoliation, reducing yields.",
            "symptoms": "Small, circular spots with dark borders and grey centers. Small black fruiting bodies inside spots.",
            "causes": "Septoria spores splashing from soil or debris onto lower leaves in wet conditions.",
            "treatment": "Prune all spotted leaves. Apply a copper or chemical fungicide.",
            "medicines": "Chlorothalonil, Copper spray, Maneb.",
            "organic_solution": "Neem oil spray (1%) combined with regular removal of affected foliage.",
            "prevention": "Mulch soil surface, rotate crops, sterilize tools, and space plants.",
            "water": "Morning base watering only.",
            "sunlight": "6-8 hours direct sunlight.",
            "temperature": "20°C - 25°C",
            "humidity": "Moderate to High",
            "fertilizer": "Balanced NPK compost to help replacement leaf growth.",
            "health_status": "Needs Attention ⚠️",
            "tips": [
                "🍂 Mulch under plants to create a barrier against soil spores.",
                "🧤 Disinfect shears with alcohol after trimming.",
                "🌬️ Thin branches to improve air penetration."
            ]
        })

    # ── Powdery Mildew ───────────────────────
    elif "powdery_mildew" in label or "powdery mildew" in label:
        data.update({
            "scientific_name": "Podosphaera pannosa",
            "description": "Common fungal disease appearing as white, dusty spots on leaves and stems.",
            "symptoms": "White powdery coating on upper leaf surfaces. Leaves may curl, turn yellow, and dry up.",
            "causes": "High humidity at night and dry conditions during the day. Warm temperatures.",
            "treatment": "Trim infected foliage. Apply sulfur or potassium bicarbonate sprays.",
            "medicines": "Myclobutanil, Sulfur dust, Triadimefon.",
            "organic_solution": "Milk spray (30% milk, 70% water) or potassium bicarbonate solutions.",
            "prevention": "Choose sunlit spots, avoid crowded plantings, and water from below.",
            "water": "Keep water off the foliage completely. Water early.",
            "sunlight": "6+ hours direct sunlight (inhibits spores).",
            "temperature": "15°C - 27°C",
            "humidity": "Thrives in dry air with high night humidity",
            "fertilizer": "Avoid high nitrogen (makes new foliage susceptible).",
            "health_status": "Needs Attention ⚠️",
            "tips": [
                "🌬️ Ensure plants have maximum air clearance.",
                "🧴 Spray preventive milk mixture during bright noon sun.",
                "✂️ Prune dense central branches."
            ]
        })

    # ── Rust ─────────────────────────────────
    elif "rust" in label:
        data.update({
            "scientific_name": "Puccinia graminis",
            "description": "Fungal infection causing powdery, rust-colored spots on leaves and stems.",
            "symptoms": "Reddish-orange or brown powdery pustules on leaf undersides. Yellow spots on upper leaf surfaces.",
            "causes": "Persistent leaf wetness and warm humid conditions.",
            "treatment": "Remove all rusted leaves. Spray organic sulfur or copper fungicide.",
            "medicines": "Sulfur fungicide, Chlorothalonil.",
            "organic_solution": "Neem oil spray or garlic oil mixture.",
            "prevention": "Avoid wetting foliage. Destroy infected debris. Plant rust-resistant varieties.",
            "water": "Drip irrigation to keep leaves dry.",
            "sunlight": "Full direct sunlight.",
            "temperature": "18°C - 24°C",
            "humidity": "High humidity",
            "fertilizer": "Potassium compost to strengthen plant defenses.",
            "health_status": "Needs Attention ⚠️",
            "tips": [
                "🍂 Rake up and destroy fallen leaves.",
                "💧 Always water at base.",
                "🧤 Use clean gloves when touching infected plants."
            ]
        })

    # ── Bacterial Spot ───────────────────────
    elif "bacterial_spot" in label or "bacterial spot" in label:
        data.update({
            "scientific_name": "Xanthomonas perforans",
            "description": "Bacterial disease affecting tomatoes and peppers, causing leaf lesions and fruit spotting.",
            "symptoms": "Small, dark, water-soaked spots on leaves. Lesions can turn black and cause leaf drop.",
            "causes": "Infested seeds, weeds, or splashing rainwater in warm humid seasons.",
            "treatment": "Remove affected parts. Apply copper-based sprays early in infection.",
            "medicines": "Copper hydroxide, Streptomycin sulfate (in selected regions).",
            "organic_solution": "Copper fungicide combined with organic compost top dressings.",
            "prevention": "Use certified pathogen-free seeds, avoid overhead watering, control weeds.",
            "water": "Water base level, keep plants as dry as possible.",
            "sunlight": "Full direct sun.",
            "temperature": "24°C - 30°C",
            "humidity": "High humidity with rain",
            "fertilizer": "Balanced low-nitrogen organic compost.",
            "health_status": "Critical 🔴",
            "tips": [
                "🚨 Wash hands and tools immediately after contact.",
                "🌧️ Do not work in garden when plants are wet.",
                "🔄 Rotate crops out of Solanaceae family."
            ]
        })

    return data


# ------------------------------------------
# Web Routes & Static Serving
# ------------------------------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "message": "Verdant AI Plant Disease Detection and Profile API is running"
    })

# Serve uploaded profile and plant images
@app.route("/uploads/<path:filename>", methods=["GET"])
def serve_uploads(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# ------------------------------------------
# User Registration
# ------------------------------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    mobile = data.get("mobile", "").strip()
    bio = data.get("bio", "").strip()

    if not username or not email or not password:
        return jsonify({"success": False, "error": "Username, email, and password are required fields."}), 400

    # Validate duplicate records
    if db_find_user_by_username(username):
        return jsonify({"success": False, "error": "Username already taken."}), 400
    if db_find_user_by_email(email):
        return jsonify({"success": False, "error": "Email address already registered."}), 400

    hashed_password = generate_password_hash(password)

    new_user = {
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "email": email,
        "password": hashed_password,
        "mobile": mobile,
        "bio": bio,
        "photo_url": ""  # Initial empty profile photo
    }

    try:
        db_insert_user(new_user)
        return jsonify({"success": True, "message": "User registered successfully."})
    except Exception as e:
        return jsonify({"success": False, "error": f"Database write error: {str(e)}"}), 500

# ------------------------------------------
# User Login (Returns JWT)
# ------------------------------------------
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username_or_email = data.get("username_or_email", "").strip()
    password = data.get("password", "")

    if not username_or_email or not password:
        return jsonify({"success": False, "error": "Credentials missing."}), 400

    # Lookup user by username or email
    user = db_find_user_by_username_or_email(username_or_email)

    if not user or not check_password_hash(user["password"], password):
        return jsonify({"success": False, "error": "Incorrect username/email or password."}), 401

    # Generate token (expires in 7 days)
    secret = os.environ.get("JWT_SECRET", "supersecretkey_ecogarden_ai_2026")
    token_payload = {
        "username": user["username"],
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    }
    token = jwt.encode(token_payload, secret, algorithm="HS256")

    return jsonify({
        "success": True,
        "token": token,
        "user": serialize_user(user)
    })

# ------------------------------------------
# Get/Update User Profile
# ------------------------------------------
@app.route("/profile", methods=["GET", "PUT"])
@token_required
def profile_handler(current_user):
    if request.method == "GET":
        return jsonify({"success": True, "user": serialize_user(current_user)})

    # PUT request to update profile details
    data = request.get_json() or {}
    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()
    email = data.get("email", "").strip()
    mobile = data.get("mobile", "").strip()
    bio = data.get("bio", "").strip()
    photo_action = data.get("photo_action", "") # e.g. "remove" to clear photo

    update_fields = {}
    if "first_name" in data: update_fields["first_name"] = first_name
    if "last_name" in data: update_fields["last_name"] = last_name
    if "mobile" in data: update_fields["mobile"] = mobile
    if "bio" in data: update_fields["bio"] = bio

    # Handle email change validation
    if "email" in data and email != current_user["email"]:
        if not email:
            return jsonify({"success": False, "error": "Email cannot be empty."}), 400
        if db_find_user_by_email(email):
            return jsonify({"success": False, "error": "Email already in use by another user."}), 400
        update_fields["email"] = email

    # Remove photo if requested
    if photo_action == "remove":
        update_fields["photo_url"] = ""

    if not update_fields:
        return jsonify({"success": True, "user": serialize_user(current_user)})

    try:
        db_update_user(current_user["username"], update_fields)
        updated_user = db_find_user_by_username(current_user["username"])
        return jsonify({"success": True, "user": serialize_user(updated_user)})
    except Exception as e:
        return jsonify({"success": False, "error": f"Database update error: {str(e)}"}), 500

# ------------------------------------------
# Upload Profile Photo
# ------------------------------------------
@app.route("/upload-profile-photo", methods=["POST"])
@token_required
def upload_profile_photo(current_user):
    if "photo" not in request.files:
        return jsonify({"success": False, "error": "No photo file provided."}), 400

    file = request.files["photo"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No selected file."}), 400

    # Validate image extension
    allowed_extensions = {".png", ".jpg", ".jpeg", ".webp"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        return jsonify({"success": False, "error": "Unsupported file format. Use PNG, JPG, JPEG, or WEBP."}), 400

    try:
        # Save photo with a clean unique name
        filename = f"{current_user['username']}_{int(datetime.datetime.now().timestamp())}{ext}"
        filepath = os.path.join(app.config["PROFILE_UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # Build local URL (access host dynamically or localhost:5001 fallback)
        host_url = request.host_url.rstrip("/")
        photo_url = f"{host_url}/uploads/profiles/{filename}"

        # Update in database
        db_update_user(current_user["username"], {"photo_url": photo_url})

        return jsonify({
            "success": True,
            "photo_url": photo_url
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to save image: {str(e)}"}), 500


# ------------------------------------------
# Prediction Scanner endpoint
# ------------------------------------------
@app.route("/predict", methods=["POST"])
def predict():
    if not model:
        return jsonify({
            "success": False,
            "error": "AI Model is not loaded on this server."
        }), 500

    if "image" not in request.files:
        return jsonify({
            "success": False,
            "error": "No image file provided."
        }), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({
            "success": False,
            "error": "No selected file."
        }), 400

    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        # Preprocess
        img = image.load_img(file_path, target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = img_array / 255.0

        # Predict
        prediction = model.predict(img_array)
        predicted_index = int(np.argmax(prediction))
        confidence = round(float(np.max(prediction) * 100), 2)

        # Map to class label
        if class_names:
            raw_label = class_names[predicted_index]
        else:
            raw_label = "Unknown___Blight"

        # Split plant name and disease
        if "___" in raw_label:
            plant_name, disease_part = raw_label.split("___", 1)
        else:
            plant_name = "Plant"
            disease_part = raw_label

        plant_name = plant_name.replace("_", " ").strip()
        disease_name = disease_part.replace("_", " ").strip()
        
        if disease_name.lower() == "healthy":
            disease_name = "Healthy"

        # Get rich metadata
        metadata = get_disease_metadata(raw_label)

        # Clean file
        try:
            os.remove(file_path)
        except OSError:
            pass

        # Build response (no plant name — health/disease info only)
        return jsonify({
            "success": True,
            "disease": disease_name,
            "description": metadata["description"],
            "symptoms": metadata["symptoms"],
            "causes": metadata["causes"],
            "treatment": metadata["treatment"],
            "medicines": metadata["medicines"],
            "organic_solution": metadata["organic_solution"],
            "prevention": metadata["prevention"],
            "water": metadata["water"],
            "sunlight": metadata["sunlight"],
            "temperature": metadata["temperature"],
            "humidity": metadata["humidity"],
            "fertilizer": metadata["fertilizer"],
            "health_status": metadata["health_status"],
            "tips": metadata["tips"],
            "confidence": confidence
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)