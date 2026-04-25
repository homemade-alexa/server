import requests, uuid, json

key = "d8c6807ceecc429e814ee8c011e7e0ea"
endpoint = "https://api.cognitive.microsofttranslator.com"
location = "westeurope"
path = '/translate'


class Translator:
    def translate(self, phrase: str):
        constructed_url = endpoint + path
        params = {
            'api-version': '3.0',
            'from': 'en',
            'to': ['pl']
        }

        headers = {
            'Ocp-Apim-Subscription-Key': key,
            'Ocp-Apim-Subscription-Region': location,
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }

        body = [{
            'text': phrase
        }]

        request = requests.post(constructed_url, params=params, headers=headers, json=body)
        response = request.json()
        return response[0]['translations'][0]['text']
