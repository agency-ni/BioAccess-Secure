"""
windows_integration.py — BioAccess Secure
Détection des événements session Windows (verrouillage / déverrouillage).

Utilisation :
    from windows_integration import WindowsSessionMonitor

    def on_unlock():
        # déclencher l'auth biométrique automatique
        ...

    monitor = WindowsSessionMonitor(on_unlock_callback=on_unlock)
    monitor.start()   # thread daemon — arrêt automatique à la fermeture de l'app
    monitor.stop()    # arrêt propre si nécessaire

Compatibilité : Windows uniquement.
Sur macOS/Linux, start() est un no-op silencieux.
"""

import sys
import logging
import threading
import platform

logger = logging.getLogger("bioaccess.windows_integration")

# ── Disponibilité Windows ─────────────────────────────────────────────────────
_WINDOWS = platform.system() == "Windows"

if _WINDOWS:
    try:
        import ctypes
        import ctypes.wintypes as _wt
        _CTYPES_OK = True
    except Exception:
        _CTYPES_OK = False
else:
    _CTYPES_OK = False


# ── Constantes WTS / Windows Messages ────────────────────────────────────────
WM_WTSSESSION_CHANGE    = 0x02B1
WTS_SESSION_LOCK        = 0x7
WTS_SESSION_UNLOCK      = 0x8

# Fenêtre invisible pour recevoir les messages Windows
_WNDCLASS_NAME = "BioAccessSessionWatcher"


class WindowsSessionMonitor:
    """
    Crée une fenêtre Windows invisible qui reçoit WM_WTSSESSION_CHANGE.
    Appelle on_lock_callback() quand la session se verrouille.
    Appelle on_unlock_callback() quand la session se déverrouille.
    """

    def __init__(self, on_unlock_callback=None, on_lock_callback=None):
        self._on_unlock = on_unlock_callback
        self._on_lock   = on_lock_callback
        self._thread    = None
        self._stop_evt  = threading.Event()
        self._hwnd      = None

    # ── API publique ──────────────────────────────────────────────────────────

    def start(self):
        """Démarre le monitor dans un thread daemon."""
        if not _WINDOWS or not _CTYPES_OK:
            logger.debug("WindowsSessionMonitor: non-Windows ou ctypes indisponible — ignoré")
            return
        self._thread = threading.Thread(
            target=self._message_loop, daemon=True, name="WinSessionMonitor"
        )
        self._thread.start()
        logger.info("WindowsSessionMonitor démarré")

    def stop(self):
        """Arrête le monitor proprement."""
        self._stop_evt.set()
        if self._hwnd:
            try:
                ctypes.windll.user32.PostMessageW(self._hwnd, 0x0012, 0, 0)  # WM_QUIT
            except Exception:
                pass

    # ── Boucle de messages Windows ────────────────────────────────────────────

    def _message_loop(self):
        """Tourne dans le thread daemon — crée une fenêtre cachée et pompe les messages."""
        try:
            user32   = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            wtsapi32 = ctypes.windll.wtsapi32

            WNDPROC = ctypes.WINFUNCTYPE(
                ctypes.c_long, _wt.HWND, _wt.UINT, _wt.WPARAM, _wt.LPARAM
            )

            def wnd_proc(hwnd, msg, wparam, lparam):
                if msg == WM_WTSSESSION_CHANGE:
                    if wparam == WTS_SESSION_UNLOCK:
                        logger.info("Session Windows déverrouillée — déclenchement auth biométrique")
                        if self._on_unlock:
                            threading.Thread(
                                target=self._on_unlock, daemon=True
                            ).start()
                    elif wparam == WTS_SESSION_LOCK:
                        logger.info("Session Windows verrouillée")
                        if self._on_lock:
                            threading.Thread(
                                target=self._on_lock, daemon=True
                            ).start()
                    return 0
                if msg == 0x0002:  # WM_DESTROY
                    user32.PostQuitMessage(0)
                    return 0
                return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

            _proc = WNDPROC(wnd_proc)

            class WNDCLASSEXW(ctypes.Structure):
                _fields_ = [
                    ("cbSize",        ctypes.c_uint),
                    ("style",         ctypes.c_uint),
                    ("lpfnWndProc",   WNDPROC),
                    ("cbClsExtra",    ctypes.c_int),
                    ("cbWndExtra",    ctypes.c_int),
                    ("hInstance",     _wt.HANDLE),
                    ("hIcon",         _wt.HANDLE),
                    ("hCursor",       _wt.HANDLE),
                    ("hbrBackground", _wt.HANDLE),
                    ("lpszMenuName",  _wt.LPCWSTR),
                    ("lpszClassName", _wt.LPCWSTR),
                    ("hIconSm",       _wt.HANDLE),
                ]

            hinstance = kernel32.GetModuleHandleW(None)
            wc = WNDCLASSEXW()
            wc.cbSize        = ctypes.sizeof(WNDCLASSEXW)
            wc.lpfnWndProc   = _proc
            wc.hInstance     = hinstance
            wc.lpszClassName = _WNDCLASS_NAME

            user32.RegisterClassExW(ctypes.byref(wc))

            hwnd = user32.CreateWindowExW(
                0, _WNDCLASS_NAME, "BioAccess Session Watcher",
                0, 0, 0, 0, 0,
                -3,  # HWND_MESSAGE — fenêtre message-only (invisible)
                None, hinstance, None,
            )
            if not hwnd:
                logger.error("Impossible de créer la fenêtre message Windows")
                return

            self._hwnd = hwnd

            # S'abonner aux notifications de session WTS
            try:
                wtsapi32.WTSRegisterSessionNotification(hwnd, 0)  # NOTIFY_FOR_THIS_SESSION
            except Exception as e:
                logger.warning(f"WTSRegisterSessionNotification: {e}")

            # Boucle de messages
            class MSG(ctypes.Structure):
                _fields_ = [
                    ("hwnd",    _wt.HWND),
                    ("message", _wt.UINT),
                    ("wParam",  _wt.WPARAM),
                    ("lParam",  _wt.LPARAM),
                    ("time",    _wt.DWORD),
                    ("pt",      _wt.POINT),
                ]

            msg = MSG()
            while not self._stop_evt.is_set():
                ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if ret == 0 or ret == -1:
                    break
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))

            try:
                wtsapi32.WTSUnRegisterSessionNotification(hwnd)
            except Exception:
                pass
            user32.DestroyWindow(hwnd)
            user32.UnregisterClassW(_WNDCLASS_NAME, hinstance)

        except Exception as e:
            logger.error(f"WindowsSessionMonitor._message_loop: {e}", exc_info=True)


