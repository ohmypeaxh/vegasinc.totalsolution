"""Cross-process single-instance protection for desktop execution."""

from __future__ import annotations

import ctypes
import sys
from pathlib import Path

from PySide6.QtCore import QLockFile

WINDOWS_MUTEX_NAME = "VegasTotalSolutionDoc.SingleInstance"
_ERROR_ALREADY_EXISTS = 183


class SingleInstanceGuard:
    """Own a Windows mutex or Qt lock file for one running process."""

    def __init__(self, data_directory: Path) -> None:
        data_directory.mkdir(parents=True, exist_ok=True)
        self._lock = QLockFile(str(data_directory / "VegasTotalSolutionDoc.lock"))
        self._lock.setStaleLockTime(30_000)
        self._acquired = False
        self._mutex_handle: int | None = None
        self._kernel32 = None

    def acquire(self, timeout_ms: int = 100) -> bool:
        """Try to own the platform lock without delaying startup."""

        if self._acquired:
            return True
        if sys.platform == "win32":
            self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            create_mutex = self._kernel32.CreateMutexW
            create_mutex.argtypes = (ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p)
            create_mutex.restype = ctypes.c_void_p
            self._kernel32.CloseHandle.argtypes = (ctypes.c_void_p,)
            self._kernel32.CloseHandle.restype = ctypes.c_bool
            ctypes.set_last_error(0)
            handle = create_mutex(None, False, WINDOWS_MUTEX_NAME)
            if not handle:
                return False
            if ctypes.get_last_error() == _ERROR_ALREADY_EXISTS:
                self._kernel32.CloseHandle(handle)
                return False
            self._mutex_handle = int(handle)
            self._acquired = True
            return True
        self._acquired = self._lock.tryLock(timeout_ms)
        return self._acquired

    def release(self) -> None:
        """Release an acquired platform lock."""

        if not self._acquired:
            return
        if self._mutex_handle is not None and self._kernel32 is not None:
            self._kernel32.CloseHandle(ctypes.c_void_p(self._mutex_handle))
            self._mutex_handle = None
        else:
            self._lock.unlock()
        self._acquired = False

    def __enter__(self) -> "SingleInstanceGuard":
        if not self.acquire():
            raise RuntimeError("Vegas Total Solution Doc is already running")
        return self

    def __exit__(self, *_args: object) -> None:
        self.release()
