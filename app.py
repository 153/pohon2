from flask import Flask, request

from view import view

app = Flask(__name__,
            static_url_path = "",
            static_folder = "static",)

app.register_blueprint(view)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
    print("!", request)
