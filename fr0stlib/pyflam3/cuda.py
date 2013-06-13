import sys
from ctypes import *
from fr0stlib.pyflam3.find_dll import find_dll


__all__ = ['is_cuda_capable']


def is_cuda_capable():
    if 'win32' not in sys.platform:
        return False

    try:
        cudart = find_dll('cudart', omit_lib_in_windows=True, windows_uses_stdcall=True)
    except Exception:
        return False

    version = c_int()
    cudart.cudaDriverGetVersion(byref(version))

    return bool(version)



