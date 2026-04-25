import itertools
import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class PartialMatcher():
    def __init__(self, partials: []):
        self.partials = partials

    def matches(self, phrase: str) -> bool:
        if isinstance(self.partials[0], str):
            for p in self.partials:
                if self.check_match(p, phrase):
                    return True
        else:
            for element in itertools.product(*self.partials):
                p = ' '.join(element).strip()
                if self.check_match(p, phrase):
                    return True
        return False

    @staticmethod
    def check_match(p: str, phrase: str):
        p = ' '.join(p.split())  # to remove double spaces
        s = SequenceMatcher(None, phrase.rstrip(',.? '), p)
        # logger.debug(f"{phrase} == {p}: {s.ratio()}")
        if s.ratio() > 0.9:
            logger.debug(f"Match found: {p}")
            return True
        return False
