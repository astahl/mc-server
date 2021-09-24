from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path


hostName = "0.0.0.0"
serverPort = 8080
worldDirectory = Path("worlds")
jarsDirectory = Path("jars")


def writeJsonResponse(self, obj, response=200):
    self.send_response(response)
    self.send_header("Content-type", "text/json")
    self.end_headers()
    serialized = json.dumps(obj)
    self.wfile.write(bytes(serialized, "utf-8"))

def writeTxtResponse(self, message, response=200):
    self.send_response(response)
    self.send_header("Content-type", "text/txt")
    self.end_headers()
    self.wfile.write(bytes(message, "utf-8"))
        

def versions():
    return [x.name for x in jarsDirectory.iterdir() if x.is_dir()]


class MCControlServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/versions":
            writeJsonResponse(self, versions())
        else:
            writeTxtResponse(self, "404 - File not found", 404)
        

if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), MCControlServer)

    print("Server started http://%s:%s" % (hostName, serverPort))

    try: 
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped")



