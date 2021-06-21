# Manav-Weather-Website

Example Website Link: https://manav-weather.herokuapp.com/

All you need to do to run your own version of this website is just clone the repository to your lcoal machine, run `python -m venv venv` to create a virtual environment, activate it by running `. venv/Scripts/activate` & then run `pip install requirements.txt`. Then go to https://developer.climacell.co/dashboard, sign up & then copy the api key. Make a `config.py` file & create a variable called `weather_api_key` & set it equal to your weather api key in a string. Then go to https://www.bigdatacloud.com/geocoding-apis & sign up there and get an api key from the free plan & copy it. Then go back to your `config.py` file & create a variable called `geolocation_api_key` & set it equal to your api key in a string. Now just run `python main.py` & visit `http://127.0.0.1:5000/` which is where the website will be!

Docker Support Coming Soon!
