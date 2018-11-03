import flask
from flask import Flask, request
import google.oauth2.credentials
import google_auth_oauthlib.flow
import redis

app = Flask(__name__)
redis_inst = redis.StrictRedis(host='localhost', port=6379, db=0)
redis_inst.set('led_colour', 'red')

@app.route('/colour')
def get_led_colour():
    return redis_inst.get('led_colour')

@app.route('/authorisation')
def call_client_id():
	# Use the client_secret.json file to identify the application requesting
	# authorization. The client ID (from that file) and access scopes are required.
	flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
	    'client_secret.json',
	    scopes=['https://www.googleapis.com/auth/drive.metadata.readonly'])

	# Indicate where the API server will redirect the user after the user completes
	# the authorization flow. The redirect URI is required.
	flow.redirect_uri = 'http://localhost:3000/redirect'

	# Generate URL for request to Google's OAuth 2.0 server.
	# Use kwargs to set optional request parameters.
	authorization_url, state = flow.authorization_url(
	    # Enable offline access so that you can refresh an access token without
	    # re-prompting the user for permission. Recommended for web server apps.
	    access_type='offline',
	    # Enable incremental authorization. Recommended as a best practice.
	    include_granted_scopes='true')

	return flask.redirect(authorization_url)

@app.route('/redirect', methods=['GET', 'POST'])
def response():
	code = request.args.get('code')
	print(code)
	return "ok"


if __name__ == "__main__":
    app.run(port=3000, debug=True)


