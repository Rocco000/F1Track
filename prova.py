from flask import Flask
from views import page

app = Flask(__name__)

app.register_blueprint(page, url_prefix="/homepage")

if __name__ == "__main__":
    app.run(debug=True, port=8000)