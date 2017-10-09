import os
import stat
import socket
import shutil
import time
import json
from tempfile import mkstemp

import psutil

# user config
g_cloudDir = os.path.normcase("Dropbox/Bindbox/")
g_pathsFile = "paths.json"

g_numTotalApps = None
g_numSyncedApps = None


def getHostName():
    return socket.gethostname()


def getSyncStats():
    if g_numTotalApps is None or g_numSyncedApps is None:
        return "..."
    return "{}/{}".format(g_numSyncedApps, g_numTotalApps)


def getConfigPath():
    return os.path.join(os.path.expanduser("~"), g_cloudDir, g_pathsFile)


def getCloudPath():
    return os.path.join(os.path.expanduser("~"), g_cloudDir)


def getCurrentProcesses():
    procNames = []
    for proc in psutil.process_iter():
        try:
            procName = proc.name()
        except psutil.NoSuchProcess:
            pass
        else:
            procNames.append(procName)
    return procNames


def getFolderModificationTime(dirPath):

    mtime = os.stat(dirPath).st_mtime

    for entry in os.listdir(dirPath):
        childPath = os.path.join(dirPath, entry)
        childMode = os.stat(childPath).st_mode
        if stat.S_ISDIR(childMode):
            mtime = max(mtime, getFolderModificationTime(childPath))
        elif stat.S_ISREG(childMode):
            mtime = max(mtime, os.stat(childPath).st_mtime)

    return mtime


def replaceTree(src, dst):
    # check access to 'dst' before removing
    try:
        os.rename(dst, dst + "_")
    except OSError as e:
        return False

    shutil.rmtree(dst + "_")
    shutil.copytree(src, dst)
    return True


def copyTree(src, dst):
    shutil.copytree(src, dst)


class AppSyncResult(object):
    NOT_SYNCED = 0
    EQUAL = 1
    CLOUD_TO_HOST = 2
    HOST_TO_CLOUD = 3


def getSyncPaths(jsonDict):
    if 'paths' not in jsonDict:
        return []
    currentHostName = getHostName()
    for hostName in jsonDict['paths']:
        if str(currentHostName).lower() == str(hostName).lower():
            return jsonDict['paths'][hostName]
    return []


# Sync all files and subfolders.
def syncEntireFolder(hostPath, cloudPath):

    syncResult = AppSyncResult.NOT_SYNCED

    isHostExists = os.path.exists(hostPath)
    isCloudExists = os.path.exists(cloudPath)

    if isHostExists and isCloudExists:

        hostModTime = int(getFolderModificationTime(hostPath))
        cloudModTime = int(getFolderModificationTime(cloudPath))

        print("\thost: {}\n\tcloud: {}\n\thost modified: {}\n\tcloud modified: {}".format(hostPath, cloudPath, time.ctime(hostModTime), time.ctime(cloudModTime)))

        if hostModTime > cloudModTime:
            if replaceTree(hostPath, cloudPath):
                syncResult = AppSyncResult.HOST_TO_CLOUD
            else:
                print("\tSkip '{}' because it's locked.".format(cloudPath))

        elif hostModTime < cloudModTime:
            if replaceTree(cloudPath, hostPath):
                syncResult = AppSyncResult.CLOUD_TO_HOST
            else:
                print("\tSkip '{}' because it's locked.".format(hostPath))

        else:
            syncResult = AppSyncResult.EQUAL

    elif isHostExists and not isCloudExists:
        copyTree(hostPath, cloudPath)
        syncResult = AppSyncResult.HOST_TO_CLOUD

    elif not isHostExists and isCloudExists:
        copyTree(cloudPath, hostPath)
        syncResult = AppSyncResult.CLOUD_TO_HOST

    resultStrings = { AppSyncResult.NOT_SYNCED    : "not synced",
                      AppSyncResult.EQUAL         : "host == cloud",
                      AppSyncResult.CLOUD_TO_HOST : "host <- cloud",
                      AppSyncResult.HOST_TO_CLOUD : "host -> cloud" }

    print("\t{}".format(resultStrings[syncResult]))

    return syncResult


# Sync all files by wildcard. Subfolders not included.
# All matched 'dest' files will be deleted and then replaced by 'source' files.
def syncByFileMask(fileMask, sourcePath, destPath):
    pass


class AppData(object):

    def __init__(self, jsonDict):
        self.name = jsonDict['name']
        self.procNames = jsonDict['proc_names'] if 'proc_names' in jsonDict else []
        self.paths = getSyncPaths(jsonDict)

    def syncConfig(self, callback=None):
        print("{}:".format(self.name))

        currentProcesses = getCurrentProcesses()
        for procName in self.procNames:
            if procName in currentProcesses:
                print("Skip '{}' because it's running.".format(self.name))
                return

        syncHappened = False

        for i in range(0, len(self.paths)):

            hostPath = os.path.normpath(os.path.expandvars(self.paths[i]))
            cloudPath = os.path.normpath(os.path.join(getCloudPath(), self.name, str(i), ""))

            result = syncEntireFolder(hostPath, cloudPath)

            if result == AppSyncResult.CLOUD_TO_HOST or result == AppSyncResult.HOST_TO_CLOUD:
                syncHappened = True
                if callback is not None:
                    callback(self.name, result)

        if syncHappened:
            global g_numSyncedApps
            g_numSyncedApps += 1


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
