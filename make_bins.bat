C:\Python36\python.exe make_bins.py build_exe
rmdir "%HOMEDRIVE%%HOMEPATH%\Dropbox\BindboxApp" /S /Q
xcopy "build\exe.win-amd64-3.6" "%HOMEDRIVE%%HOMEPATH%\Dropbox\BindboxApp" /S /I /Q /Y
pause
