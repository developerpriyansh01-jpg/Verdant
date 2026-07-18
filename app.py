# ==========================================
# Verdant AI Plant Disease Detection System
# Flask Backend
# ==========================================

import os
import datetime
import sqlite3
from functools import wraps

import numpy as np
import tensorflow as tf
import jwt

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from tensorflow.keras.preprocessing import image
from pymongo import MongoClient


# ------------------------------------------
# Flask App Configuration
# ------------------------------------------

app = Flask(__name__)


# Frontend (Vercel/HTML JS) Connection
CORS(
    app,
    resources={
        r"/*": {
            "origins": "*",
            "methods": [
                "GET",
                "POST",
                "PUT",
                "DELETE",
                "OPTIONS"
            ],
            "allow_headers": [
                "Content-Type",
                "Authorization"
            ]
        }
    }
)


# Test API
@app.route("/api/test", methods=["GET"])
def test():
    return jsonify({
        "success": True,
        "message": "Frontend connected successfully"
    })


# ------------------------------------------
# Environment Loader
# ------------------------------------------

def load_env():
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                line = line.strip()

                if (
                    line
                    and not line.startswith("#")
                    and "=" in line
                ):
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


load_env()


# ------------------------------------------
# Upload Configuration
# ------------------------------------------

UPLOAD_FOLDER = "uploads"
PROFILE_UPLOAD_FOLDER = os.path.join(
    UPLOAD_FOLDER,
    "profiles"
)

MODEL_PATH = "model/plant_disease_model.keras"

DATASET_PATH = (
    "dataset/"
    "PlantVillage-Dataset-master/"
    "PlantVillage-Dataset-master/"
    "raw/color"
)


app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["PROFILE_UPLOAD_FOLDER"] = PROFILE_UPLOAD_FOLDER


os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    PROFILE_UPLOAD_FOLDER,
    exist_ok=True
)


print("Verdant Backend Started")
# ==========================================
# Database Connection Layer
# ==========================================

USE_MONGO = False
users_col = None

DB_FILE = "verdant.db"


# ------------------------------------------
# MongoDB Connection
# ------------------------------------------

try:
    MONGO_URI = os.environ.get(
        "MONGODB_URI"
    )

    if MONGO_URI:

        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=3000
        )

        client.server_info()

        db = client["VerdantDB"]

        users_col = db.users

        USE_MONGO = True

        print(
            "[SUCCESS] MongoDB Connected"
        )

    else:
        print(
            "[INFO] MongoDB URI not found"
        )

except Exception as e:

    print(
        "[WARNING] MongoDB failed:",
        e
    )

    USE_MONGO = False



# ------------------------------------------
# SQLite Fallback
# ------------------------------------------

