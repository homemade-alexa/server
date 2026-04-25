import logging
import requests

from helpers.Translator import Translator

logger = logging.getLogger(__name__)


class NinjaApi:
    def __init__(self):
        self.translator = Translator()

    def get_joke(self):
        joke = self.get_ninja('dadjokes', 'joke')
        logger.debug(f'Got joke: {joke}')
        return self.translator.translate(joke)

    def get_fact(self):
        fact = self.get_ninja('facts', 'fact')
        logger.debug(f'Got fact: {fact}')
        return 'Czy wiesz, że ' + self.translator.translate(fact) + '?'

    @staticmethod
    def get_ninja(resource: str, field: str):
        headers = {
            'authority': 'api.api-ninjas.com',
            'accept': '*/*',
            'accept-language': 'pl-PL,pl;q=0.7',
            'cache-control': 'no-cache',
            'origin': 'https://api-ninjas.com',
            'pragma': 'no-cache',
            'referer': 'https://api-ninjas.com/',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Brave";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'sec-gpc': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        res = requests.get('https://api.api-ninjas.com/v1/{}?limit=1'.format(resource), headers=headers).json()
        return res[0][field]
