from flask import Flask, request, abort
from typing import TypedDict
import sqlite3
import uuid
app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World 2!</p>"

class ShoppingList(TypedDict):
    id: str
    name: str
    items: list[str]

con = sqlite3.connect("main.db")

cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS shopping_lists(id PRIMARY KEY, name)")
res = cur.execute("CREATE TABLE IF NOT EXISTS shopping_list_items(text, shopping_list, FOREIGN KEY(shopping_list) REFERENCES shopping_lists(id))")
print(res.fetchall())
# res = cur.execute("INSERT INTO shopping_lists VALUES ('1bbd9443-bc03-4820-a370-5fa39533d00d', 'Sqlite Shopping list')")
print(res.fetchall())

cur.close()
con.commit()
con.close()

@app.get("/shopping-list/")
def shopping_list_all_get():
    app.logger.debug('Get all shopping lists')

    con = sqlite3.connect("main.db")
    cur = con.cursor()
    res = cur.execute("SELECT id, name FROM shopping_lists")

    def row_to_dict(row):
        id, name = row
        return {"id": id, "name": name}
    
    try:
        return list(map(row_to_dict, res.fetchall()))
    except KeyError:
        abort(404)

@app.get("/shopping-list/<uuid:id>")
def shopping_list_single_get(id: uuid.UUID):
    app.logger.debug('Get single shopping list')

    con = sqlite3.connect("main.db")
    cur = con.cursor()
    res = cur.execute("SELECT id, name FROM shopping_lists WHERE id = :id", {'id': str(id)})
    (id, name) = res.fetchone()

    res = cur.execute("SELECT text FROM shopping_list_items WHERE shopping_list = :id", {'id': str(id)})
    # '1bbd9443-bc03-4820-a370-5fa39533d00d'
    # '1bbd9443-bc03-4820-a370-5fa39533d00d'
    items = res.fetchall()

    shopping_list = {
        'id': id,
        'name': name,
        'items': list(map(lambda row: row[0], items))
    }
    
    return shopping_list

@app.post("/shopping-list/<uuid:id>")
def shopping_list_single_post(id: uuid.UUID):
    json = request.json

    if json is None:
        abort(400)
        return
    else:
        try:
            con = sqlite3.connect("main.db")
            cur = con.cursor()


            if 'name' in json and type(json['name']) is str:
                cur.execute("UPDATE shopping_lists SET name = :name WHERE id = :id", {'id': str(id), 'name': json['name']})

            if 'items' in json and type(json['items']) is list:
                data = list(map(lambda item: {'shopping_list': str(id), 'text': item}, json['items']))
                cur.execute("DELETE FROM shopping_list_items WHERE shopping_list=:shopping_list", {'shopping_list': str(id)})
                res = cur.executemany("INSERT INTO shopping_list_items VALUES (:text, :shopping_list)", data)
                print(json['items'])
                print(data)
                print(res.fetchone())

            con.commit()

        except AttributeError as err:
            abort(400, str(err))
        except KeyError:
            abort(404)

        return "ok"
