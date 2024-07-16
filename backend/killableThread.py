from collections.abc import Callable
import threading
import ctypes


class Thread(threading.Thread):
    def __init__(self, target: Callable[[], None]):
        threading.Thread.__init__(self, daemon=True)
        self.fn = target

    def run(self):

        # target function of the thread class
        try:
            self.fn()
        except SystemExit:
            print("intentional exit")
        except Exception as e:
            print(e)
            pass

    def get_id(self) -> int | None:
        # returns id of the respective thread
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def terminate(self):
        thread_id = self.get_id()
        if thread_id is None:
            return
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), 0)
            print('Exception raise failure')
