from flask import Flask, render_template, request, jsonify
from libs.date_scrap import extract_dates, extract_topic

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.post("/add_entry")
def add_entry():
    data = request.get_json()
    task = data.get("task", None)
    if task:
        dates = extract_dates(task)
        return dates
    else:
        return jsonify({"message": "Invalid Task"})

if __name__ == "__main__":
    app.run(port=8000, debug=True)