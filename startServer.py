from flask import Flask, render_template

app = Flask(__name__)

#app.register_blueprint(page, url_prefix="/")

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=8000)