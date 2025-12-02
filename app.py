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


# New model for heating_events table
class HeatingEvents(db.Model):
    __tablename__ = "heating_events"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    timestamp_ms = db.Column(db.BigInteger, nullable=False)
    phase = db.Column(db.String(64), nullable=False)
    rounded_set_temperature_c = db.Column(db.Numeric(6, 2), nullable=True)
    should_send = db.Column(db.Boolean, nullable=False)
    t_desk_c = db.Column(db.Numeric(6, 2), nullable=True)
    t_outside_c = db.Column(db.Numeric(6, 2), nullable=True)
    user_target_c = db.Column(db.Numeric(6, 2), nullable=True)
    heater_on = db.Column(db.Boolean, nullable=True)
    hold_offset_c = db.Column(db.Numeric(6, 3), nullable=True)
    boost_offset_c = db.Column(db.Numeric(6, 3), nullable=True)
    outside_gain = db.Column(db.Numeric(8, 6), nullable=True)
    warmup_rate_est_c_per_min = db.Column(db.Numeric(10, 6), nullable=True)
    steady_error_avg_c = db.Column(db.Numeric(8, 6), nullable=True)
    trigger_reason = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())


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


# New route for logging heating events from home box
@app.route("/log_home_box", methods=["POST"])
def log_home_box():
    try:
        content_type = request.headers.get('Content-Type')
        if content_type != 'application/json':
            return jsonify({"error": "Content-Type not supported!"}), 415

        payload = request.json or {}

        # Required top-level fields
        timestamp_ms = payload.get('timestamp_ms')
        phase = payload.get('phase')
        should_send = payload.get('should_send')
        trigger = payload.get('trigger')

        if timestamp_ms is None or phase is None or should_send is None or trigger is None:
            return jsonify({"error": "Missing required field"}), 400

        inputs = payload.get('inputs') or {}
        learned = payload.get('learned_params') or {}

        event = HeatingEvents(
            timestamp_ms=timestamp_ms,
            phase=phase,
            rounded_set_temperature_c=payload.get('rounded_set_temperature_c'),
            should_send=should_send,
            t_desk_c=inputs.get('t_desk_c'),
            t_outside_c=inputs.get('t_outside_c'),
            user_target_c=inputs.get('user_target_c'),
            heater_on=inputs.get('heater_on'),
            hold_offset_c=learned.get('hold_offset_c'),
            boost_offset_c=learned.get('boost_offset_c'),
            outside_gain=learned.get('outside_gain'),
            warmup_rate_est_c_per_min=learned.get('warmup_rate_est_c_per_min'),
            steady_error_avg_c=learned.get('steady_error_avg_c'),
            trigger_reason=trigger,
        )

        db.session.add(event)
        db.session.commit()

        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(e)
        return jsonify({"error": "bad request"}), 400


@app.route("/index", methods=["GET"])
def index():
    gw_data = GW_Battery.query.all()

    return render_template("index.html", gw_data=gw_data)  # passes user_data variable into the index.html file.


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
