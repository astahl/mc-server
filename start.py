import json
from pathlib import Path
import re
import mimetypes
from http.server import BaseHTTPRequestHandler, HTTPServer
from http import HTTPStatus
from typing import Pattern
from urllib import parse
from minecraft_service import MCS

hostName = "0.0.0.0"
serverPort = 8080
staticPath = Path("static_content").resolve()
NEW_LINE = "\n".encode("utf-8")
mcs = MCS()

class MCControlServer(BaseHTTPRequestHandler):


    def do_GET(self):
        url = parse.urlparse(self.path)
        pattern = re.compile(r'/api/v1/(\w*)/?(\w+)?/?(\w+)?')
        m = pattern.match(url.path)
        if m is not None:
            (controller, id, resource) = m.groups()
            if controller == "versions":
                if id == None:
                    self.send_json(mcs.versions())
                    return
            elif controller == "worlds":
                if id == None:
                    self.send_json(mcs.worlds())
                    return
                else:
                    if resource == "srvprops":
                        self.send_json(mcs.server_properties(id))
                        return
                    if resource == "eula":
                        self.send_json(mcs.get_eula(id))
                        return
                    elif resource == "run":
                        self.send_json({"is_running": mcs.is_running(id)})
                        return
        else:
            # try serving a static file matching the path
            path = url.path.removeprefix("/")
            if path == "":
                path = "index.html"
            filePath = staticPath.joinpath(path).resolve()
            if filePath.exists() and filePath.is_relative_to(staticPath):
                self.send_static_file(filePath)
                return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self):
        url = parse.urlparse(self.path)
        pattern = re.compile(r'/api/v1/(\w*)/?(\w+)?/?(\w+)?/?(\w+)?')
        m = pattern.match(url.path)
        if m is not None:
            (controller, id, resource, resource_id) = m.groups()
            (data, status) = self.read_content_json()
            if data is None:
                self.send_error(status)
                return
            if controller == "worlds":
                # curl -X POST -H "Content-Type: application/json" -d '{"version": "1.17.1"}' "localhost:8080/api/v1/worlds"
                if id == None:

                    if "version" not in data:
                        self.send_error(HTTPStatus.BAD_REQUEST)

                    worldId = mcs.createWorld(data["version"])
                    if data.get("eula") is True:
                        mcs.setEula(worldId, True)
                    if data.get("autostart") is True:
                        mcs.startWorld(worldId)
                    self.send_json({"id": worldId})
                    return
                else:
                    if resource == "srvprops":
                        for (key, value) in data.items():
                            mcs.setServerProperty(id, key, value)
                        self.send_json(mcs.server_properties(id))
                        return

        self.send_error(HTTPStatus.NOT_FOUND)

    def do_PUT(self):
        url = parse.urlparse(self.path)
        pattern = re.compile(r'/api/v1/(\w*)/?(\w+)?/?(\w+)?/?(\w+)?')
        m = pattern.match(url.path)
        (controller, id, resource, resource_id) = m.groups()
        (data, status) = self.read_content_json()
        if data is None:
            self.send_error(status)
            return
        if controller == "worlds":
            # curl -X POST -H "Content-Type: application/json" -d '{"version": "1.17.1"}' "localhost:8080/api/v1/worlds"
            if id == None or resource == None:
                # write back error
                self.send_error(HTTPStatus.BAD_REQUEST, "Worlds PUT request needs world id and resource in url")
                return
            else:
                if resource == "srvprops":
                    for (key, value) in data.items():
                        mcs.setServerProperty(id, key, value)
                    self.send_json(mcs.server_properties(id))
                    return
                if resource == "eula":
                    mcs.setEula(id, data.get("value"))
                    self.send_json(mcs.server_properties(id))
                    return
                if resource == "run":
                    if mcs.is_running(id) or mcs.startWorld(id):
                        self.send_json({"is_running": True})
                        return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_DELETE(self):
        url = parse.urlparse(self.path)
        pattern = re.compile(r'/api/v1/(\w*)/?(\w+)?/?(\w+)?/?(\w+)?')
        m = pattern.match(url.path)
        (controller, id, resource, resource_id) = m.groups()
        if controller == "worlds":
            if resource == "run":
                if mcs.is_running(id) and mcs.stopWorld(id):
                    self.send_json({"is_running": False})
                    return
        self.send_error(HTTPStatus.NOT_FOUND)
    
    def send_json(self, obj, response=200):
        serialized = json.dumps(obj)
        self.send_response(response)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-length", str(len(serialized)))
        self.end_headers()
        self.wfile.write(serialized.encode("utf-8"))
        self.wfile.write(NEW_LINE)

    def send_message(self, message: str, response=200):
        self.send_response(response)
        self.send_header("Content-type", "text/txt")
        self.send_header("Content-length", str(len(message)))
        self.end_headers()
        self.wfile.write(message.encode("utf-8"))
        self.wfile.write(NEW_LINE)

    def send_static_file(self, file: Path):
        with open(file, "r") as f:
            size = file.stat().st_size
            self.send_response(200)
            self.send_header("Content-type", mimetypes.guess_type(file))
            self.send_header("Content-length", str(size))
            self.end_headers()
            for line in f:
                self.wfile.write(line.encode("utf-8"))
            self.wfile.write(NEW_LINE)


    def read_content_json(self):
        if self.headers.get("Content-type") != "application/json":
            return (None, HTTPStatus.BAD_REQUEST, "Content-type header does not exist or is not 'application/json'")
        content_length = self.headers.get("Content-length")
        if content_length is None:
            return (None, HTTPStatus.LENGTH_REQUIRED)
        length = int(content_length)
        return (json.loads(self.rfile.read(length)), HTTPStatus.OK)

if __name__ == "__main__":
    print("Server starting at http://%s:%s" % (hostName, serverPort))
    with HTTPServer((hostName, serverPort), MCControlServer) as webServer:
        try: 
            webServer.serve_forever()
        except KeyboardInterrupt:
            pass

    print("Server stopped")
