class Events:
    def __init__(self):
        self.handlers = {}

    def register(self, name, event, callback):
        self.handlers.setdefault((name, event), []).append(callback)

    def emit(self, element, event):
        if not element.properties["visible"] or element.properties["disabled"]:
            return
        for callback in list(self.handlers.get((element.name, event), [])):
            callback()
