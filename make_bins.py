import sys
from cx_Freeze import setup, Executable

gui_app_base = 'Win32GUI' if sys.platform == 'win32' else None
console_app_base = None

options = {
    'build_exe': {'includes': 'atexit', "include_msvcr": True}
}

executables = [
    Executable('BindboxGUI.pyw', base=gui_app_base, icon="resources/icon.ico"),
    Executable('Bindbox.py', base=console_app_base)
]

setup(name='Bindbox',
      version='0.1.0',
      description='Bindbox Sync App',
      options=options,
      executables=executables)
