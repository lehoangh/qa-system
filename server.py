from flask import Flask, request, jsonify
from flask_cors import CORS

from ipa.main import analytics, db_v

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})


@app.route('/', methods=['GET', 'POST'])
def hello():
    content = request.json
    question = content['question']
    print(question)

    return jsonify(analytics(db_v, question))


app.run()
