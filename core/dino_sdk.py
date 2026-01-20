import ctypes
from typing import Callable, List, Tuple
import os

# Global variables
VID_POINTERS: int = 5
VID_PARAMS: int = 4
METHOD_SIGNATURES: dict = {
    "Init": ([], ctypes.c_bool),
    "EnableMicroTouch": ([ctypes.c_bool], ctypes.c_bool),
    "FOVx": ([ctypes.c_int, ctypes.c_double], ctypes.c_double),
    "GetAETarget": ([ctypes.c_int], ctypes.c_long),
    "GetAMR": ([ctypes.c_int], ctypes.c_double),
    "GetAutoExposure": ([ctypes.c_int], ctypes.c_long),
    "GetConfig": ([ctypes.c_int], ctypes.c_long),
    "GetDeviceId": ([ctypes.c_int], ctypes.c_wchar_p),
    "GetDeviceIDA": ([ctypes.c_int], ctypes.c_char_p),
    "GetExposureValue": ([ctypes.c_int], ctypes.c_long),
    "GetLensFinePosLimits": (
        [ctypes.c_long, ctypes.POINTER(ctypes.c_long), ctypes.POINTER(ctypes.c_long)],
        ctypes.c_long,
    ),
    "GetLensPosLimits": (
        [ctypes.c_long, ctypes.POINTER(ctypes.c_long), ctypes.POINTER(ctypes.c_long)],
        ctypes.c_long,
    ),
    "GetVideoDeviceCount": ([], ctypes.c_int),
    "GetVideoDeviceIndex": ([], ctypes.c_long),
    "GetVideoDeviceName": ([ctypes.c_int], ctypes.c_wchar_p),
    "GetVideoProcAmp": ([ctypes.c_long], ctypes.c_long),
    "GetVideoProcAmpValueRange": (
        [ctypes.POINTER(ctypes.c_long) for _ in range(VID_POINTERS)],
        ctypes.c_long,
    ),
    "GetWiFiVideoCaps": (
        [
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_short),
            ctypes.POINTER(ctypes.c_short),
        ],
        ctypes.c_bool,
    ),
    "SetAETarget": ([ctypes.c_int, ctypes.c_long], None),
    "SetAutoExposure": ([ctypes.c_int, ctypes.c_long], None),
    "SetAimpointLevel": ([ctypes.c_int, ctypes.c_long], None),
    "SetAXILevel": ([ctypes.c_int, ctypes.c_long], None),
    "SetExposureValue": ([ctypes.c_int, ctypes.c_long], None),
    "SetEFLC": ([ctypes.c_int, ctypes.c_long, ctypes.c_long], None),
    "SetFLCSwitch": ([ctypes.c_int, ctypes.c_long], None),
    "SetFLCLevel": ([ctypes.c_int, ctypes.c_long], None),
    "SetLEDState": ([ctypes.c_int, ctypes.c_long], None),
    "SetLensInitPos": ([ctypes.c_int], None),
    "SetLensFinePos": ([ctypes.c_int, ctypes.c_long], None),
    "SetLensPos": ([ctypes.c_int, ctypes.c_long], None),
    "SetVideoDeviceIndex": ([ctypes.c_int], None),
    "SetVideoProcAmp": ([ctypes.c_long], None),
    "SetEventCallback": ([ctypes.CFUNCTYPE(None)], None),
}


class DNX64:
    def __init__(self, dll_path: str = "DNX64.dll") -> None:
        """
        Initialize the DNX64 class.

        Parameters:
            dll_path (str): Path to the DNX64.dll library file.
        """
        # Try to find DLL in current directory if not absolute path
        if not os.path.isabs(dll_path):
            dll_path = os.path.abspath(dll_path)
            
        if not os.path.exists(dll_path):
            print(f"WARNING: DNX64.dll not found at {dll_path}. MicroTouch features will be disabled.")
            self.dnx64 = None
            return

        try:
            self.dnx64 = ctypes.CDLL(dll_path)
            self.setup()
        except OSError as e:
            print(f"Error loading DNX64.dll: {e}")
            self.dnx64 = None

    def setup(self) -> None:
        """
        Set up the signatures for DNX64.dll methods using dictionary constant.
        """
        if not self.dnx64: return
        
        for method_name, (argtypes, restype) in METHOD_SIGNATURES.items():
            try:
                func = getattr(self.dnx64, method_name)
                func.argtypes = argtypes
                func.restype = restype
            except AttributeError:
                # Some versions might miss functions
                pass

    def Init(self) -> bool:
        """
        Initialize control object.
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.dnx64: return False
        try:
            return self.dnx64.Init()
        except OSError as e:
            print(f"DNX64 Init Error: {e}")
            return False

    def EnableMicroTouch(self, flag: bool) -> bool:
        """
        Enable or disable the MicroTouch feature.
        """
        if not self.dnx64: return False
        return self.dnx64.EnableMicroTouch(flag)

    def SetEventCallback(self, external_callback: Callable) -> None:
        """
        Set callback function for MicroTouch pressed event.
        """
        if not self.dnx64: return
        
        # Keep reference to avoid GC
        self.EventCallback = ctypes.CFUNCTYPE(None)
        self.callback_func = self.EventCallback(external_callback)
        self.dnx64.SetEventCallback(self.callback_func)
