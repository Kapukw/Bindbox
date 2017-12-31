rmdir "build" /S /Q
rmdir "dist" /S /Q
"C:\Program Files (x86)\Microsoft Visual Studio\Shared\Python36_64\Scripts\pyinstaller.exe" BindboxGUI.pyw --onefile --windowed --icon resources/icon.ico
rmdir "%HOMEDRIVE%%HOMEPATH%\Dropbox\BindboxApp" /S /Q
xcopy "dist" "%HOMEDRIVE%%HOMEPATH%\Dropbox\BindboxApp" /S /I /Q /Y
pause
