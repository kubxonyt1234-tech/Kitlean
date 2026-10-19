import os

from .errors import KitleanError


class Audio:
    """Niezależny kanał dla każdego utworu; ponowne play nie nakłada kopii."""

    def __init__(self):
        self.items = {}
        self.mixer = None

    def ensure(self, line):
        if self.mixer is None:
            try:
                os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
                import pygame.mixer

                pygame.mixer.init()
                self.mixer = pygame.mixer
            except Exception as e:
                raise KitleanError(
                    "Nie można uruchomić audio: " + str(e), line
                ) from None

    def command(self, action, element, path, line):
        name = element.name
        if action == "play":
            if not path.is_file():
                raise KitleanError("Brak pliku audio: " + str(path), line)
            if path.suffix.lower() not in (".mp3", ".wav", ".ogg"):
                raise KitleanError("Audio wymaga MP3, WAV lub OGG", line)
            self.ensure(line)
            previous = self.items.get(name)
            if previous and previous[0] == path and previous[2].get_busy():
                return
            try:
                if previous:
                    previous[2].stop()
                sound = self.mixer.Sound(str(path))
                sound.set_volume(element.properties["volume"] / 100)
                channel = sound.play(loops=-1 if element.properties["loop"] else 0)
                if channel is None:
                    raise ValueError("Brak wolnego kanału audio")
                self.items[name] = (path, sound, channel)
            except Exception as e:
                raise KitleanError("Błąd odtwarzania audio: " + str(e), line) from None
        elif name in self.items:
            channel = self.items[name][2]
            {"pause": channel.pause, "resume": channel.unpause, "stop": channel.stop}[
                action
            ]()

    def change(self, element, prop):
        previous = self.items.get(element.name)
        if previous:
            if prop == "volume":
                previous[1].set_volume(element.properties["volume"] / 100)
                previous[2].set_volume(1.0)
            elif prop in ("file", "loop"):
                previous[2].stop()
                self.items.pop(element.name, None)

    def close(self):
        for _, _, channel in self.items.values():
            channel.stop()
        self.items.clear()
        if self.mixer is not None:
            self.mixer.quit()
            self.mixer = None
