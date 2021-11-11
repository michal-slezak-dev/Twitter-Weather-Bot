import tweepy
import requests
import json
from dotenv import load_dotenv
import os
from collections import defaultdict
import time

load_dotenv()  # take environment variables from .env.

# Get api keys for tweepy
CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")

# Get api keys for rapidapi
headers = {
    "x-rapidapi-host": os.getenv("X_RAPIDAPI_HOST"),
    "x-rapidapi-key": os.getenv("X_RAPIDAPI_KEY"),
}

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

api = tweepy.API(auth, wait_on_rate_limit=True)
FILE = "responded.txt"

# functions
def get_json_response_from_server(api_url, headers, params):
    response = requests.get(api_url, headers=headers, params=params)

    return response


def extract_json_data(response):
    try:
        content = response.json()
    except json.decoder.JSONDecodeError:
        print("Invalid format. . .")
    else:
        return content


def get_already_responded(file_name):
    with open(file_name, "r") as file:
        last_responded_id = file.read().strip()

    return last_responded_id


def add_already_responded(last_responded_id, file_name):
    with open(file_name, "w") as file:
        file.write(str(last_responded_id))


def reply_with_the_weather_forecast():
    # 0 degrees C = 273.15 K
    ZERO_DEGREES_CELSIUS = 273.15

    last_responded_id = get_already_responded(FILE)
    mentions = api.mentions_timeline(since_id=last_responded_id, tweet_mode="extended")

    # most recent mentions(reversed)
    for mention in reversed(mentions):
        userScreenName = mention.user.screen_name
        tweetId = mention.id
        cityAndCountry = "".join(mention.full_text.split()[1:3])
        language = mention.full_text.split()[3]

        params = {"q": cityAndCountry, "cnt": 1, "lang": language}

        # # get json response
        response = get_json_response_from_server("https://community-open-weather-map.p.rapidapi.com/forecast/daily", headers, params)

        # extract json data
        content = extract_json_data(response)

        # get the forecast
        day = content['list'][0]

        # get the feels_like temp
        feels_like = defaultdict(float)
        feels_like["day"] = round(day["feels_like"]["day"] - ZERO_DEGREES_CELSIUS, 1)
        feels_like["morning"] = round(day["feels_like"]["morn"] - ZERO_DEGREES_CELSIUS, 1)
        feels_like["evening"] = round(day["feels_like"]["eve"] - ZERO_DEGREES_CELSIUS, 1)
        feels_like["night"] = round(day["feels_like"]["night"] - ZERO_DEGREES_CELSIUS, 1)

        # get the temp
        temp = defaultdict(float)
        temp["day"] = round(day["temp"]["day"] - ZERO_DEGREES_CELSIUS, 1)
        temp["morning"] = round(day["temp"]["morn"] - ZERO_DEGREES_CELSIUS, 1)
        temp["evening"] = round(day["temp"]["eve"] - ZERO_DEGREES_CELSIUS, 1)
        temp["night"] = round(day["temp"]["night"] - ZERO_DEGREES_CELSIUS, 1)

        # get the min & max temp in the day
        max_temp = round(day["temp"]["max"] - ZERO_DEGREES_CELSIUS, 1)
        min_temp = round(day["temp"]["min"] - ZERO_DEGREES_CELSIUS, 1)

        # get the description
        description = day["weather"][0]["description"]

        # reply messages
        feels_like_msg = f"morning: {temp['morning']} °C\nevening: {temp['evening']} °C\nnight: {temp['night']} °C"
        reply_msg = f"Your forecast:\nBrief description: {description}\nAvg. temperature: {temp['day']} °C\nmorning: {temp['morning']} °C\nevening: {temp['evening']} °C\nnight: {temp['night']} °C\nmax_temp: {max_temp} °C\nmin_temp: {min_temp} °C\n\nAvg. perceived temp.: {feels_like['day']} °C\n{feels_like_msg}"

        # set last_responded_id to a new one
        last_responded_id = tweetId
        add_already_responded(last_responded_id, FILE)

        # testing, retweeting, liking and replying . . .
        print(f"Replying to: {tweetId} ---> {cityAndCountry} in: {language}")
        api.update_status(status=f"@{userScreenName} {reply_msg}", in_reply_to_status_id=tweetId, auto_populate_reply_metadata=True)
        api.retweet(tweetId)
        api.create_favorite(tweetId)

while True:
    reply_with_the_weather_forecast()
    time.sleep(2)