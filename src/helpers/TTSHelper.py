import logging
from pycsspeechtts import pycsspeechtts

logger = logging.getLogger(__name__)

class TTSHelper():
    def say(self, text: str):
        filename = "/tmp/file.wav"
        t = pycsspeechtts.TTSTranslator("8390cea6edea4ef1989434e228092efc","westeurope")
        logger.debug(f"SAYING {text}")
        data = t.speak(language='pl-pl',gender='Female',voiceType='ZofiaNeural', output='riff-16khz-16bit-mono-pcm', text=text)
        with open(filename, "wb") as f:
            f.write(data)
        return filename
