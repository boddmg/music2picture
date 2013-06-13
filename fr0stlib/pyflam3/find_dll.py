import sys
import os
import ctypes


def find_dll(name, omit_lib_in_windows=False, windows_uses_stdcall=False):
    if 'win32' not in sys.platform:
        name += '.so'

        try:
            return ctypes.CDLL(os.path.join('fr0stlib', 'pyflam3', 'linux_so', name))
        except OSError:
            return ctypes.CDLL(name)
    else:
        name += '.dll'

        dll_dir = os.getcwd()
        dll_type = ctypes.CDLL if not windows_uses_stdcall else ctypes.WinDLL

        try:
            if os.path.exists(os.path.join(dll_dir, name)):
                return dll_type(name)
            else:
                dll_dir = os.path.join(os.path.dirname(__file__), 'win32_dlls')
                sys_path = os.environ['PATH']
                os.environ['PATH'] = ';'.join((sys_path, dll_dir))
                return dll_type(name)
        except WindowsError:
            print >>sys.stderr, 'ERROR: Unable to load "%s" from "%s"' % (dll_name, dll_dir)
            raise

