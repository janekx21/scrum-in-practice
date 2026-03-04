from flask.helpers import make_response
from flask import Flask, request, abort, g, jsonify
from typing import TypedDict
import sqlite3
import uuid
from flask import send_from_directory
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from run_pipeline import convert

# Notes 
# =====
# Stuff that are common to add for larger apps found below.
# 
# Common Flask Extensions
# - Flask-SQLAlchemy: ORM for databases
# - Flask-Migrate: Database migrations (like Alembic)
# - Flask-CORS: Handle CORS for frontend apps
# - Flask-JWT-Extended: Authentication with JWT tokens
# - Marshmallow: Request/response validation & serialization
# - Testing stuff: pytest pytest-flask
#
# Propper project structure
# 
# project/
# ├── app/
# │   ├── __init__.py          # Application factory
# │   ├── models.py            # Database models/queries
# │   ├── routes/              # Route handlers (controllers)
# │   │   ├── shopping_lists.py
# │   │   └── auth.py
# │   ├── services.py          # Business logic
# │   └── schemas.py           # Validation (with marshmallow/pydantic)
# ├── config.py                # Configuration classes
# ├── tests/
# │   ├── __init__.py
# │   ├── conftest.py        # Test fixtures @pytest.fixture, mocks db and stuff
# │   └── test_shopping_lists.py
# └── run.py                   # Entry point 

DATABASE = "main.db"

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db() -> sqlite3.Connection:
    """Get database connection, creating if needed"""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # Access columns by name
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Close database connection at end of request"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize database schema with the Scan table"""
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            upload_datetime DATE NOT NULL,
            zip_file BLOB NOT NULL,
            glb_file BLOB NOT NULL
        )
    """)
    con.commit()
    con.close()

with app.app_context():
    init_db()


@app.before_request
def handle_options():
    if request.method == "OPTIONS":
        response = make_response("OK", 200)
        return response


@app.after_request
def add_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response    


###########################################################

@app.route("/")
def hello_world():
    return "<p>Hello, World 2!</p>"

@app.route("/upload", methods=["POST"])
def upload_scan():
    db = get_db()

    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        zip_bytes = file.read()

        name = request.form.get('name')

        if not name or file.filename == '':
            return jsonify({"error": "Name and File are mandatory"}), 400

        id = str(uuid.uuid4())
        glb_bytes = convert(zip_bytes)
        now = datetime.now()

        cur = db.cursor()
        cur.execute("""
            INSERT INTO scans (id, name, upload_datetime, zip_file, glb_file)
            VALUES (?, ?, ?, ?, ?)
        """, (id, name, now, zip_bytes, glb_bytes))
        db.commit()

        return jsonify({"id": id, "message": "Upload successful"}), 201

    except Exception as e:
        if 'db' in locals():
            db.rollback()
        return jsonify({"error": str(e)}), 500

@app.get("/scans")
def get_all_scans():
    try:
        db = get_db()
        # Fetching all scans, ordered by newest first
        cur = db.execute("SELECT id, name,  upload_datetime FROM scans ORDER BY upload_datetime DESC")
        rows = cur.fetchall()
        
        # Convert sqlite3.Row objects to a list of dictionaries
        scans = [dict(row) for row in rows]
        return jsonify(scans), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/scan/<scan_id>")
def get_scan_metadata(scan_id):
    cur = get_db().cursor()
    res = cur.execute("SELECT name, upload_datetime FROM scans WHERE id = :id", {'id': str(scan_id)})
    row = res.fetchone()

    return {
        "id": scan_id,
        "name": row["name"],
        "upload_datetime": row["upload_datetime"],
    }

@app.route("/scan/<scan_id>/full.glb")
def serve_model(scan_id):
    print("request glb ", scan_id)
    cur = get_db().cursor()
    res = cur.execute("SELECT glb_file FROM scans WHERE id = :id", {'id': str(scan_id)})
    row = res.fetchone()
    glb_bytes = row["glb_file"]

    print("sending ", len(glb_bytes), " bytes of glb")

    response = make_response(glb_bytes)
    response.headers.set('Content-Type', 'model/gltf-binary')
    response.headers.set(
        'Content-Disposition', 'attachment', filename='fill.glb')
    return response


if __name__ == "__main__":
    app.run(debug=True, port=5001)
