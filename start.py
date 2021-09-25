from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from subprocess import Popen
from pathlib import Path
import subprocess
import uuid


hostName = "0.0.0.0"
serverPort = 8080
worldDirectory = Path("worlds")
jarsDirectory = Path("jars")


def createWorld(version):
    jarFile = jarsDirectory.joinpath(version).joinpath("server.jar")
    id = uuid.uuid4()
    worldPath = worldDirectory.joinpath(id.hex)
    worldPath.mkdir(parents=True)
    print("creating world %s" % id)
    serverProcess = subprocess.run(["java", "-Xmx6G", "-Xms6G", "-jar", jarFile.resolve(), "nogui"], cwd=worldPath, capture_output=True)
    print(serverProcess.stdout)


def versions():
    return [x.name for x in jarsDirectory.iterdir() if x.is_dir()]


class MCControlServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/versions":
            self.writeJsonResponse(versions())
        else:
            self.writeTxtResponse("404 - File not found", 404)
    
    def do_POST(self):
        if self.path == "/worlds":
            # curl -X POST -H "Content-Type: application/json" -d '{"version": "1.17.1"}' "localhost:8080/worlds"
            data = self.readJsonRequest()
            if data is None:
                return
            createWorld(data["version"])

    def writeJsonResponse(self, obj, response=200):
        serialized = json.dumps(obj)
        self.send_response(response)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-length", str(len(serialized)))
        self.end_headers()
        self.wfile.write(serialized.encode("utf-8"))

    def writeTxtResponse(self, message: str, response=200):
        self.send_response(response)
        self.send_header("Content-type", "text/txt")
        self.send_header("Content-length", str(len(message)))
        self.end_headers()
        self.wfile.write(message.encode("utf-8"))

    def readJsonRequest(self):
        content_length = self.headers.get("Content-length")
        if content_length is None:
            self.send_error(411)
            return None
        length = int(content_length)
        return json.loads(self.rfile.read(length))


if __name__ == "__main__":
    print("Server starting at http://%s:%s" % (hostName, serverPort))
    with HTTPServer((hostName, serverPort), MCControlServer) as webServer:
        try: 
            webServer.serve_forever()
        except KeyboardInterrupt:
            pass

    print("Server stopped")
