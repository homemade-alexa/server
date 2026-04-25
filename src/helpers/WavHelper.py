import wave


class WavHelper:
    @staticmethod
    def get_duration(filename: str) -> float:
        with wave.open(filename, 'rb') as f:
            return f.getnframes() / float(f.getframerate())
