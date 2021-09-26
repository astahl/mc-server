import subprocess
import signal
import uuid
from pathlib import Path

from subprocess import Popen
from time import sleep

import minecraft_property_file as property_file


worldDirectory = Path("worlds")
jarsDirectory = Path("jars")
class MCS:

    def createWorld(version):
        jarFile = jarsDirectory.joinpath(version).joinpath("server.jar")
        id = uuid.uuid4().hex
        worldPath = worldDirectory.joinpath(id)
        worldPath.mkdir(parents=True)
        print("creating world %s" % id)
        serverProcess = subprocess.run(["java", "-Xmx6G", "-Xms6G", "-jar", jarFile.resolve(), "nogui"], cwd=worldPath, capture_output=True)
        print(serverProcess.stdout)
        versionFile = worldPath.joinpath("version")
        with open(versionFile, "w") as f:
            f.write(version)
        return id

    def startWorld(worldId):
        worldPath = worldDirectory.joinpath(worldId)
        versionFile = worldPath.joinpath("version")
        with open(versionFile, "r") as f:
            version = f.read()
        jarFile = jarsDirectory.joinpath(version).joinpath("server.jar")
        print("Start World " + worldId)
        proc = Popen(["java", "-Xmx6G", "-Xms6G", "-jar", jarFile.resolve(), "nogui"], cwd=worldPath)
        print("PID: "+ str(proc.pid))
        sleep(30)
        proc.send_signal(signal.SIGINT)
        proc.wait()
        print("Shut down " + worldId)


    def setEula(worldId, value):
        eulaFilePath = worldDirectory.joinpath(worldId, "eula.txt")
        eula = property_file.read_to_dict(eulaFilePath)
        print(eula['eula'])
        eula['eula'] = value
        property_file.write(eulaFilePath, eula, "By changing the setting below to TRUE you are indicating your agreement to our EULA (https://account.mojang.com/documents/minecraft_eula).")

    def setServerProperty(worldId, key, value):
        propertyFilePath = worldDirectory.joinpath(worldId, "server.properties")
        properties = property_file.read_to_dict(propertyFilePath)
        properties['key'] = value
        property_file.write(propertyFilePath, properties, "Minecraft server properties")

    def server_properties(worldId):
        propertyFilePath = worldDirectory.joinpath(worldId, "server.properties")
        return property_file.read_to_dict(propertyFilePath)

    def versions():
        return [x.name for x in jarsDirectory.iterdir() if x.is_dir()]

    def worlds():
        return [x.name for x in worldDirectory.iterdir() if x.is_dir()]
