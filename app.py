#!/usr/bin/python3
import os

from flask import Flask, request
from view import view
from admin import admin
from whitelist import whitelist
from atom import atom

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__,
            static_url_path = "",
            static_folder = "static",)

app.register_blueprint(view)
app.register_blueprint(admin)
app.register_blueprint(whitelist)
app.register_blueprint(atom)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
    print("!", request)
    files = ["log.txt", "index.txt", "tags.txt", "bans.txt", "ips.txt"]
    for f in files:
        if not os.path.isfile(f"data/{f}"):
            with open(f"data/{f}", "w") as fp:
                pass
