from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer

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
        elif url.path == "/check":
            if "tracker" not in query or "size" not in query or "client" not in query:
                return self.respond(
                    400, "Required parameters: tracker, size, client.\n"
                )
            try:
                tracker_name = query["tracker"][0]
                size = int(query["size"][0])
                client_name = query["client"][0]

                ok, err = self.server.application.check(client_name, tracker_name, size)
                if ok:
                    self.respond(200, "OK\n")
                else:
                    self.respond(403, f"NOK: {err}\n")
            except ValueError as e:
                self.respond(400, f"Invalid parameters: {str(e)}\n")
