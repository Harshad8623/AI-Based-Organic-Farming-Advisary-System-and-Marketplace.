"""Current observations and cautious farm guidance from OpenWeatherMap."""

from datetime import datetime, timezone
import math

import requests
from flask import Blueprint, render_template, request, flash, current_app
from flask_login import login_required

weather_bp = Blueprint('weather', __name__, url_prefix='/weather')

CITY_ALIASES = {
    'sambhajinagar': 'Aurangabad,IN',
    'aurangabad': 'Aurangabad,IN',
    'chhatrapati sambhajinagar': 'Aurangabad,IN',
    'ch. sambhajinagar': 'Aurangabad,IN',
    'prayagraj': 'Allahabad,IN', 'allahabad': 'Allahabad,IN',
    'baroda': 'Vadodara,IN', 'calcutta': 'Kolkata,IN',
    'madras': 'Chennai,IN', 'bombay': 'Mumbai,IN',
    'bengaluru': 'Bangalore,IN', 'bangalore': 'Bangalore,IN',
}


class WeatherUnavailable(Exception):
    """The provider cannot supply a valid current observation."""


def _resolve_city(city):
    return CITY_ALIASES.get(city.lower().strip(), city.strip())


def _advice(temp, humidity, rain_mm, description, wind_speed=0):
    """Return translation keys, never a forecast inferred from cloud cover."""
    tips = ['advice_check_soil']
    description = description.lower()
    if rain_mm > 0 or 'rain' in description or 'drizzle' in description:
        tips.append('advice_rain')
    if temp > 35:
        tips.append('advice_heat')
    elif temp < 15:
        tips.append('advice_cool')
    if humidity > 80:
        tips.append('advice_humid')
    if wind_speed >= 5:
        tips.append('advice_wind')
    if 'storm' in description or 'thunder' in description:
        tips.append('advice_storm')
    return tips


def _number(value, lower, upper):
    value = float(value)
    if not math.isfinite(value) or not lower <= value <= upper:
        raise ValueError('Invalid weather observation')
    return value


def _fetch_weather(city):
    """Return a genuine observation or raise; never fabricate fallback data."""
    api_key = (current_app.config.get('OPENWEATHER_API_KEY', '') or '').strip()
    if not api_key:
        raise WeatherUnavailable('Weather service is not available right now.')
    owm_city = _resolve_city(city)
    if ',' not in owm_city:
        owm_city += ',IN'
    response = requests.get(
        'https://api.openweathermap.org/data/2.5/weather',
        params={'q': owm_city, 'appid': api_key, 'units': 'metric'}, timeout=10,
    )
    if response.status_code == 404:
        raise WeatherUnavailable('City not found. Try a nearby town or city and country code.')
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError('Invalid weather response')
    rain = data.get('rain')
    if rain is None:
        rain = {}
    if not isinstance(rain, dict):
        raise ValueError('Invalid rain observation')
    observed = datetime.fromtimestamp(_number(data['dt'], 0, 4102444800), timezone.utc)
    age_seconds = (datetime.now(timezone.utc) - observed).total_seconds()
    if age_seconds < -600 or age_seconds > 10800:
        raise WeatherUnavailable('The weather observation is out of date. Please try again later.')
    return {
        'city': str(data['name']), 'country': str(data['sys']['country']),
        'temp': round(_number(data['main']['temp'], -90, 65), 1),
        'feels_like': round(_number(data['main']['feels_like'], -100, 80), 1),
        'humidity': _number(data['main']['humidity'], 0, 100),
        'description': str(data['weather'][0]['description']).title(),
        'wind_speed': round(_number(data['wind']['speed'], 0, 150), 1),
        'rain_mm': round(_number(rain.get('1h', 0), 0, 1000), 1),
        'observed_at': observed.isoformat(),
        'observed_label': observed.strftime('%d %b %Y, %H:%M UTC'),
        'source': 'OpenWeatherMap',
    }


@weather_bp.route('/', methods=['GET', 'POST'])
@login_required
def advisory():
    weather, tips, error = None, [], None
    city = request.values.get('city', '').strip()
    configured = bool((current_app.config.get('OPENWEATHER_API_KEY', '') or '').strip())
    if request.method == 'POST' or city:
        if not city or len(city) > 120:
            error = 'weather_city_invalid'
        elif not configured:
            error = 'weather_unavailable'
        else:
            try:
                weather = _fetch_weather(city)
                tips = _advice(weather['temp'], weather['humidity'], weather['rain_mm'],
                               weather['description'], weather['wind_speed'])
            except WeatherUnavailable as exc:
                # These exceptions contain only our own safe public messages.
                flash(str(exc), 'warning')
                error = 'weather_request_failed'
            except (requests.RequestException, ValueError, KeyError, TypeError, IndexError, OverflowError):
                # Do not expose exception URLs, which can contain API credentials.
                error = 'weather_request_failed'
    return render_template('weather/advisory.html', weather=weather, tips=tips,
                           city=city, weather_error=error, weather_configured=configured)
