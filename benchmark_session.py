import http.server
import socketserver
import threading
import time
import requests
import requests.adapters

# Define a simple handler that returns 200 OK immediately
class QuietHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, format, *args):
        pass # Suppress logging

def start_server(port):
    handler = QuietHandler
    httpd = socketserver.TCPServer(("localhost", port), handler)
    httpd.serve_forever()

def run_benchmark():
    PORT = 8888
    # Start server in a background thread
    server_thread = threading.Thread(target=start_server, args=(PORT,))
    server_thread.daemon = True
    server_thread.start()

    # Wait for server to start
    time.sleep(1)

    URL = f"http://localhost:{PORT}/"
    ITERATIONS = 200

    print(f"🚀 Benchmarking {ITERATIONS} requests to {URL}...")

    # --- Test 1: No Session (Simulating old code) ---
    start_time = time.time()
    for _ in range(ITERATIONS):
        requests.post(URL, data={"test": "data"})
    end_time = time.time()
    duration_no_session = end_time - start_time
    print(f"❌ Without Session: {duration_no_session:.4f}s")

    # --- Test 2: With Session (Optimized) ---
    session = requests.Session()
    # Pre-connect
    session.post(URL, data={"warmup": "true"})

    start_time = time.time()
    for _ in range(ITERATIONS):
        session.post(URL, data={"test": "data"})
    end_time = time.time()
    duration_session = end_time - start_time
    print(f"✅ With Session:    {duration_session:.4f}s")

    # Calculate improvement
    improvement = (duration_no_session - duration_session) / duration_no_session * 100
    print(f"⚡ Improvement:     {improvement:.2f}%")

if __name__ == "__main__":
    run_benchmark()
