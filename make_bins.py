import sys
from cx_Freeze import setup, Executable

options = {
    'build_exe': {
        'optimize': 2,
        'include_msvcr': True,
        'zip_include_packages': ['*'],
        'zip_exclude_packages': [],
    }
}

gui_app_base = 'Win32GUI' if sys.platform == 'win32' else None
console_app_base = None

executables = [
    Executable('BindboxGUI.pyw', base=gui_app_base, icon='resources/icon.ico'),
    Executable('Bindbox.py', base=console_app_base)
]

setup(name='Bindbox',
      version='0.1.1',
      description='Bindbox Sync App',
      options=options,
      executables=executables)
