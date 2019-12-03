import os

from flask import Flask, redirect

app = Flask(__name__)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def redirect_all(path):
    REDIRECT_DOMAIN = "sfdo-metaci.herokuapp.com"
    redirect_url = f"{REDIRECT_DOMAIN}/{path}"
    return redirect(redirect_url, code=301)


if __name__ == "__main__":
    # Bind to PORT if defined, otherwise default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
