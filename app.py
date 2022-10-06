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
#app.config[ 'SQLALCHEMY_DATABASE_URI'] = 'postgresql://cneuhaus:martin@zo:5432/goodwatch'
db = SQLAlchemy(app)


class GW_Battery(db.Model):
    __tablename__ = "gw_battery"

    # Makes three columns into the table id, name, email
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    voltage = db.Column(db.REAL, nullable=False)

    # A constructor function where we will pass the name and email of a user and it gets add as a new entry in the table.
    def __init__(self, voltage):
        self.voltage = voltage


# Control will come here and then gets redirect to the index function
@app.route("/")
def home():
    return redirect(url_for('index'))


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
