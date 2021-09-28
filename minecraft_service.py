import logging
import subprocess
import signal
import uuid
from pathlib import Path

from subprocess import Popen
from time import sleep

import minecraft_property_file as property_file


worldDirectory = Path("worlds")
jarsDirectory = Path("jars")

logger = logging.getLogger("minecraft_service")
running_worlds = {}

class MCS:

    def createWorld(self, version):
        jarFile = jarsDirectory.joinpath(version).joinpath("server.jar")
        id = uuid.uuid4().hex
        worldPath = worldDirectory.joinpath(id)
        worldPath.mkdir(parents=True)
        logger.info("creating world %s" % id)
        subprocess.run(["java", "-Xmx6G", "-Xms6G", "-jar", jarFile.resolve(), "nogui"], cwd=worldPath)
        versionFile = worldPath.joinpath("version")
        with open(versionFile, "w") as f:
            f.write(version)
        return id

    def startWorld(self, worldId):
        if worldId in running_worlds:
            logger.warn("World with id %s is already running", worldId)
            return
        worldPath = worldDirectory.joinpath(worldId)
        versionFile = worldPath.joinpath("version")
        with open(versionFile, "r") as f:
            version = f.read()
        jarFile = jarsDirectory.joinpath(version).joinpath("server.jar")
        logger.info("Starting World %s" % worldId)
        process = Popen(["java", "-Xmx6G", "-Xms6G", "-jar", jarFile.resolve(), "nogui"], cwd=worldPath)
        running_worlds[worldId] = process
        logger.info("Started world PID: "+ str(process.pid))

    def stopWorld(self, worldId):
        process: Popen = running_worlds.pop(worldId, None)
        if process is None:
            logger.warn("World with id %s is not running", worldId)
            return False
        process.send_signal(signal.SIGINT)
        return process.wait() == 0
        
    def is_running(self, worldId):
        return worldId in running_worlds

    def setEula(self, worldId, value):
        eulaFilePath = worldDirectory.joinpath(worldId, "eula.txt")
        eula = property_file.read_to_dict(eulaFilePath)
        print(eula['eula'])
        eula['eula'] = value
        property_file.write(eulaFilePath, eula, "By changing the setting below to TRUE you are indicating your agreement to our EULA (https://account.mojang.com/documents/minecraft_eula).")
    
    def get_eula(self, worldId, value):
        eulaFilePath = worldDirectory.joinpath(worldId, "eula.txt")
        eula = property_file.read_to_dict(eulaFilePath)
        return(eula['eula'])

    def setServerProperty(self, worldId, key, value):
        propertyFilePath = worldDirectory.joinpath(worldId, "server.properties")
        properties = property_file.read_to_dict(propertyFilePath)
        properties[key] = value
        property_file.write(propertyFilePath, properties, "Minecraft server properties")

    def server_properties(self, worldId):
        propertyFilePath = worldDirectory.joinpath(worldId, "server.properties")
        return property_file.read_to_dict(propertyFilePath)

    def versions(self):
        return [x.name for x in jarsDirectory.iterdir() if x.is_dir()]

    def worlds(self):
        return [x.name for x in worldDirectory.iterdir() if x.is_dir()]
