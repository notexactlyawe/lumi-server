import flask
import json
from flask import Flask, request, render_template
import google.oauth2.credentials
import google_auth_oauthlib.flow
import redis
from datetime import time, datetime, timedelta
from googleapiclient.discovery import build
import os

client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']
# This variable specifies the name of a file that contains the OAuth 2.0
# information for this application, including its client_id and client_secret.
config = {
  "web": {
    "client_id": client_id,
    "client_secret": client_secret,
    "redirect_uris": ["https://lumi-htm-best.herokuapp.com/oauth2callback"],
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://accounts.google.com/o/oauth2/token"
  }
}


# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
API_SERVICE_NAME = 'drive'
API_VERSION = 'v2'

application = flask.Flask(__name__)
application.secret_key = "ears"
redis_inst = redis.from_url(os.environ.get("REDIS_URL"))
redis_inst.set('led_colour', 'g')

def get_event_date():
    raw_credentials = json.loads(redis_inst.get("credentials"))
    credentials = google.oauth2.credentials.Credentials(**raw_credentials)
    service = build('calendar', 'v3', credentials=credentials)

    now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the upcoming 1 events')
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')

    first_event_found = False
    first_reminder_found = False
    first_event = None
    first_notification = None

    min_plus_one_day = (datetime.min + timedelta(days=1)).isoformat() + 'Z'

    dismissed_notifications = redis_inst.lrange('dismissed_notifications', 0, -1)
    print("Dismissed_notifictaions list {}".format(dismissed_notifications))

    for event in events:
        print("Current event id:{}".format(event['id']))
        if event['id'] in dismissed_notifications:
            continue

        if not first_event_found:
            if not event['summary'].startswith('Reminder:'):
                first_event_found = True
                first_event = event

        if not first_reminder_found:
            if event['summary'].startswith('Reminder:'):
                first_reminder_found = True
                first_notification = event
                redis_inst.set('current_notification', event['id'])

    if first_event_found:
        event_date = first_event['start'].get('dateTime', first_event['start'].get('data'))
    else:
        event_date = min_plus_one_day

    if first_notification:
        notification_date = first_notification['start'].get('dateTime', first_notification['start'].get('data'))
    else:
        notification_date = min_plus_one_day

    return [event_date, notification_date]

def change_led_colour(event_date, notification_date):
    '''
    Returns an LED colour depending on the amount of time left till the next meeting
    '''
    time_30_mins = timedelta(seconds=30*60)
    time_1_minute = timedelta(seconds=60)
    time_now = datetime.now()

    if (notification_date - time_1_minute < time_now) and (notification_date + time_1_minute > time_now):
        if event_date < time_now:
            #red and flashing
            redis_inst.set('led_colour', 'a')
        elif event_date - time_30_mins < time_now:
            #blue and flashing
            redis_inst.set('led_colour', 'c')
        else:
            #green and flashing
            redis_inst.set('led_colour', 'd')
    else:
        if event_date < time_now:
            #red
            redis_inst.set('led_colour', 'r')
        elif event_date - time_30_mins < time_now:
            #blue
            redis_inst.set('led_colour', 'b')
        else:
            #green
            redis_inst.set('led_colour', 'g')

@application.route('/')
def render_login_page():
    return render_template('index.html')

@application.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@application.route('/colour')
def get_led_colour():
    [event_date, notification_date] = get_event_date()
    change_led_colour(datetime.strptime(event_date,"%Y-%m-%dT%H:%M:%SZ"), datetime.strptime(notification_date, "%Y-%m-%dT%H:%M:%SZ"))
    print("-------- {} of type {} --------".format(event_date, type(event_date)))
    return redis_inst.get('led_colour')

@application.route('/dismiss')
def dismiss():
    current_notification = redis_inst.get('current_notification')
    if current_notification is None:
        return get_led_colour()
    redis_inst.lpush('dismissed_notifications', current_notification)
    return get_led_colour()

@application.route('/authorize')
def authorize():
  # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
  flow = google_auth_oauthlib.flow.Flow.from_client_config(
      config, scopes=SCOPES)

  flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

  authorization_url, state = flow.authorization_url(
      # Enable offline access so that you can refresh an access token without
      # re-prompting the user for permission. Recommended for web server apps.
      access_type='offline')

  # Store the state so the callback can verify the auth server response.
  flask.session['state'] = state

  return flask.redirect(authorization_url)


@application.route('/oauth2callback', methods=['GET', 'POST'])
def oauth2callback():
  # Specify the state when creating the flow in the callback so that it can
  # verified in the authorization server response.
  state = flask.session['state']
  code = request.args.get('code')
  flow = google_auth_oauthlib.flow.Flow.from_client_config(
    config, scopes=SCOPES, state=state)
  flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

  # Use the authorization server's response to fetch the OAuth 2.0 tokens.
  authorization_response = flask.request.url
  flow.fetch_token(code=code)

  # Store credentials in the session.
  # ACTION ITEM: In a production app, you likely want to save these
  #              credentials in a persistent database instead.
  credentials = flow.credentials
  flask.session['credentials'] = credentials_to_dict(credentials)
  redis_inst.set("credentials", json.dumps(flask.session['credentials']))

  return flask.redirect(flask.url_for("dashboard"))


@application.route('/revoke')
def revoke():
  if 'credentials' not in flask.session:
    return ('You need to <a href="/authorize">authorize</a> before ' +
            'testing the code to revoke credentials.')

  credentials = google.oauth2.credentials.Credentials(
    **flask.session['credentials'])

  revoke = requests.post('https://accounts.google.com/o/oauth2/revoke',
      params={'token': credentials.token},
      headers = {'content-type': 'application/x-www-form-urlencoded'})

  status_code = getattr(revoke, 'status_code')
  if status_code == 200:
    return('Credentials successfully revoked.' + print_index_table())
  else:
    return('An error occurred.' + print_index_table())


@application.route('/clear')
def clear_credentials():
  if 'credentials' in flask.session:
    del flask.session['credentials']
  return ('Credentials have been cleared.<br><br>' +
          print_index_table())


def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}

if __name__ == '__main__':
  application.run(host='0.0.0.0', debug=True)
