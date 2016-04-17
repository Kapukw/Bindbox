import win32pipe, win32ts, win32api, pywintypes, struct, sys

def dropbox_path_status(pathname):
        return ['dropbox not running','not in dropbox','up to date','syncronising','sync problem'][dropbox_path_status_code(pathname)+1]

def dropbox_path_status_code(pathname):
        processid = win32api.GetCurrentProcessId()
        threadid = win32api.GetCurrentThreadId()
        request_type = 1
        wtf = 0x3048302
        pipename = r'\\.\PIPE\DropboxPipe_' + str(win32ts.ProcessIdToSessionId(processid))
        request = (struct.pack('LLLL', wtf, processid, threadid, request_type) + pathname.encode('utf-16') + (chr(0)*540))[0:540]
        try:
                response = win32pipe.CallNamedPipe(pipename, request, 16382, 1000)
        except pywintypes.error, err:
                if err[0] == 2:
                        return -1
                else:
                        raise
        else:
                return int(response[4:-1])

if __name__ == "__main__":
        if len(sys.argv) > 1:
                print dropbox_path_status(sys.argv[1])
        else:
                print >> sys.stderr, 'pathname required'