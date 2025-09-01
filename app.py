from flask import Flask, render_template, jsonify, request, redirect, url_for, jsonify, json
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_cors import CORS
from config import DB_PWD

app = Flask(__name__)
app.config.from_pyfile('config.py')
CORS(app)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config[ 'SQLALCHEMY_DATABASE_URI'] = 'postgresql://'+DB_PWD+'@zo:5432/goodwatch'

db = SQLAlchemy(app)


class GW_Battery(db.Model):
    __tablename__ = "gw_battery"

    # Database columns
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    source = db.Column(db.String(50), nullable=True)
    voltage = db.Column(db.REAL, nullable=False)
    capacity = db.Column(db.REAL, nullable=True)
    warnings = db.Column(db.String(50), nullable=True)
    bat_status_string = db.Column(db.String(50), nullable=True)
    bat_slope = db.Column(db.REAL, nullable=True)
    nvs_log = db.Column(db.Text(25500), nullable=True)

    # Constructor function
    def __init__(self, source=None, voltage=None, capacity=None, warnings=None, bat_status_string=None, bat_slope=None, nvs_log=None):
        self.source = source
        self.voltage = voltage
        self.capacity = capacity
        self.warnings = warnings
        self.bat_status_string = bat_status_string
        self.bat_slope = bat_slope
        self.nvs_log = nvs_log


# Control will come here and then gets redirect to the index function
@app.route("/")
def home():
    return redirect(url_for('index'))


@app.route("/log", methods=["POST"])
def log_error():
    try:
        if request.headers.get('Content-Type') == 'application/json':
            data = request.json
            log_entry = data.get('log')
            if log_entry:
                bat = GW_Battery(nvs_log=log_entry,voltage=0)
                db.session.add(bat)
                db.session.commit()
                return jsonify({"status": "success"}), 200
            else:
                return jsonify({"error": "Missing log field"}), 400
        else:
            return jsonify({"error": "Content-Type not supported!"}), 415
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 400



@app.route("/voltage", methods=["POST"])
def logwrite_json():
    try:
        content_type = request.headers.get('Content-Type')
        if (content_type == 'application/json'):
            json_res = request.json
            bat = GW_Battery(**json_res)

            db.session.add(bat)
            db.session.commit()

            response = app.response_class(
                status=200,
                mimetype='application/json'
            )

            return response

        else:
            return 'Content-Type not supported!'
    except Exception as e:

        response = app.response_class(
            status=400,
            mimetype='application/json'
        )

        return response


@app.route("/index", methods=["GET"])
def index():
    gw_data = GW_Battery.query.all()

    return render_template("index.html", gw_data=gw_data)  # passes user_data variable into the index.html file.


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
