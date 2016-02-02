import os, socket, shutil, time, json
from tempfile import mkstemp
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

def copystat_recursive(src, dst):

    if S_ISDIR(os.stat(src).st_mode):
        src_entries = os.listdir(src)
        dst_entries = os.listdir(dst)
        count = len(src_entries)

        for i in xrange(0, count):
            copystat_recursive(os.path.join(src, src_entries[i]), os.path.join(dst, dst_entries[i]))

    shutil.copystat(src, dst)


def replace(file_path, pattern, subst):
    old_mtime = os.stat(file_path).st_mtime
    fh, abs_path = mkstemp()
    with open(abs_path,'w') as new_file:
        with open(file_path) as old_file:
            for line in old_file:
                new_file.write(line.replace(pattern, subst))
    os.close(fh)
    os.remove(file_path)
    shutil.move(abs_path, file_path)

def preprocess(src_dir, dst_dir, preprocess_dict, from_local, native):
    if preprocess_dict == None:
        return
    for var_name, file_names in preprocess_dict.iteritems():
        for file_name in file_names:

            src_path = os.path.join(src_dir, file_name)
            if not os.path.exists(src_path) or not os.path.isfile(src_path):
                continue

            dst_path = os.path.join(dst_dir, file_name)
            if not os.path.exists(dst_path) or not os.path.isfile(dst_path):
                continue

            var_value = os.path.expandvars(var_name)
            if native:
                var_value = var_value.replace('\\', '\\\\')
            else:
                var_value = var_value.replace('\\', '/')

            if from_local:
                pattern = var_value
                subst = var_name
            else:
                pattern = var_name
                subst = var_value

            print("replace " + dst_path + " " + pattern + " " + subst)
            replace(dst_path, pattern, subst)

    copystat_recursive(src_dir, dst_dir)

class AppSyncResult:
    SYNCED = 0
    CLOUD_TO_HOST = 1
    HOST_TO_CLOUD = 2

class AppData:
    def __init__(self, json_dict):
        self.name = json_dict['name']
        self.proc_names = json_dict['proc_names'] if 'proc_names' in json_dict else None
        self.paths = json_dict['paths'][get_host_name()]
        self.preprocess = json_dict['preprocess'] if 'preprocess' in json_dict else None
        self.preprocess_native = json_dict['preprocess_native'] if 'preprocess_native' in json_dict else None

    def sync_config(self, callback=None):
        print(self.name + ":")

        if self.proc_names != None:
            for proc_name in self.proc_names:
                if proc_name in list_processes():
                    print("Skip '" + self.name + "' because it's running.")
                    return

        if self.paths != []:
            for i in range(0, len(self.paths)):

                host_path = os.path.normpath(os.path.expandvars(self.paths[i]))
                print("\thost path: %s" % host_path)
                cloud_path = os.path.normpath(os.path.join(get_cloud_path(), self.name, str(i), ""))
                print("\tcloud path: %s" % cloud_path)

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

                if result == AppSyncResult.CLOUD_TO_HOST:
                    preprocess(cloud_path, host_path, self.preprocess, False, False)
                    preprocess(cloud_path, host_path, self.preprocess_native, False, True)

                elif result == AppSyncResult.HOST_TO_CLOUD:
                    preprocess(host_path, cloud_path, self.preprocess, True, False)
                    preprocess(host_path, cloud_path, self.preprocess_native, True, True)

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
