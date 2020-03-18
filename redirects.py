import os

from flask import Flask, redirect

app = Flask(__name__)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def redirect_all(path):
    REDIRECT_DOMAIN = "https://sfdo-metaci.herokuapp.com"
    redirect_url = f"{REDIRECT_DOMAIN}/{path}"
    response = redirect(redirect_url, code=301)
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response


if __name__ == "__main__":
    # Bind to PORT if defined, otherwise default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
