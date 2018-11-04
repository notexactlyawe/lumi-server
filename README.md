# lumÏ

**lumÏ** is a smart lamp that unintrusively gives you information. Currently it integrates with Google Calendar, but can easily be extended to alert you to the weather, follow along with your music or simply provide mood lighting.

## Calendar integration

**lumÏ** lets you know when your next event is getting close by changing colour. When the light is green, it means you have no events in the next 30 minutes. If the light changes to blue, it means an event is coming up and red indicates that you are late. **lumÏ** also allows you to create reminders that will flash the LED when they happen. These notifications can be dismissed by swiping your hand over the top of the lamp.

## Install locally

### Pre-requisites

 - Redis
 - Python 3
 - pip

### Instructions

```
pip install -r requirements.txt
sudo apt install redis-server
```

You will also need to set the following environment variables:

```
CLIENT_ID       = {your Google OAuth client ID}
CLIENT_SECRET   = {your Google OAuth client secret}
REDIS_URL       = {the URL of your redis instance}
```

If running locally you will also probably need to set the following variables to allow you to use `http` with OAuth.

```
OAUTHLIB_INSECURE_TRANSPORT = 1
DEBUG                       = 1
```

## Running locally

The above may or may not start the redis-server running in the background. If it doesn't, you can run `redis-server`. To run the server, run the below command:

`python3 app.py`

## Deploy on Heroku

This repository is designed to be deployed on Heroku. The Procfile will start up a gunicorn server that will serve both the frontend and the endpoints for the LINKIT.

## Programming the LINKIT

The LINKIT One can be programmed using the Arduino IDE. All the code for the board is stored inside `LumiLED.ino`.
