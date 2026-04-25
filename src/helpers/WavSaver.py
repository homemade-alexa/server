import datetime
import wave


class WavSaver:
    @staticmethod
    def write_wav(folder: str, data: bytearray, rates: int, bits: int, ch: int):
        t = datetime.datetime.utcnow()
        time = t.strftime('%Y%m%dT%H%M%SZ')
        filename = f'{folder}/{time}_{rates}_{bits}_{ch}.wav'

        wavfile = wave.open(filename, 'wb')
        wavfile.setparams((ch, int(bits / 8), rates, 0, 'NONE', 'NONE'))
        wavfile.writeframesraw(bytearray(data))
        wavfile.close()
        return filename
