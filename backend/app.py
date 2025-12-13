from flask import Flask, request, abort, g
from typing import TypedDict
import sqlite3
import uuid

DATABASE = "main.db"

class ShoppingList(TypedDict):
    id: str
    name: str
    items: list[str]

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
            shopping_list TEXT NOT NULL,
            FOREIGN KEY(shopping_list) REFERENCES shopping_lists(id) ON DELETE CASCADE
        )
    """)
    con.commit()
    con.close()

# Initialize DB on startup
with app.app_context():
    init_db()

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

    res = cur.execute("SELECT text FROM shopping_list_items WHERE shopping_list = :id", {'id': str(id)})
    items = list(map(lambda row: row[0], res.fetchall())) 

    shopping_list = {
        'id': id,
        'name': name,
        'items': items 
    }
    
    return shopping_list

@app.post("/shopping-list/<uuid:id>")
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
            data = list(map(lambda item: {'shopping_list': str(id), 'text': item}, json['items']))
            cur.execute("DELETE FROM shopping_list_items WHERE shopping_list=:shopping_list", {'shopping_list': str(id)})
            cur.executemany("INSERT INTO shopping_list_items (text, shopping_list) VALUES (:text, :shopping_list)", data)

        db.commit()
        return {"status": "ok"}

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
    
    return {"id": new_id, "name": json['name']}, 201
