import flask
from flask import Flask, request
import google.oauth2.credentials
import google_auth_oauthlib.flow
import redis
from datetime import time, datetime, timedelta
import googleapiclient.discovery
import os



client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']
# This variable specifies the name of a file that contains the OAuth 2.0
# information for this application, including its client_id and client_secret.
config = {
  "web": {
    "client_id": client_id,
    "client_secret": client_secret,
    "redirect_uris": ["https://localhost:3000/oauth2callback"],
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://accounts.google.com/o/oauth2/token"
  }
}


# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
API_SERVICE_NAME = 'drive'
API_VERSION = 'v2'



app = flask.Flask(__name__)
app.secret_key = "ears"
redis_inst = redis.from_url(os.environ.get("REDIS_URL"))
redis_inst.set('led_colour', 'red')

def store_next_event(event_date):
    '''
    Get event date as a string and store it in the redis databse
    '''
    redis_inst.set('next_event', event_date)

def change_led_colour():
    '''
    Returns an LED colour depending on the amount of time left till the next meeting
    '''
    next_event_date_string = str(redis_inst.get('next_event')).strip('b\'')

    event_date = datetime.strptime(next_event_date_string, '%Y:%M:%d')
    time_30_mins = timedelta(seconds=30*60)
    time_now = datetime.now()

    if event_date - time_30_mins > time_now:
        redis_inst.set('led_colour', 'red')
    else:
        redis_inst.set('led_colour', 'green')

@app.route('/colour')
def get_led_colour():
    return redis_inst.get('led_colour')


@app.route('/test')
def test_api_request():
  if 'credentials' not in flask.session:
    return flask.redirect('authorize')

  # Load credentials from the session.
  credentials = google.oauth2.credentials.Credentials(
      **flask.session['credentials'])

  drive = googleapiclient.discovery.build(
      API_SERVICE_NAME, API_VERSION, credentials=credentials)

  files = drive.files().list().execute()

  # Save credentials back to session in case access token was refreshed.
  # ACTION ITEM: In a production app, you likely want to save these
  #              credentials in a persistent database instead.
  flask.session['credentials'] = credentials_to_dict(credentials)

  return flask.jsonify(**files)


@app.route('/authorize')
def authorize():
  # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
  flow = google_auth_oauthlib.flow.Flow.from_client_config(
      config, scopes=SCOPES)

  flow.redirect_uri = 'https://localhost:3000/oauth2callback'

  authorization_url, state = flow.authorization_url(
      # Enable offline access so that you can refresh an access token without
      # re-prompting the user for permission. Recommended for web server apps.
      access_type='offline',
      # Enable incremental authorization. Recommended as a best practice.
      include_granted_scopes='true')

  # Store the state so the callback can verify the auth server response.
  flask.session['state'] = state

  return flask.redirect(authorization_url)


@app.route('/oauth2callback', methods=['GET', 'POST'])
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
  flow.fetch_token(authorization_response=code)

  # Store credentials in the session.
  # ACTION ITEM: In a production app, you likely want to save these
  #              credentials in a persistent database instead.
  credentials = flow.credentials
  flask.session['credentials'] = credentials_to_dict(credentials)

  return "ok"


@app.route('/revoke')
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


@app.route('/clear')
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
  # When running locally, disable OAuthlib's HTTPs verification.
  # ACTION ITEM for developers:
  #     When running in production *do not* leave this option enabled.
  

  # Specify a hostname and port that are set as a valid redirect URI
  # for your API project in the Google API Console.
  app.run(port=3000, debug=True, ssl_context='adhoc')