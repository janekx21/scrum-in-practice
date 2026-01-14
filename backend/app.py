from flask.helpers import make_response
from flask import Flask, request, abort, g
from typing import TypedDict
import sqlite3
import uuid

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

class ShoppingList(TypedDict):
    id: str
    name: str
    items: list[str]

class ShoppingListItem(TypedDict):
    name: str
    done: bool

app = Flask(__name__)

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
    """Initialize database schema"""
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS shopping_lists(
            id TEXT PRIMARY KEY, 
            name TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS shopping_list_items(
            text TEXT NOT NULL, 
            done BOOLEAN NOT NULL,
            shopping_list TEXT NOT NULL,
            FOREIGN KEY(shopping_list) REFERENCES shopping_lists(id) ON DELETE CASCADE
        )
    """)
    con.commit()
    con.close()

# Initialize DB on startup
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

@app.route("/")
def hello_world():
    return "<p>Hello, World 2!</p>"

@app.get("/shopping-list/")
def shopping_list_all_get():
    app.logger.debug('Get all shopping lists')

    cur = get_db().cursor()
    res = cur.execute("SELECT id, name FROM shopping_lists")
    
    return list(map(lambda row: dict(row), res.fetchall()))

@app.get("/shopping-list/<uuid:id>")
def shopping_list_single_get(id: uuid.UUID):
    app.logger.debug('Get single shopping list')

    cur = get_db().cursor()
    res = cur.execute("SELECT id, name FROM shopping_lists WHERE id = :id", {'id': str(id)})
    row = res.fetchone()

    if row is None:
        abort(404)

    (id, name) = row

    res = cur.execute("SELECT text, done FROM shopping_list_items WHERE shopping_list = :id", {'id': str(id)})
    items = list(map(lambda row: {"text": row["text"], "done": row["done"] == 1}, res.fetchall())) 

    shopping_list = {
        'id': id,
        'name': name,
        'items': items 
    }
    
    return shopping_list

@app.patch("/shopping-list/<uuid:id>")
def shopping_list_single_post(id: uuid.UUID):
    json = request.json
    if json is None:
        abort(400)
        return

    db = get_db()
    cur = db.cursor()

    try:
        if 'name' in json and isinstance(json['name'], str):
            cur.execute("UPDATE shopping_lists SET name = :name WHERE id = :id", {'id': str(id), 'name': json['name']})

        if 'items' in json and isinstance(json['items'], list):
            data = list(map(lambda item:
                {'shopping_list': str(id), 'text': item['text'], 'done': item['done']}, json['items']))
            
            cur.execute("DELETE FROM shopping_list_items WHERE shopping_list=:shopping_list", {'shopping_list': str(id)})
            print(data)
            cur.executemany("INSERT INTO shopping_list_items (text, shopping_list, done) VALUES (:text, :shopping_list, :done)", data)

        db.commit()
        return {"ok": True}

    except sqlite3.Error as e:
            db.rollback()
            app.logger.error(f"Database error: {e}")
            abort(500, "Database error")

@app.post("/shopping-list/")
def shopping_list_create():
    """Create a new shopping list"""

    json = request.json
    if json is None:
        abort(400)
        return
    
    db = get_db()
    cur = db.cursor()
    
    new_id = str(uuid.uuid4())
    name = json["name"] if "name" in json and isinstance(json["name"], str) else ""
    cur.execute("INSERT INTO shopping_lists (id, name) VALUES (:id, :name)", {"id": new_id, "name": name})
    db.commit()
    
    return {"id": new_id, "name": json['name'], "items": []}, 201
