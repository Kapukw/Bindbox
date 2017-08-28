import os
import stat
import socket
import shutil
import time
import json
from tempfile import mkstemp

import psutil

# user config
CLOUD_DIR = os.path.normcase("Dropbox/Bindbox/")
PATHS_FILE = "paths.json"

g_numTotalApps = None
g_numSyncedApps = None


def getHostName():
    name = socket.gethostname()
    return name


def getSyncStats():
    if g_numTotalApps is None or g_numSyncedApps is None:
        return "..."
    return "{}/{}".format(g_numSyncedApps, g_numTotalApps)


def getConfigPath():
    path = os.path.join(os.path.expanduser("~"), CLOUD_DIR, PATHS_FILE)
    return path


def getCloudPath():
    path = os.path.join(os.path.expanduser("~"), CLOUD_DIR)
    return path


def listProcesses():
    procNames = list()
    for proc in psutil.process_iter():
        try:
            procName = proc.name()
        except psutil.NoSuchProcess:
            pass
        else:
            procNames.append(procName)
    return procNames


def getTreeModificationTime(rootPath):
    mtime = os.stat(rootPath).st_mtime
    new_mtime = mtime

    for child in os.listdir(rootPath):

        childPath = os.path.join(rootPath, child)
        childMode = os.stat(childPath).st_mode

        # directory
        if stat.S_ISDIR(childMode):
            new_mtime = getTreeModificationTime(childPath)

        # file
        elif stat.S_ISREG(childMode):
            new_mtime = os.stat(childPath).st_mtime

        mtime = max(new_mtime, mtime)

    return mtime


def copystatRecursive(src, dst):
    if stat.S_ISDIR(os.stat(src).st_mode):
        srcEntries = os.listdir(src)
        dstEntries = os.listdir(dst)
        for i in range(0, len(srcEntries)):
            copystatRecursive(os.path.join(src, srcEntries[i]), os.path.join(dst, dstEntries[i]))
    shutil.copystat(src, dst)


class AppSyncResult(object):
    NOT_SYNCED = 0
    EQUAL = 1
    CLOUD_TO_HOST = 2
    HOST_TO_CLOUD = 3


def getResultStr(result):
    strings = { AppSyncResult.NOT_SYNCED    : "not synced",
                AppSyncResult.EQUAL         : "host == cloud",
                AppSyncResult.CLOUD_TO_HOST : "host <- cloud",
                AppSyncResult.HOST_TO_CLOUD : "host -> cloud" }
    return strings[result]


def getSyncPaths(jsonDict):
    if 'paths' not in jsonDict:
        return []
    currentHostName = getHostName()
    for hostName in jsonDict['paths']:
        if str(currentHostName).lower() == str(hostName).lower():
            return jsonDict['paths'][hostName]
    return []


class AppData(object):
    def __init__(self, jsonDict):
        hostName = getHostName()
        self.name = jsonDict['name']
        self.procNames = jsonDict['proc_names'] if 'proc_names' in jsonDict else []
        self.paths = getSyncPaths(jsonDict)

    def syncConfig(self, callback=None):
        print("{}:".format(self.name))

        currentProcesses = listProcesses()
        for procName in self.procNames:
            if procName in currentProcesses:
                print("Skip '{}' because it's running.".format(self.name))
                return

        syncHappened = False

        for i in range(0, len(self.paths)):

            result = AppSyncResult.NOT_SYNCED

            hostPath = os.path.normpath(os.path.expandvars(self.paths[i]))
            cloudPath = os.path.normpath(os.path.join(getCloudPath(), self.name, str(i), ""))
                
            isHostExists = os.path.exists(hostPath)
            isCloudExists = os.path.exists(cloudPath)

            if isHostExists and isCloudExists:

                hp_mtime = int(getTreeModificationTime(hostPath))
                cp_mtime = int(getTreeModificationTime(cloudPath))

                print("\thost: {}\n\tcloud: {}\n\thost modified: {}\n\tcloud modified: {}".format(hostPath, cloudPath, time.ctime(hp_mtime), time.ctime(cp_mtime)))

                if hp_mtime > cp_mtime:
                    if not replaceTree(hostPath, cloudPath):
                        print("\tSkip '{}' because it's locked.".format(cloudPath))
                        continue
                    result = AppSyncResult.HOST_TO_CLOUD

                elif hp_mtime < cp_mtime:
                    if not replaceTree(cloudPath, hostPath):
                        print("\tSkip '{}' because it's locked.".format(hostPath))
                        continue
                    result = AppSyncResult.CLOUD_TO_HOST

                else:
                    result = AppSyncResult.EQUAL

            elif isHostExists and not isCloudExists:
                shutil.copytree(hostPath, cloudPath)
                result = AppSyncResult.HOST_TO_CLOUD

            elif not isHostExists and isCloudExists:
                shutil.copytree(cloudPath, hostPath)
                result = AppSyncResult.CLOUD_TO_HOST

            print("\t{}".format(getResultStr(result)))

            if result == AppSyncResult.CLOUD_TO_HOST or result == AppSyncResult.HOST_TO_CLOUD:
                syncHappened = True
                if callback is not None:
                    callback(self.name, result)

        if syncHappened:
            global g_numSyncedApps
            g_numSyncedApps += 1


def replaceTree(src, dst):
    # check access to 'dst' before removing
    try:
        os.rename(dst, dst + "_")
    except OSError as e:
        return False

    shutil.rmtree(dst + "_")
    shutil.copytree(src, dst)
    return True


def mainFunction(callback=None):

    jsonFile = open(getConfigPath(), 'r')
    jsonData = json.load(jsonFile)

    appsData = list()
    for app in jsonData:
        appsData.append(AppData(jsonData[app]))

    global g_numTotalApps
    g_numTotalApps = len(appsData)

    global g_numSyncedApps
    g_numSyncedApps = 0

    for app in appsData:
        app.syncConfig(callback)

    jsonFile.close()


if __name__ == "__main__":
    mainFunction()
