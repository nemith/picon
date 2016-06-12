from datetime import datetime
from flask import Flask, request, jsonify, g, render_template
from werkzeug.exceptions import BadRequest, Unauthorized
import collections
import sqlite3
	
app = Flask(__name__)
DATABASE = '/home/hack/picon/server/server.db'
DEADTIME = 60*5

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = dict_factory
    return db

@app.route("/")
def hello():
    return render_template("index.html")

@app.route("/devices")
def devices():
    db = get_db()
    c = db.cursor()
    devices = list(c.execute("SELECT * FROM devices"))
    for device in devices:
        last_updated = datetime.strptime(device['last_updated'], 
                                         "%Y-%m-%d %H:%M:%S.%f")
        seen_ago = datetime.utcnow() - last_updated
        if seen_ago.seconds > DEADTIME:
            device['status'] = "Dead :("
        else:
            device['status'] = "Alive"
    return render_template("devices.html", devices=devices)

@app.route('/device/<string:host>/<string:port>')
def device(host, port):
    return render_template('device.html', host=host, port=port)  

@app.route('/api/register',methods=['POST'])
def register():
    data = request.get_json()
    db = get_db()
    c = db.cursor()
    print(data)
    c.execute("SELECT * FROM devices WHERE sn=?", (data['sn'], ))
    device = c.fetchone()
    print(device)
    if device:
        c.execute("UPDATE devices set hostname=?, last_updated=? WHERE sn=?",
                  (data['hostname'], datetime.utcnow(), data['sn']))
    else:
        c.execute("INSERT INTO devices (hostname, sn, first_seen, last_updated) VALUES (?, ?, ?, ?)", (data['hostname'], data['sn'], datetime.utcnow(), datetime.utcnow()))
    db.commit()
    return jsonify(status='ok')


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0:5000", debug=True)

