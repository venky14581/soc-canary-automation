from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class SOCIngestionHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        print("\n" + "="*50)
        print("🚨 MOCK SOC RECEIVER: NEW DATA INGESTED 🚨")
        print("="*50)
        
        # Format and print the data cleanly on your screen
        try:
            parsed_json = json.loads(post_data.decode('utf-8'))
            print(json.dumps(parsed_json, indent=2))
        except:
            print(post_data.decode('utf-8'))
            
        print("="*50 + "\n")
        
        # Send a 200 OK success code back to your script
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status": "Success"}')

print("🚀 Mock SOC Server listening on port 8080... (Press Ctrl+C to stop)")
HTTPServer(('127.0.0.1', 8080), SOCIngestionHandler).serve_forever()