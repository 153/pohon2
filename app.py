#!/usr/bin/python3
import os

from flask import Flask, request
from view import view
from admin import admin

app = Flask(__name__,
            static_url_path = "",
            static_folder = "static",)

app.register_blueprint(view)
app.register_blueprint(admin)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
    print("!", request)
    files = ["log.txt", "index.txt", "tags.txt", "bans.txt"]
    for f in files:
        if not os.path.isfile(f"data/{f}"):
            with open(f"data/{f}", "w") as fp:
                pass
