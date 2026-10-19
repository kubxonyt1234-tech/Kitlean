class Events:
    def __init__(self):
        self.handlers = {}
        self.registered = set()

    def register(self, name, event, callback, key=None):
        identity = (name, event, key)
        if key is not None:
            if identity in self.registered:
                return
            self.registered.add(identity)
        self.handlers.setdefault((name, event), []).append(callback)

    def emit(self, element, event):
        if not element.properties["visible"] or element.properties["disabled"]:
            return
        for callback in list(self.handlers.get((element.name, event), [])):
            callback()
