from flask import Flask, render_template, app, request
import requests
import json
import datetime
from datetime import datetime, timedelta
import pytz
from dateutil.parser import isoparse
from concurrent.futures import ThreadPoolExecutor
import itertools
import config


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/weather", methods=["POST"])
def post():
    byte_str = request.data
    cords = json.loads(byte_str)
    lat = cords["lat"]
    long = cords["long"]

    url = f"https://api.bigdatacloud.net/data/reverse-geocode-with-timezone?latitude={lat}&longitude={long}&localityLanguage=en&key={config.geolocation_api_key}"
    geo_data = requests.request("GET", url)
    geo_data = geo_data.text
    geo_data = json.loads(geo_data)
    time = geo_data["timeZone"]["localTime"]
    time_iso = datetime.fromisoformat(time[:-1])
    time_str = time_iso.strftime("%I:%M %p")
    #print(geo_data)

    time_iso_utc = time_iso.astimezone(pytz.utc)
    time_iso_utc_24 = time_iso_utc + timedelta(hours=24)
    time_iso_utc_48 = time_iso_utc + timedelta(hours=48)
    time_iso_utc_96 = time_iso_utc + timedelta(hours=96)
    time_iso_utc_7 = time_iso_utc + timedelta(days=7)
    time_iso_utc_15 = time_iso_utc + timedelta(days=14)
    #print(time_iso_utc_24)
    #print(time_iso_utc_7)

    us_system_countries = ["United States of America", "Liberia", "Myanmar"]

    if geo_data["countryName"] in us_system_countries:
        unit_system = "us"
    else:
        unit_system = "si"


    def weather_now(lat, long, unit_system):
        url = "https://api.climacell.co/v3/weather/realtime"
        querystring = {"lat":f"{lat}","lon":f"{long}","unit_system":f"{unit_system}","fields":"temp,feels_like,dewpoint,humidity,wind_speed,wind_direction,wind_gust,baro_pressure,precipitation,precipitation_type,sunrise,sunset,visibility,cloud_cover,cloud_base,cloud_ceiling,surface_shortwave_radiation,moon_phase,weather_code","apikey":f"{config.weather_api_key}"}
        weather_now = requests.request("GET", url, params=querystring)
        weather_now = weather_now.text
        weather_now_info = json.loads(weather_now)
        #print(weather_now_info)
        return weather_now_info
    
    
    def weather_hourly(lat, long, unit_system):
        url = "https://api.climacell.co/v3/weather/forecast/hourly"
        querystring = {"lat":f"{lat}","lon":f"{long}","unit_system":f"{unit_system}","start_time":"now","end_time":f"{time_iso_utc_48}","fields":"temp,feels_like,dewpoint,humidity,wind_speed,wind_direction,wind_gust,baro_pressure,precipitation,precipitation_type,precipitation_probability,sunrise,sunset,visibility,cloud_cover,cloud_base,cloud_ceiling,surface_shortwave_radiation,moon_phase,weather_code","apikey":f"{config.weather_api_key}"}
        weather_hourly = requests.request("GET", url, params=querystring)
        weather_hourly = weather_hourly.text
        #print(weather_hourly)
        weather_hourly_info = json.loads(weather_hourly)
        #print(weather_hourly_info)
        return weather_hourly_info
        


    def weather_daily(lat, long, unit_system):
        url = "https://api.climacell.co/v3/weather/forecast/daily"
        querystring = {"lat":f"{lat}","lon":f"{long}","unit_system":f"{unit_system}","start_time":"now","end_time":f"{time_iso_utc_15}","fields":"precipitation,precipitation_accumulation,temp,feels_like,wind_speed,baro_pressure,visibility,humidity,wind_direction,sunrise,sunset,moon_phase,weather_code","apikey":f"{config.weather_api_key}"}
        weather_daily = requests.request("GET", url, params=querystring)
        weather_daily = weather_daily.text
        #print(weather_daily)
        weather_daily_info = json.loads(weather_daily)
        #print(weather_daily_info)
        return weather_daily_info


    executor = ThreadPoolExecutor(max_workers=5)
    weather_now_thread = executor.submit(weather_now, lat, long, unit_system)
    weather_hourly_thread = executor.submit(weather_hourly, lat, long, unit_system)
    weather_daily_thread = executor.submit(weather_daily, lat, long, unit_system)
    weather_now_info = weather_now_thread.result()
    weather_hourly_info = weather_hourly_thread.result()
    weather_daily_info = weather_daily_thread.result()


    weather_code_now = weather_now_info["weather_code"]["value"]
    special_weather_codes = ["partly_cloudy", "mostly_clear", "clear"]  

    if weather_code_now in special_weather_codes:
        if 6 <= time_iso.hour < 21:
            weather_code_now = weather_code_now + "_day"
        else:
            weather_code_now = weather_code_now + "_night"

    for day in weather_daily_info:
        if day["weather_code"]["value"] in special_weather_codes:
            if 6 <= time_iso.hour < 21:
                day["weather_code"]["value"] += "_day"

    
    """today = weather_daily_info[0]['observation_time']["value"]
    tommorrow = weather_daily_info[1]['observation_time']["value"]
    next_day = weather_daily_info[2]['observation_time']["value"]
    next_next_day = weather_daily_info[3]['observation_time']["value"]
    today = datetime.strptime(today, "%Y-%m-%d")
    tommorrow = datetime.strptime(tommorrow, "%Y-%m-%d")
    next_day = datetime.strptime(next_day, "%Y-%m-%d")
    next_next_day = datetime.strptime(next_next_day, "%Y-%m-%d")
    today = today.strftime("%A, %B %d")
    tommorrow = tommorrow.strftime("%A, %B %d")
    next_day = next_day.strftime("%A, %B %d")
    next_next_day = next_next_day.strftime("%A, %B %d")
    print(today)
    print(tommorrow)
    print(next_day)
    print(next_next_day)
    hourly_day_list = [today, tommorrow, next_day, next_next_day]"""


    for hour in weather_hourly_info:
        houry = hour["observation_time"]["value"]
        houry = isoparse(houry)
        houry = houry.astimezone(pytz.timezone(geo_data["timeZone"]["ianaTimeId"]))
        #print(houry)


    for day in weather_daily_info:
        sunrise = day["sunrise"]["value"]
        sunset = day["sunset"]["value"]
        sunrise = isoparse(sunrise)
        sunset = isoparse(sunset)
        sunrise = sunrise.astimezone(pytz.utc)
        sunset = sunset.astimezone(pytz.utc)
        sunrise = sunrise.astimezone(pytz.timezone(geo_data["timeZone"]["ianaTimeId"]))
        sunset = sunset.astimezone(pytz.timezone(geo_data["timeZone"]["ianaTimeId"]))
        sunrise = sunrise.strftime("%I:%M %p")
        sunset = sunset.strftime("%I:%M %p")
        day["sunrise"]["value"] = sunrise
        day["sunset"]["value"] = sunset
        #print(day["sunrise"]["value"])
        #print(day["sunset"]["value"])

        dayy = day["observation_time"]["value"]
        dayy = datetime.strptime(dayy, "%Y-%m-%d")
        dayy = dayy.strftime("%a %d")
        day["observation_time"]["value"] = dayy
        #print(day["observation_time"]["value"])
       
    weather_daily_info[0]["observation_time"]["value"] = "Today"


    for hour in weather_hourly_info:
        observation_time = hour["observation_time"]["value"]
        observation_time = isoparse(observation_time)
        observation_time = observation_time.astimezone(pytz.utc)
        observation_time = observation_time.astimezone(pytz.timezone(geo_data["timeZone"]["ianaTimeId"]))
        #observation_time_str = observation_time.strftime("%Y-%m-%d")
        hour["observation_time"]["value"] = observation_time

        special_weather_codes = ["partly_cloudy", "mostly_clear", "clear"]
        weather_code_hourly = hour["weather_code"]["value"]

        if weather_code_hourly in special_weather_codes:
            if 6 <= observation_time.hour < 21:
                hour["weather_code"]["value"] += "_day"
            else:
                hour["weather_code"]["value"] += "_night"


    a = weather_hourly_info    
    weather_hourly_info = {k: list(vals) for k, vals in itertools.groupby(a, lambda val: val["observation_time"]["value"].date())}

    weather_current_hour = next(iter(weather_hourly_info.values()))[0]


    return {"html_content": render_template("weather_now.html", weather_now_info=weather_now_info, weather_code_now=weather_code_now, time_str=time_str, geo_data=geo_data, weather_current_hour=weather_current_hour), "html_content2": render_template("weather_daily.html", weather_daily_info=weather_daily_info, weather_hourly_info=weather_hourly_info), "html_content3": render_template("weather_hourly.html", weather_hourly_info=weather_hourly_info)}


if __name__=="__main__":
    app.run(debug=True)