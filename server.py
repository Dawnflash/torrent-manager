from flask import Flask, request
from application import Application

app = Flask("torrent-manager")


@app.route("/", methods=["GET"])
def manage():
    """Manage torrents."""
    delete = request.args.get("delete", "0") == "1"
    app.config["application"].manage(delete=delete)
    return "OK\n", 200


@app.route("/", methods=["POST"])
def check():
    """Check if a torrent can be added."""
    data = request.get_json()
    if not data or "tracker" not in data or "size" not in data or "client" not in data:
        return "Required parameters: tracker, size, client.\n", 400
    if not isinstance(data["size"], int) or data["size"] <= 0:
        return "Size must be a positive integer.\n", 400
    try:
        ok, err = app.config["application"].check(
            data["client"], data["tracker"], data["size"]
        )
        if ok:
            return "OK\n", 200
        else:
            return f"NOK: {err}\n", 403
    except ValueError as e:
        return f"Invalid parameters: {str(e)}\n", 400


class Server:
    """HTTP server."""

    def __init__(self, application: Application):
        self.host = application.config.server["host"]
        self.port = application.config.server["port"]
        app.config["application"] = application

    def run(self):
        """Run the HTTP server."""
        app.run(host=self.host, port=self.port, debug=False)