def init_sqlite():

    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(

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

    conn = sqlite3.connect(
        DB_FILE
    )

    conn.row_factory = sqlite3.Row

    return conn



# ==========================================
# User Database Functions
# ==========================================


def find_user(identifier):

    # MongoDB

    if USE_MONGO:

        return users_col.find_one(
            {
                "$or":[
                    {
                        "username":identifier
                    },
                    {
                        "email":identifier
                    }
                ]
            }
        )


    # SQLite

    conn = get_db_connection()


    user = conn.execute(
        """
        SELECT * FROM users
        WHERE username=?
        OR email=?
        """,
        (
            identifier,
            identifier
        )
    ).fetchone()


    conn.close()


    return dict(user) if user else None



def insert_user(user):

    if USE_MONGO:

        users_col.insert_one(user)

        return



    conn = get_db_connection()


    conn.execute(
        """
        INSERT INTO users
        (
        username,
        email,
        password,
        first_name,
        last_name,
        mobile,
        bio,
        photo_url
        )

        VALUES(?,?,?,?,?,?,?,?)

        """,

        (
            user["username"],
            user["email"],
            user["password"],
            user.get(
                "first_name",
                ""
            ),
            user.get(
                "last_name",
                ""
            ),
            user.get(
                "mobile",
                ""
            ),
            user.get(
                "bio",
                ""
            ),
            user.get(
                "photo_url",
                ""
            )
        )

    )


    conn.commit()

    conn.close()



# ==========================================
# JWT Authentication
# ==========================================


def token_required(function):

    @wraps(function)

    def wrapper(*args, **kwargs):

        token = None


        auth = request.headers.get(
            "Authorization"
        )


        if auth and auth.startswith(
            "Bearer "
        ):

            token = auth.split(
                " "
            )[1]



        if not token:

            return jsonify(
                {
                    "success":False,
                    "error":
                    "Token missing"
                }
            ),401



        try:

            secret = os.environ.get(
                "JWT_SECRET",
                "secret123"
            )


            data = jwt.decode(
                token,
                secret,
                algorithms=[
                    "HS256"
                ]
            )


            user = find_user(
                data["username"]
            )


            if not user:

                return jsonify(
                    {
                        "success":False,
                        "error":
                        "User not found"
                    }
                ),401



        except Exception:

            return jsonify(
                {
                    "success":False,
                    "error":
                    "Invalid token"
                }
            ),401



        return function(
            user,
            *args,
            **kwargs
        )


    return wrapper
# ==========================================
# User Serialization
# ==========================================

def serialize_user(user):

    return {
        "username": user.get(
            "username",
            ""
        ),
        "email": user.get(
            "email",
            ""
        ),
        "first_name": user.get(
            "first_name",
            ""
        ),
        "last_name": user.get(
            "last_name",
            ""
        ),
        "mobile": user.get(
            "mobile",
            ""
        ),
        "bio": user.get(
            "bio",
            ""
        ),
        "photo_url": user.get(
            "photo_url",
            ""
        )
    }



# ==========================================
# Register API
# ==========================================

@app.route(
    "/register",
    methods=["POST"]
)
def register():

    data = request.json or {}


    username = data.get(
        "username",
        ""
    ).strip()

    email = data.get(
        "email",
        ""
    ).strip()

    password = data.get(
        "password",
        ""
    )


    if not username or not email or not password:

        return jsonify(
            {
                "success":False,
                "error":
                "Username email password required"
            }
        ),400



    if find_user(username):

        return jsonify(
            {
                "success":False,
                "error":
                "Username already exists"
            }
        ),400



    if find_user(email):

        return jsonify(
            {
                "success":False,
                "error":
                "Email already exists"
            }
        ),400



    hashed_password = generate_password_hash(
        password
    )


    user = {

        "username":username,

        "email":email,

        "password":hashed_password,

        "first_name":
        data.get(
            "first_name",
            ""
        ),

        "last_name":
        data.get(
            "last_name",
            ""
        ),

        "mobile":
        data.get(
            "mobile",
            ""
        ),

        "bio":
        data.get(
            "bio",
            ""
        ),

        "photo_url":""
    }



    insert_user(
        user
    )


    return jsonify(
        {
            "success":True,
            "message":
            "Registration successful"
        }
    )




# ==========================================
# Login API
# ==========================================

@app.route(
    "/login",
    methods=["POST"]
)
def login():

    data = request.json or {}


    username = data.get(
        "username",
        ""
    )


    password = data.get(
        "password",
        ""
    )



    user = find_user(
        username
    )


    if not user:

        return jsonify(
            {
                "success":False,
                "error":
                "User not found"
            }
        ),404



    if not check_password_hash(
        user["password"],
        password
    ):

        return jsonify(
            {
                "success":False,
                "error":
                "Wrong password"
            }
        ),401



    secret = os.environ.get(
        "JWT_SECRET",
        "secret123"
    )


    token = jwt.encode(

        {
            "username":
            user["username"],

            "exp":
            datetime.datetime.now(
                datetime.timezone.utc
            )
            +
            datetime.timedelta(
                days=7
            )
        },

        secret,

        algorithm="HS256"
    )



    return jsonify(
        {
            "success":True,

            "token":token,

            "user":
            serialize_user(
                user
            )
        }
    )




# ==========================================
# Profile API
# ==========================================

@app.route(
    "/profile",
    methods=["GET"]
)
@token_required
def profile(user):

    return jsonify(
        {
            "success":True,

            "user":
            serialize_user(
                user
            )
        }
    )
# ==========================================
# TensorFlow Model Loading
# ==========================================

MODEL_PATH = "model/plant_disease_model.keras"

DATASET_PATH = (
    "dataset/"
    "PlantVillage-Dataset-master/"
    "PlantVillage-Dataset-master/"
    "raw/color"
)


try:

    model = tf.keras.models.load_model(
        MODEL_PATH
    )

    print(
        "[SUCCESS] AI Model Loaded"
    )


except Exception as e:

    print(
        "[ERROR] Model Loading Failed:",
        e
    )

    model = None




# ==========================================
# Disease Class Names
# ==========================================

if os.path.exists(DATASET_PATH):

    class_names = sorted(
        [
            folder
            for folder in os.listdir(
                DATASET_PATH
            )
            if os.path.isdir(
                os.path.join(
                    DATASET_PATH,
                    folder
                )
            )
        ]
    )


    print(
        f"[SUCCESS] Classes Loaded: {len(class_names)}"
    )


else:

    class_names = []

    print(
        "[WARNING] Dataset folder missing"
    )





# ==========================================
# Plant Disease Prediction API
# ==========================================

@app.route(
    "/predict",
    methods=["POST"]
)
def predict():


    if model is None:

        return jsonify(
            {
                "success":False,
                "error":
                "AI model not loaded"
            }
        ),500




    if "image" not in request.files:

        return jsonify(
            {
                "success":False,
                "error":
                "Image not provided"
            }
        ),400




    file = request.files["image"]


    if file.filename == "":

        return jsonify(
            {
                "success":False,
                "error":
                "Empty file"
            }
        ),400




    try:


        filename = secure_filename(
            file.filename
        )


        path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )


        file.save(
            path
        )



        # Image preprocessing

        img = image.load_img(
            path,
            target_size=(
                224,
                224
            )
        )


        img_array = image.img_to_array(
            img
        )


        img_array = np.expand_dims(
            img_array,
            axis=0
        )


        img_array = img_array / 255.0




        # Prediction

        prediction = model.predict(
            img_array
        )


        index = int(
            np.argmax(
                prediction
            )
        )


        confidence = round(
            float(
                np.max(prediction)
                *
                100
            ),
            2
        )



        if class_names:

            result = class_names[index]

        else:

            result = "Unknown"



        # Format name

        result = result.replace(
            "_",
            " "
        )



        # Remove image

        try:

            os.remove(
                path
            )

        except:

            pass




        return jsonify(
            {
                "success":True,

                "disease":
                result,

                "confidence":
                confidence,

                "message":
                "Prediction completed"
            }
        )



    except Exception as e:


        return jsonify(
            {
                "success":False,

                "error":
                str(e)
            }
        ),500
# ==========================================
# Serve Uploaded Images
# ==========================================

@app.route(
    "/uploads/<path:filename>",
    methods=["GET"]
)
def uploaded_file(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )



# ==========================================
# Health Check API (Render Test)
# ==========================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return jsonify(
        {
            "status": "online",
            "message":
            "Verdant AI Backend Running"
        }
    )



# ==========================================
# Error Handler
# ==========================================

@app.errorhandler(404)
def not_found(error):

    return jsonify(
        {
            "success":False,
            "error":
            "API endpoint not found"
        }
    ),404



# ==========================================
# Run Server
# ==========================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5001
            )
        )
    )
