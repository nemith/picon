from datetime import datetime
from flask import Flask, request, jsonify, g, render_template
from werkzeug.exceptions import BadRequest, Unauthorized
import collections
import sqlite3
import picon_db

app = Flask(__name__)
DEADTIME = 60*5

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = picon_db.PiconDB()
    return db

@app.route("/")
def hello():
    return render_template("index.html")

@app.route("/devices")
def devices():
    db = get_db()
    devices = db.get_device_details()
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
    print(data)
    db.update_device(data)
    return jsonify(status='ok')


@app.teardown_appcontext
def close_connection(exception):
    db.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0:5000", debug=True)

