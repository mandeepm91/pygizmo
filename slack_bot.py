# useful logging function if you use slack.

def incoming_hook(kw):
    """ kw contains...
    text -- message
    channel -- #general begin with hash
    username -- make something up (bot name)
    icon_emoji -- :squirrel:
    put links in <brackets> and use <link|label> for fancy links
    url -- webhook url = https://hooks.slack.com/services/othercode/usercode/<authcode>....
    SEE SLACK MARKUP for more -- https://api.slack.com/docs/formatting
    #  -- webhook url = https://hooks.slack.com/services/key1/key2/key3
    """
    
    if not kw.get('url'):
        kw['url'] = 'https://hooks.slack.com/services/key1/key2/key3' # REPLACE THIS KEY. That's your slack webhooks URL in admin section
    if not kw.get('channel'):
        kw['channel'] = '#general' # default channel
    if not kw.get('username'):
        kw['username'] = 'gizmo-bot'
    if not kw.get('icon_emoji'):
        kw['icon_emoji'] = ':squirrel:'
    import requests as r
    import json
    payload = {"text": kw['text'], "channel":kw['channel'], "username":kw['username'], "icon_emoji": kw['icon_emoji']}
    msg = r.post(kw['url'], data=json.dumps(payload))
    return msg
