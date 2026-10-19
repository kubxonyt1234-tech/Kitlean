from pathlib import Path
from unittest.mock import Mock

import pytest

from kitlean.errors import KitleanError
from kitlean.interpreter import Interpreter

ASSETS = Path(__file__).parents[1] / "examples/assets"


def test_audio_mock_no_overlap_and_reconfigure():
    i = Interpreter()
    r = i.runtime
    r.configure_program(ASSETS.parent / "music.kit")
    mixer = Mock()
    sound = mixer.Sound.return_value
    channel = sound.play.return_value
    channel.get_busy.return_value = True
    r.audio.mixer = mixer
    i.execute(
        "create audio/music\naudio.file/assets/music.wav\naudio.volume/50\naudio.loop/true\nplay audio\nplay audio\npause audio\nresume audio\naudio.volume/75\nstop audio"
    )
    sound.play.assert_called_once_with(loops=-1)
    channel.pause.assert_called_once()
    channel.unpause.assert_called_once()
    channel.stop.assert_called_once()
    sound.set_volume.assert_called_with(0.75)
    r.audio.close()
    mixer.quit.assert_called_once()


@pytest.mark.audio
@pytest.mark.parametrize("extension", ["wav", "mp3", "ogg"])
def test_audio_real_codecs(extension):
    i = Interpreter()
    r = i.runtime
    r.configure_program(ASSETS.parent / "music.kit")
    try:
        i.execute(
            f"create audio/music\naudio.file/assets/music.{extension}\naudio.volume/1\naudio.loop/true\nplay audio"
        )
        path, sound, channel = r.audio.items[r.get("audio").name]
        assert channel.get_busy()
        assert sound.get_length() > 1
        i.execute("play audio")
        assert r.audio.items[r.get("audio").name][2] is channel
        i.execute("pause audio\nresume audio\naudio.volume/75")
        assert abs(sound.get_volume() - 0.75) < 0.02
        i.execute("stop audio")
        assert not channel.get_busy()
    finally:
        r.cleanup()
    assert r.audio.mixer is None


def test_missing_corrupt_audio(tmp_path):
    i = Interpreter()
    i.runtime.configure_program(tmp_path / "program.kit")
    with pytest.raises(KitleanError):
        i.execute("create audio/music\naudio.file/missing.wav")
    (tmp_path / "bad.wav").write_text("broken", encoding="utf-8")
    try:
        i.execute("audio.file/bad.wav")
        with pytest.raises(KitleanError):
            i.execute("play audio")
    finally:
        i.runtime.cleanup()
