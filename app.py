from importlib.util import spec_from_loader
from venv import create
from flask import Flask, request, url_for, session, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import os 

app = Flask(__name__)

app.secret_key = os.urandom(16) #generates a random string for the flask secret key
app.config['SESSION_COOKIE_NAME'] = 'yummy cookie'
TOKEN_INFO = 'token_info'

# print(os.environ.get('SP_BESTIE_SECRET'))
# print(os.environ.get('SP_BESTIE_CLIENTID'))

# ----------------------------------------------------------------
#                              endpoints!!
# ----------------------------------------------------------------

# login base endpoint when flask first loads
@app.route('/')
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

# redirect protocol after logging in
@app.route('/redirect')
def redirectPage():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('getTracks', _external=True))

# get all the tracks from the user
@app.route('/getTracks')
def getTracks():
    try:
        token_info = get_token()
    except:
        print('user not logged in!!!')
        return redirect(url_for('login', _external=False))

    # get all the saved tracks in form "name - artist"
    sp = spotipy.Spotify(auth=token_info['access_token'])
    results = []
    iter = 0
    while True:
        offset = iter * 50
        iter += 1
        curGroup = sp.current_user_saved_tracks(limit=50, offset=offset)['items']
        for i, item in enumerate(curGroup):
            track = item['track']
            val = track['name'] + " - " + track['artists'][0]['name']
            results += [val]
        if (len(curGroup) < 50): # reached the end of liked songs!!
            break

    return results

# redirect to login page if token expires or doesn't exist
def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info: # if there is no current token info
        raise 'exception'

    # if token expires in 60 seconds, get a new token
    now = int(time.time())
    expired = token_info['expires_at'] - now < 60
    if expired:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])

    return token_info

# creates spotify oauth to successfully connect code to spotify db
def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=os.environ.get('SP_BESTIE_CLIENTID'), 
        client_secret=os.environ.get('SP_BESTIE_SECRET'),
        redirect_uri=url_for('redirectPage', _external=True),
        scope='user-library-read'
    )
