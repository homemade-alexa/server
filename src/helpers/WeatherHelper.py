import datetime

import requests

API_KEY = "d58dfae82fca20596113a5bea4a0b5ff"
locationKey = 'poznan'
location = 'Poznan,PL'

"""{
    'coord': {
        'lon': 16.9299, 
        'lat': 52.4069
    }, 
    'weather': [
        {'id': 803, 'main': 'Clouds', 'description': 'zachmurzenie umiarkowane', 'icon': '04n'}
    ], 
    'base': 'stations', 
    'main': {
        'temp': 5.8, 
        'feels_like': 2.05, 
        'temp_min': 5.06, 
        'temp_max': 6.12, 
        'pressure': 1015, 
        'humidity': 63
    }, 
    'visibility': 10000, 
    'wind': {
        'speed': 5.66, 
        'deg': 240
    }, 
    'clouds': {'all': 75}, 
    'dt': 1706900145, 
    'sys': {
        'type': 2, 
        'id': 19661, 
        'country': 'PL', 
        'sunrise': 1706855592, 
        'sunset': 1706888311
    }, 
    'timezone': 3600, 
    'id': 3088171, 
    'name': 'Poznań', 
    'cod': 200
    }
"""


class WeatherHelper:
    def get_weather(self):
        res = requests.get(
            "http://api.openweathermap.org/data/2.5/weather?q={}&units=metric&APPID={}&lang=pl".format(location,
                                                                                                       API_KEY))
        weather = res.json()
        temperature = str(weather['main']['temp']).replace('.', ',')
        feels_like = str(weather['main']['feels_like']).replace('.', ',')
        humidity = weather['main']['humidity']
        pressure = weather['main']['pressure']
        desc = weather['weather'][0]['description']

        now = datetime.datetime.now()
        sunrise_ts = weather['sys']['sunrise']
        sunrise_dt = datetime.datetime.fromtimestamp(sunrise_ts)

        sun = ''
        if sunrise_dt > now:
            sun += 'słońce wzejdzie dziś o '
        else:
            sun += 'słońce wzeszło dziś o '
        sun += sunrise_dt.strftime("%H:%M")

        sunset_ts = weather['sys']['sunset']
        sunset_dt = datetime.datetime.fromtimestamp(sunset_ts)
        if sunset_dt > now:
            sun += ', a zajdzie o '
        else:
            sun += ', a zaszło o '
        sun += sunset_dt.strftime("%H:%M")

        w = f'Na dworze jest {temperature}°C. Temperatura odczuwalna to {feels_like}°. Wilgotność powietrza dochodzi do {humidity}%, a ciśnienie wynosi {pressure}hPa. {sun}. {desc}.'
        return w
