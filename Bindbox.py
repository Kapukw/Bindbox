import socket
import shutil
import json
import os, time
from stat import *

import psutil

# user config
g_cloud_dir = os.path.normcase("Dropbox/Bindbox/")
g_paths_file = "paths.json"

def get_host_name():
    return socket.gethostname()

def get_config_path():
    path = os.path.join(os.path.expanduser("~"), g_cloud_dir, g_paths_file)
    return path

def get_cloud_path():
    path = os.path.join(os.path.expanduser("~"), g_cloud_dir)
    return path

def list_processes():
    proc_names = list()
    for proc in psutil.process_iter():
        try: proc_name = proc.name()
        except psutil.NoSuchProcess: pass
        else: proc_names.append(proc_name)
    return proc_names

def get_tree_mtime(top):
    mtime = os.stat(top).st_mtime
    new_mtime = mtime
    for f in os.listdir(top):
        path = os.path.join(top, f)
        mode = os.stat(path).st_mode
        if S_ISDIR(mode): new_mtime = get_tree_mtime(path)
        elif S_ISREG(mode): new_mtime = os.stat(path).st_mtime
        else: print 'Skipping %s' % path
        if new_mtime > mtime: mtime = new_mtime
    return mtime

class AppSyncResult:
    SYNCED = 0
    CLOUD_TO_HOST = 1
    HOST_TO_CLOUD = 2

class AppData:
    def __init__(self, json_dict):
        self.name = json_dict['name']
        self.proc_names = json_dict['proc_names']
        self.paths = json_dict['paths'][get_host_name()]

    def sync_config(self, callback=None):
        print(self.name + ":")

        for proc_name in self.proc_names:
            if proc_name in list_processes():
                print("Skip '" + self.name + "' because it's running.")
                return

        if self.paths != []:
            for i in range(0, len(self.paths)):

                host_path = self.paths[i]
                cloud_path = os.path.join(get_cloud_path(), self.name, str(i), "")

                host_exists = os.path.exists(host_path)
                cloud_exists = os.path.exists(cloud_path)

                result = None
                result_str = None

                if host_exists and cloud_exists:

                    hp_mtime = int(get_tree_mtime(host_path))
                    print("\thost modified: %s" % time.ctime(hp_mtime))

                    cp_mtime = int(get_tree_mtime(cloud_path))
                    print("\tcloud modified: %s" % time.ctime(cp_mtime))

                    if hp_mtime > cp_mtime:
                        shutil.rmtree(cloud_path)
                        shutil.copytree(host_path, cloud_path)
                        result = AppSyncResult.HOST_TO_CLOUD
                        result_str = "host -> cloud"
                    
                    elif hp_mtime < cp_mtime:
                        shutil.rmtree(host_path)
                        shutil.copytree(cloud_path, host_path)
                        result = AppSyncResult.CLOUD_TO_HOST
                        result_str = "host <- cloud"

                    else:
                        result = AppSyncResult.SYNCED
                        result_str = "host == cloud"
                
                elif host_exists and not cloud_exists:
                    shutil.copytree(host_path, cloud_path)
                    result = AppSyncResult.HOST_TO_CLOUD
                    result_str = "host -> cloud"

                elif not host_exists and cloud_exists:
                    shutil.copytree(cloud_path, host_path)
                    result = AppSyncResult.CLOUD_TO_HOST
                    result_str = "host <- cloud"

                if result != None:
                    print("\t" + result_str)
                    if callback != None and result != AppSyncResult.SYNCED:
                        callback(self.name, result)

def main_func(callback=None):

    json_file = open(get_config_path(), 'r')
    json_data = json.load(json_file)

    apps_data = list()
    for app in json_data:
        apps_data.append(AppData(json_data[app]))

    for app in apps_data:
        app.sync_config(callback)

    json_file.close()

# execute
if __name__ == "__main__":
    main_func()
