from datetime import datetime
from flask import Flask, request, jsonify, g, render_template
from werkzeug.exceptions import BadRequest, Unauthorized
import collections
import sqlite3
from db import DB
import pprint


app = Flask(__name__)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = DB()
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
        device['seen_ago'] = "Status expires in {}s".format(
            device['holdtime'] - seen_ago.seconds)
        if seen_ago.seconds > device['holdtime']:
            device['status'] = "dead"
        else:
            device['status'] = "alive"
    return render_template("devices.html", devices=devices)


@app.route('/device/<int:dev_id>')
def device(dev_id):
    db = get_db()
    device = db.get_device_details(dev_id)
    print(device)
    return render_template('device.html', device=device[0])

# update port description via POST from device details page
@app.route('/device/<int:dev_id>/serialport/<string:port_name>/description', methods=['POST'])
def device_update_port_description(dev_id, port_name):
    db = get_db()
    port_description = request.form['value']
    db.update_serialport_description(dev_id, port_name, port_description)
    return ""

@app.route('/api/register', methods=['POST'])
def register():
    db = get_db()
    data = request.get_json()
    print(data)
    response = db.update_device(data)
    return jsonify(response)

@app.route("/api/devices")
def api_devices():
    db = get_db()
    devices = db.get_device_details()
    return jsonify(devices)

@app.teardown_appcontext
def close_connection(exception):
    db = get_db()
    db.close()


if __name__ == "__main__":
    app.run(host="::", debug=True)