# ── Polling fallback (si WTS échoue) ─────────────────────────────────────────

class WindowsSessionPolling:
    """
    Alternative légère qui poll l'état de la session toutes les 2 secondes
    via GetSystemMetrics(SM_REMOTESESSION) et OpenInputDesktop().
    À utiliser si WindowsSessionMonitor ne peut pas démarrer.
    """

    def __init__(self, on_unlock_callback=None, on_lock_callback=None, interval=2.0):
        self._on_unlock = on_unlock_callback
        self._on_lock   = on_lock_callback
        self._interval  = interval
        self._thread    = None
        self._stop_evt  = threading.Event()
        self._was_locked = False

    def start(self):
        if not _WINDOWS or not _CTYPES_OK:
            return
        self._thread = threading.Thread(
            target=self._poll_loop, daemon=True, name="WinSessionPoller"
        )
        self._thread.start()

    def stop(self):
        self._stop_evt.set()

    def _is_locked(self) -> bool:
        """Retourne True si la session est verrouillée."""
        try:
            hdesk = ctypes.windll.user32.OpenInputDesktop(0, False, 0x0100)
            if not hdesk:
                return True
            ctypes.windll.user32.CloseDesktop(hdesk)
            return False
        except Exception:
            return False

    def _poll_loop(self):
        while not self._stop_evt.wait(self._interval):
            locked = self._is_locked()
            if locked and not self._was_locked:
                self._was_locked = True
                logger.info("Session verrouillée (polling)")
                if self._on_lock:
                    threading.Thread(target=self._on_lock, daemon=True).start()
            elif not locked and self._was_locked:
                self._was_locked = False
                logger.info("Session déverrouillée (polling) — déclenchement auth")
                if self._on_unlock:
                    threading.Thread(target=self._on_unlock, daemon=True).start()
