# dependencies: rauth, requests
# added June 2016


def start_service():
    host = 'http://restapi.surveygizmo.com/head'
    key = "put your oauth service key here"
    secret = "your client secret"
    #//This is the URL that we use to request a new access token
    request_token_url = host + '/oauth/request_token'
    #//After getting an access token we'll want to have the user authenicate 
    authorize_url = host + '/oauth/authenticate'
    # //this final call fetches an access token.
    access_token_url = host + '/oauth/access_token'
    import requests
    from rauth import OAuth1Service # requires requests
    # 1. create a rauth service object.
    service = OAuth1Service(
        name='surveygizmo',
        consumer_key= key, 
        consumer_secret= secret, 
        request_token_url= request_token_url, 
        access_token_url= access_token_url, 
        authorize_url= authorize_url, 
        base_url= host
        )
    return service


def start_authentication(uid):
    # import database as db --- import your own mysql database wrapper here.
    # 1. create a rauth service object.
    service = start_service()
    # 2. get request tokens
    request_token, request_token_secret = service.get_request_token()
    authorize_url = service.get_authorize_url(
        request_token,
        oauth_callback='http://api.mysite.org/import-survey',
        custom_pluginname='Smart Bot'
        )
    # 3. find out if user has already got an api_user account. if not, add new one with basic 'org' level read access
    data,msg = db.mysql("""SELECT uid from api_user where uid = %s LIMIT 1;""",'ka',params=(uid,))
    if len(data) == 0:
        # create user; otherwise, do nothing
        import cherrypy
        msg = db.mysql("""INSERT INTO api_user (user, pass, call_count, uid, org_id, created, permissions) 
        VALUES (%s, %s, 0, %s, %s, now(), 'org');""",'ka',params=(cherrypy.request.username, cherrypy.request.api_password, uid, cherrypy.request.org_id))
        #import slack_bot
        #msg_ignore = slack_bot.incoming_hook({"text":u'''New api_user: {0} {1}'''.format(cherrypy.request.username, msg), "channel":"#fc_gizmo_errors", "icon_emoji":":level_slider:"})
    # 3. save stuff you can.
    msg = db.mysql("""UPDATE api_user SET request_token = %s, 
        request_token_secret = %s
        WHERE uid = %s;""",'ka', params=(request_token, request_token_secret, uid) )
    # 4. let user authorize access
    return authorize_url


def finish_authentication(uid, kw):
    """ oauth1
.. note::
   realize that (1) there's no path to refresh a revoked token, and no way to check for users with multiple oauth records in DB.
   so in that sense, the user's first oauth1 record in api_user is their only usable token. 
   ALSO depends on the database structure and wrapper you use.
"""
    import database as db
    data,msg = db.mysqldict("""SELECT request_token, request_token_secret from api_user WHERE uid = %s;""",'ka',params=(uid))
    service = start_service()
    oauth_token = kw.get('oauth_token')
    oauth_verifier = kw.get('oauth_verifier')
    TOKENS = service.get_access_token(data[0]['request_token'], data[0]['request_token_secret'])
    try:
        access_token = TOKENS[0]
        access_token_secret = TOKENS[1]
        msg = db.mysql("""UPDATE api_user 
        SET gizmo_access_token = %s,
        gizmo_access_token_secret = %s,
        oauth_token = %s, 
        oauth_verifier = %s
        WHERE uid = %s;""",'ka', params=(access_token, access_token_secret, oauth_token, oauth_verifier, uid))
        return True
    except:
        return False


def test_oauth(gizmo_access_token, gizmo_access_token_secret):
    # returns session object for a given user's token/secret
    # reloading the session with rauth
    from rauth import OAuth1Service
    import requests
    # supply consumer_key and consumer_secret
    service = OAuth1Service(consumer_key = 'my key', consumer_secret = 'my secret')
    # pass a (key,secret) tuple to get_session
    session = service.get_session((gizmo_access_token, gizmo_access_token_secret))
    return session
