import flask
from flask import Flask, render_template, app, request, redirect, session, make_response
from flask.helpers import flash
import requests
import json
import datetime
from datetime import datetime, timedelta, time
from pytz import timezone
import pytz
from dateutil.parser import parse, parser
from concurrent.futures import ThreadPoolExecutor


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
    print(request.headers)
    print(request.data)

    url = f"https://api.bigdatacloud.net/data/reverse-geocode-with-timezone?latitude={lat}&longitude={long}&localityLanguage=en&key=7fb45ca5cb3a40a690064cd6cf037829"
    geo_data = requests.request("GET", url)
    geo_data = geo_data.text
    geo_data = json.loads(geo_data)
    time = geo_data["timeZone"]["localTime"]
    time_iso = datetime.fromisoformat(time[:-1])
    time_str = time_iso.strftime("%I:%M %p")
    #print(geo_data)

    time_iso_utc = time_iso.astimezone(pytz.utc)
    time_iso_utc_24 = time_iso_utc + timedelta(hours=24)
    time_iso_utc_7 = time_iso_utc + timedelta(days=7)
    #print(time_iso_utc_24)
    #print(time_iso_utc_7)

    us_system_countries = ["United States of America", "Liberia", "Myanmar"]

    if geo_data["countryName"] in us_system_countries:
        unit_system = "us"
    else:
        unit_system = "si"


    def weather_now(lat, long, unit_system):
        url = "https://api.climacell.co/v3/weather/realtime"
        querystring = {"lat":f"{lat}","lon":f"{long}","unit_system":f"{unit_system}","fields":"temp,feels_like,dewpoint,humidity,wind_speed,wind_direction,wind_gust,baro_pressure,precipitation,precipitation_type,sunrise,sunset,visibility,cloud_cover,cloud_base,cloud_ceiling,surface_shortwave_radiation,moon_phase,weather_code","apikey":"Pjj20stQZPi2r58kgyUq3JsHtyy2QbsU"}
        weather_now = requests.request("GET", url, params=querystring)
        weather_now = weather_now.text
        weather_now_info = json.loads(weather_now)
        #print(weather_now_info)
        return weather_now_info
    
    
    def weather_hourly(lat, long, unit_system):
        url = "https://api.climacell.co/v3/weather/forecast/hourly"
        querystring = {"lat":f"{lat}","lon":f"{long}","unit_system":f"{unit_system}","start_time":"now","end_time":f"{time_iso_utc_24}","fields":"temp,feels_like,dewpoint,humidity,wind_speed,wind_direction,wind_gust,baro_pressure,precipitation,precipitation_type,precipitation_probability,sunrise,sunset,visibility,cloud_cover,cloud_base,cloud_ceiling,surface_shortwave_radiation,moon_phase,weather_code","apikey":"Pjj20stQZPi2r58kgyUq3JsHtyy2QbsU"}
        weather_hourly = requests.request("GET", url, params=querystring)
        weather_hourly = weather_hourly.text
        weather_hourly_info = json.loads(weather_hourly)
        #print(weather_hourly_info)
        return weather_hourly_info
        


    """def weather_daily(lat, long, unit_system):
        url = "https://api.climacell.co/v3/weather/forecast/daily"
        querystring = {"lat":f"{lat}","lon":f"{long}","unit_system":f"{unit_system}","start_time":"now","end_time":f"{time_iso_utc_7}","fields":"precipitation,precipitation_accumulation,temp,feels_like,wind_speed,baro_pressure,visibility,humidity,wind_direction,sunrise,sunset,moon_phase,weather_code","apikey":"Pjj20stQZPi2r58kgyUq3JsHtyy2QbsU"}
        weather_daily = requests.request("GET", url, params=querystring)
        weather_daily = weather_daily.text
        weather_daily_info = json.loads(weather_daily)
        #print(weather_daily_info)
        return weather_daily_info"""


    executor = ThreadPoolExecutor(max_workers=5)
    weather_now_thread = executor.submit(weather_now, lat, long, unit_system)
    weather_hourly_thread = executor.submit(weather_hourly, lat, long, unit_system)
    #weather_daily_thread = executor.submit(weather_daily, lat, long, unit_system)
    weather_now_info = weather_now_thread.result()
    weather_hourly_info = weather_hourly_thread.result()
    #weather_daily_info = weather_daily_thread.result()


    weather_code_now = weather_now_info["weather_code"]["value"]
    special_weather_codes = ["partly_cloudy", "mostly_clear", "clear"]

    if weather_code_now in special_weather_codes:
        if 6 <= time_iso.hour < 21:
            weather_code_now = weather_code_now + "_day"
        else:
            weather_code_now = weather_code_now + "_night"


    return {"html_content": render_template("weather_now.html", weather_now_info=weather_now_info, weather_code_now=weather_code_now, time_str=time_str, geo_data=geo_data, weather_hourly_info=weather_hourly_info), "html_content2": render_template("weather_daily.html")}


if __name__=="__main__":
    app.run(debug=True)