import math

from .errors import KitleanError


class Delay:
    def __init__(self, seconds):
        self.seconds = seconds

    def __await__(self):
        yield self


class GuiWait:
    def __await__(self):
        yield self


class Scheduler:
    def __init__(self, runtime):
        self.runtime = runtime
        self.jobs = {}
        self.coroutines = set()
        self.active = set()
        self.want_loop = False

    def seconds(self, value, line):
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise KitleanError("Czas musi być skończoną nieujemną liczbą sekund", line)
        return value

    def later(self, seconds, callback):
        self.runtime.windows.ensure()
        token = None

        def fire():
            self.jobs.pop(token, None)
            try:
                callback()
            except Exception as e:
                self.runtime.windows.callback_error(type(e), e, e.__traceback__)

        token = self.runtime.windows.root.after(max(1, round(seconds * 1000)), fire)
        self.jobs[token] = callback
        return token

    def cancel(self, token):
        if token in self.jobs:
            self.jobs.pop(token)
            if self.runtime.windows.root is not None:
                self.runtime.windows.root.after_cancel(token)

    def submit(self, coroutine):
        if self.runtime.closed:
            coroutine.close()
            return
        self.coroutines.add(coroutine)
        self.step(coroutine)

    def step(self, coroutine):
        self.active.add(coroutine)
        try:
            request = coroutine.send(None)
            if isinstance(request, Delay):
                self.later(request.seconds, lambda: self.step(coroutine))
            elif not isinstance(request, GuiWait):
                raise RuntimeError("Nieznane żądanie planisty")
        except StopIteration:
            self.coroutines.discard(coroutine)
        except BaseException:
            self.coroutines.discard(coroutine)
            coroutine.close()
            raise
        finally:
            self.active.discard(coroutine)
        if (
            not self.coroutines
            and not self.jobs
            and not self.want_loop
            and self.runtime.windows.root is not None
        ):
            self.runtime.windows.root.quit()

    def close(self):
        for token in list(self.jobs):
            self.cancel(token)
        for coroutine in self.coroutines - self.active:
            coroutine.close()
        self.coroutines.intersection_update(self.active)
        self.want_loop = False
