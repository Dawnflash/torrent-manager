from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

from application import Application


class Server(HTTPServer):
    """HTTP server."""

    def __init__(self, application: Application):
        self.application = application
        host = application.config.server["host"]
        port = application.config.server["port"]
        super().__init__((host, port), HTTPRequestHandler)

    def run(self):
        """Run the HTTP server."""
        print(f"Starting server on {self.server_address[0]}:{self.server_address[1]}")
        try:
            self.serve_forever()
        except KeyboardInterrupt:
            print("Server stopped by user.")
        finally:
            self.server_close()
            print("Server closed.")


class HTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler."""

    def read_body(self):
        """Read the request body."""
        if "Content-Length" in self.headers:
            length = int(self.headers["Content-Length"])
            return self.rfile.read(length).decode()
        elif (
            "Transfer-Encoding" in self.headers
            and self.headers["Transfer-Encoding"] == "chunked"
        ):
            body = []
            while True:
                line = self.rfile.readline().strip()
                if not line:
                    break
                chunk_size = int(line, 16)
                if chunk_size == 0:
                    self.rfile.read(2)  # Read the trailing CRLF
                    break
                body.append(self.rfile.read(chunk_size).decode())
                self.rfile.read(2)
            return "".join(body)
        return self.rfile.read().decode()

    def respond(self, code: int, message: str = ""):
        """Send an HTTP response."""
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(message.encode())

    def do_GET(self):
        """Handle GET requests."""
        url = urlparse(self.path)
        query = parse_qs(url.query)
        if url.path == "/":
            delete = query.get("delete", ["0"])[0] == "1"
            self.server.application.manage(delete=delete)
            return self.respond(200, "OK\n")
        else:
            self.respond(404, "Not Found.\n")

    def do_POST(self):
        """Handle POST requests."""
        url = urlparse(self.path)
        if url.path == "/":
            body = self.read_body()
            data = json.loads(body)
            if "tracker" not in data or "size" not in data or "client" not in data:
                return self.respond(
                    400, "Required parameters: tracker, size, client.\n"
                )
            if not isinstance(data["size"], int) or data["size"] <= 0:
                return self.respond(400, "Size must be a positive integer.\n")
            try:
                ok, err = self.server.application.check(
                    data["client"], data["tracker"], data["size"]
                )
                if ok:
                    self.respond(200, "OK\n")
                else:
                    self.respond(403, f"NOK: {err}\n")
            except ValueError as e:
                self.respond(400, f"Invalid parameters: {str(e)}\n")
        else:
            self.respond(404, "Not Found.\n")
