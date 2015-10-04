python make_bins.py build
rmdir "%HOMEDRIVE%%HOMEPATH%\Dropbox\BindboxApp" /S /Q
xcopy "build\exe.win-amd64-2.7" "%HOMEDRIVE%%HOMEPATH%\Dropbox\BindboxApp" /S /I /Q /Y
pause