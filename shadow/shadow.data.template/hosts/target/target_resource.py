import http.server
import socketserver

PORT = 8080
MESSAGE = b"Fetched target resource successfully\n"

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(MESSAGE)
    def log_message(self, format, *args):
        return

with socketserver.TCPServer(("", PORT), QuietHandler) as httpd:
    httpd.serve_forever()