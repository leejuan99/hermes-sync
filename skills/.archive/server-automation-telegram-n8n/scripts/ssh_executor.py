#!/usr/bin/env python3
"""
SSH Command Executor for n8n webhook
Runs as a simple HTTP server to execute shell commands
No Flask dependency - uses stdlib only
"""
import json
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = "8871187293:AAGk2B5LI64z9xlxmBi3zXG0EQnJwZIKI3Y"
CHAT_ID = "316228407"

def send_telegram(chat_id, text):
    """Send message via Telegram Bot API"""
    import urllib.request
    import urllib.parse
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    data = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=data)
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Failed to send Telegram: {e}")

class SSHHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/ssh-command':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                ssh_cmd = data.get('sshCmd', '')
                chat_id = data.get('chatId', CHAT_ID)
                
                if not ssh_cmd:
                    self.send_error(400, "No command provided")
                    return
                
                # Execute command
                result = subprocess.run(
                    ssh_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                output = result.stdout or result.stderr or "No output"
                if len(output) > 3500:
                    output = output[:3500] + "\n... (truncated)"
                
                # Send result via Telegram
                response_text = f"✅ *Command Result:*\n```\n{output}\n```"
                send_telegram(chat_id, response_text)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "ok"}')
                
            except subprocess.TimeoutExpired:
                send_telegram(chat_id, "❌ Command timed out (60s)")
                self.send_response(408)
                self.end_headers()
            except Exception as e:
                send_telegram(chat_id, f"❌ Error: {str(e)}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default log messages
        pass

if __name__ == '__main__':
    port = 5679  # Different from n8n's 5678
    server = HTTPServer(('0.0.0.0', port), SSHHandler)
    print(f"SSH Executor running on port {port}")
    server.serve_forever()