from collections import OrderedDict
import requests as r
import logging   
#GIZMO_LOG_FORMAT = '%(asctime)-15s %(user)-8s %(message)s' # removed %(clientip)s
#logging.basicConfig(filename='gizmo.log', level=logging.DEBUG, format=GIZMO_LOG_FORMAT)
logging.basicConfig(filename='error.log',level=logging.WARNING)
root = 'https://restapi.surveygizmo.com/v4/'
def get_auth():
    """ every call requires a token and secret, or if you are using oauth, you would implement that here instead.
    use the gizmo_auth.py file to fill in your oauth1 process, then dump to a database. your query might look like this:
    
    SELECT gizmo_access_token, gizmo_access_token_secret from api_user where uid = %s LIMIT 1;""",'ka', params=(uid,)
    
    for fetching tokens for a user.
    """
    return 'api_token=<your token goes here>&api_token_secret=<your secret>'
    
# ADDED Sep 2, 2015 -- API limits imposed on each operation (max 60 calls per minute, so wait remainder of second after call is done)
# ADDED Dec 7, 2015 -- allow a cherrypy.request specific auth to override this global auth.
# ADDED June 2016 -- oauth1 supported

# --------------------------- debugging functions --------------------
def show(result, indent=''):
    # pretty print results of an API call, for debugging
    import json
    try:
        print json.dumps(result.json(), sort_keys=True, indent=4, separators=(',', ': '))
    except:
        # already in json format?
        print json.dumps(result, sort_keys=True, indent=4, separators=(',', ': '))


def catch(response,msg=None):
    """
.. note ::
  When invoked catch reads the gizmo_api response and copies any errors to slack. 
  msg=''.... optional parameter to pass to slack, such as name of function that failed
  reports to slack, or logging.
    """
    #from slack_bot import incoming_hook
    #import logging
    try:
        if response.json().get('result_ok') in (1,True,'1','True'): #True is the right answer
            return response
        else:
            #MSG = incoming_hook({"icon_emoji":":ant:", "channel":"#fc_gizmo_errors", "text":"{0} \n {1}".format(msg or "Gizmo error",str(response.json()))})
            # insert your logging function here
            return response
    except:
        import traceback
        #MSG = incoming_hook({"icon_emoji":":ant:", "channel":"#fc_gizmo_errors", "text":"Error: {0} msg: {1} {2}".format(traceback.format_exc(),str(response), msg or "Gizmo error")})
        # insert your logging function here
        return response


def utf8_urlencode(params):
    # problem: urllib.urlencode(params) is not unicode-safe. Must encode all params strings as utf8 first.
    # UTF-8 encodes all the keys and values in params dictionary
    for k,v in params.items():
        # from http://stackoverflow.com/questions/22472015/unicode-url-encode-decode-with-python
        # TRY urllib.unquote_plus(artist.encode('utf-8')).decode('utf-8')
        if type(v) in (int, long, float):
            params[k] = v
        else:
            try:
                params[k.encode('utf-8')] = v.encode('utf-8')
            except Exception as e:
                logging.warning( '**ERROR utf8_urlencode ERROR** %s' % e )
    import urllib
    # urllib.urlencode(params.items()).decode('utf-8') #converts utf-8 to unicode, but URLs can only by UTF8, so OMIT.
    return urllib.urlencode(params.items())

#------------------- account functions ------------------------------------
def account():
    """ returns account data """
    hidden = """ # returns account data
    in "data":
        "contact_phone": "+44 20 7316 1844",
        "datecreated": "2014-06-04T07:45:32-04:00",
        "id": 00000,
        "login_link": "https://app.surveygizmo.com/login/v1?authenticate=...",
        "organization": "",
        "reseller": false,
        "reseller_uuid": null,
        "resellers_customer_id": null
    """
    auth = get_auth()
    return root + 'account/?' + auth

def account_teams(_id = None):
    # if _id is None, returns a LIST of all teams. Otherwise, details on specific team
    auth = get_auth()
    if _id is None:
        return root + 'accountteams/?' + auth
    else:        
        return root + 'accountteams/' +str(_id) + '?' + auth

def account_user(_id = None):
    # if _id is None, returns a LIST of all users. Otherwise, details on specific user
    auth = get_auth()
    if _id is None:
        return root + 'accountuser/?' + auth
    else:
        #e.g. x = r.get(account_user(402285))        
        return root + 'accountuser/' + str(_id) + '?' + auth


# ------------------------ survey functions --------------------------------
def get_survey(_id = None, kw={}):
    """
    # if _id is None, returns a LIST of all surveys. Otherwise, details on specific survey
    # note: varnames are at x.json()['data']['pages'][XX]['questions'][YY]['varname'] where XX and YY are the matching Nth page and Nth question
    # if {'page':2} in kw, then returns second page of results (51-100)
    """
    auth = get_auth()
    if kw != {}:
        kw = utf8_urlencode(kw) + '&'
    else:
        kw = ''
    if _id is None:
        return root + 'survey/?' + kw + auth
    else:
        return root + 'survey/' + str(_id) + '?'+ kw + auth

def create_survey(title=None,kw={}):
    """
    # KEYS: title, type, status, theme, team, options[internal_title], blockby,
    # method=PUT to create, POST to update, and DELETE to delete.
    # NOTE: created surveys have 2 pages. 
    # convention is to put either {{fcids}} or {{kaids}} into internal title to specify which ref id set was used.
    """
    auth = get_auth()
    params = OrderedDict(( ('_method','PUT'),
    ('title', title or 'Survey'),
    ('type', kw.get('type') or 'survey'),
    ('subtype', kw.get('subtype') or 'Standard Survey'),
    ('theme', kw.get('theme') or 83194) ))
    if 'options[internal_title]' in kw:
        params['options[internal_title]'] = kw['options[internal_title]']
    return root + 'survey/?' + utf8_urlencode(params) +'&'+ auth
    
def update_survey(_id, kw):
    #NOTE: title is required for copying a survey this way
    auth = get_auth()
    return root + 'survey/' + str(_id) +'/?_method=POST&'+ utf8_urlencode(kw) +'&'+ auth

def add_page(_id = None, title = None, description = None):
    auth = get_auth()
    if _id is None: #no survey_id
        return
    x = catch(r.get(get_survey(_id)),'add_page')
    import time
    time.sleep(0.99)
    prev_survey_page = last_page(x) #after last non-submit page
    after = '&after='+str(prev_survey_page)
    title = '&title='+str(title) if title is not None else ''
    descr = '&description'+str(description) if description is not None else ''
    return root + 'survey/' + str(_id) + '/surveypage?_method=PUT' + title + after + descr + '&' + auth

def update_survey_page(_id=None, survey_page=None, kw={}):
    auth = get_auth()
    if _id is None or survey_page is None or kw is {}:
        return
    params = {k:v for k,v in kw.items() if k in ['title', 'description', 'properties[hidden]', 'properties[piped_from]']}
    return root + 'survey/' + str(_id) + '/surveypage/' + str(survey_page) + '?_method=POST&' + utf8_urlencode(params) + '&' + auth


# ------------------- question functions ----------------------------------------- #
def questions(survey_id):
    auth = get_auth()
    return root + 'survey/' + str(survey_id) + '/surveyquestion?' + auth
    
def get_question(survey_id, question_id):
    auth = get_auth()
    return root + 'survey/' + str(survey_id) + '/surveyquestion/' + str(question_id) +'?'+ auth
    
def add_question(kw):
    """ INPUT kw is a dictionary of keyed data, either from question database or user form input
    #https://restapi.surveygizmo.com/v4/survey/123456/surveypage/1/surveyquestion?_method=PUT
    INSIDE kw:
        survey_id REQUIRED
        surveypage (if None, add to last page)
        type (radio, checkbox, menu, text, essay, email, multitext, single-image,
                multi-image, contsum, rank-dragdrop, table-radio, table-checkbox, table-textbox,
                table-menu-matrix, table-stars, file, instructions, media, hidden, urlredirect)
        title ---- QUESTION TEXT
        description
        after (question_id to follow this question)
        varname = 'q3'(SPSS variable name)
        varname[3]='q3', varname[4]='q4' -- assigns varname to a complex form table-radio question.
        shortname (alias)
    ----Look & Feel Properties  Example Required
        properties[disabled]    true    False
        properties[exclude_number]  true    False
        properties[hide_after_response] true    False
        properties[option_sort] true    False
        properties[orientation] HORZ,VERT   False
        properties[labels_right]    true    False
        properties[question_description_above]  true    False
        properties[custom_css]  CSS template hook   False
    ----Validation Properties   
        properties[required]    true    False
        properties[soft-required]   true    False
        properties[force_numeric]   true    False
        properties[force_percent]   true    False
        properties[force_currency]  true    False
        properties[subtype] email, date False
        properties[min_number]  value   False
        properties[max_number]  value   False
        properties[min_answers_per_row] value   False
        properties[minimum_response]    value   False
        properties[inputmask][mask] RegEx Pattern   False
        properties[inputmask][message]  RegEx Pattern   False
        properties[defaulttext] Default text or reporting value False
    ----Logic Properties    
        properties[hidden]  true    False
        properties[piped_from]  Question ID to pipe from    False
    ----Continuous Sum Properties
        properties[max_total]   value   False
        properties[max_total_noshow]    true    False
        properties[must_be_max] true    False
    ----File Upload Properties  
        properties[maxfiles]    1-10    False
        properties[extentions]  png,gif,jpg,doc,xls,docx,xlsx,pdf,txt   False
    ----URL Redirect Properties
        properties[url] Redirect URL    False
        properties[outbound][n][fieldname]  Variable Name   False
        properties[outbound][n][mapping]    Question ID for variable you wish to map    False
        properties[outbound][n][default]    Default Value to be passed when blank   False
    EXAMPLES

    kw = {'description': 'extended description', 'survey_id': 1996038, 'type': 'instructions', 'surveypage': 1, 'title': 'these instructions have a <a href="http://google.com"> link</a>'}
    the extended description is hidden from user.
    
    """
    auth = get_auth()
    if not (kw.get('survey_id') and kw.get('surveypage') and kw.get('type') and kw.get('title')):
        #json.dumps('result_ok':False,'note':"ERROR - missing data: %s, %s, %s, %s" % (kw.get('survey_id'), kw.get('surveypage'), kw.get('type'), kw.get('title')))
        return "ERROR - add_question missing data: %s, %s, %s, %s" % (kw.get('survey_id'), kw.get('surveypage'), kw.get('type'), kw.get('title'))
    if 'surveyquestion' in kw:
        # building a compound question by adding ROW
        # https://restapi.surveygizmo.com/v4/survey/123456/surveypage/1/surveyquestion/2?_method=PUT&type=radio&title=Twitter
        params = {k:v for k,v in kw.items() if k not in ('survey_id','surveypage','surveyquestion')}
        return root + 'survey/' + str(kw['survey_id']) + '/surveypage/' + str(kw['surveypage']) + \
            '/surveyquestion/'+str(kw['surveyquestion'])+'?_method=PUT&' + utf8_urlencode(params) +'&'+ auth
    else:
        params = {k:v for k,v in kw.items() if k not in ('survey_id','surveypage')}    
        return root + 'survey/' + str(kw['survey_id']) + '/surveypage/' + str(kw['surveypage']) + \
            u'/surveyquestion?_method=PUT&' + utf8_urlencode(params) +'&'+ auth

def update_question(kw):
    # https://restapi.surveygizmo.com/v4/survey/123456/surveyquestion/1?_method=POST
    # use for 'shortname', 'varname', 'title', 'properties[XXX]'
    auth = get_auth()
    if not (kw.get('survey_id') and kw.get('surveyquestion')):
        return "ERROR - update_question missing data: %s %s " % str(kw.get('survey_id')), str(kw.get('surveyquestion'))
    params = {k:v for k,v in kw.items() if k not in ('survey_id','surveyquestion')}
    return root + 'survey/' + str(kw['survey_id']) + '/surveyquestion/' + str(kw['surveyquestion']) + \
           '?_method=POST&' + utf8_urlencode(params) +'&' + auth

# ----------------------- survey options / answers ----------------------------------#
def add_option(kw):
    # x = r.get('https://restapi.surveygizmo.com/v4/survey/1996038/surveypage/1/surveyquestion/2/surveyoption?_method=PUT&title=option3&value=Reporting Value 3&' + auth)
    # requires survey_id, surveypage, surveyquestion, title, value
    auth = get_auth()
    if not (kw.get('survey_id') and kw.get('surveypage') and kw.get('surveyquestion') and kw.get('value') and kw.get('title')):
        return "ERROR - missing data: sid, page, qid, value, title - " + str((kw.get('survey_id'), kw.get('surveypage'),kw.get('surveyquestion'), kw.get('value'), kw.get('title')))
    #title=' + kw['title'] + '&value=' +
    params = {k:v for k,v in kw.items() if k not in ('survey_id','surveypage','surveyquestion')}
    return root + 'survey/' + str(kw['survey_id']) + '/surveypage/' + str(kw['surveypage']) + '/surveyquestion/' + str(kw['surveyquestion']) + \
           '/surveyoption?_method=PUT&' + utf8_urlencode(params) +'&'+ auth 

def update_option(kw):
    # https://restapi.surveygizmo.com/v4/survey/123456/surveyquestion/1/surveyoption/10001?_method=POST
    # to assign a varname, use kw['varname'] = 'q123'
    auth = get_auth()
    if not (kw.get('survey_id') and kw.get('surveyquestion') and kw.get('option_sku')):
        return "missing parameters. Requires 'survey_id', 'surveyquestion', 'option_sku'"
    params = {k:v for k,v in kw.items() if k not in ('survey_id','surveypage','surveyquestion','option_sku')}
    return root + 'survey/' + str(kw['survey_id']) + '/surveypage/' + str(kw['surveypage']) + \
           '/surveyquestion/' + str(kw['surveyquestion']) + '/surveyoption/' + str(kw['option_sku']) + \
           '?_method=POST&' + utf8_urlencode(params) +'&'+ auth 
   
    
# ------------------------- parsing results ---------------------------------- #
def last_question_id(survey_result):
    # input: API result from a create_survey or get_survey(_id) function.
    # parses a survey_result from API to find the ID of the last question, for 'after=XX' value
    question_ids = []
    for i in survey_result.json()['data']['pages']:#a list       
        question_ids.extend([j['id'] for j in i['questions']])
    return sorted(question_ids)[-1]

def survey_id(survey_result):
    # input: API result from a create_survey or get_survey(_id) function.
    return survey_result.json()['data']['id'] #only ONE ID per survey always

def last_page(survey_result):
    # input: API result from a create_survey or get_survey(_id) function.
    # returns the SECOND TO LAST PAGE, because LAST PAGE is the submitted, thankyou! page.
    return [i['id'] for i in survey_result.json()['data']['pages']][-2] #2nd-to-last



###################################################################################################
# ------------------------- build whole questions: API CALL LIMITS APPLY -------------------------#
# ------------------------- also doesn't require auth here, because low-level functions are above #

def build_text_question(survey_id=None, question_text=None, surveypage=None, kw={}):
    """
    REQUIRED
        survey_id
        question_text
    ALLOWED TYPES
        'text', 'essay', 'email', 'instructions'
    OPTIONAL PARAMETERS
        surveypage,
        'after'
            -- question_id in survey to follow
        'type'
            -- default is 'text' but can override with 'essay'
        'properties[question_description_above]'
            -- display the 'description' field

        'surveyquestion' -- if this is adding to an existing question
    USAGE
        build_text_question(1996038,"this an essay box:",{'type':'essay'})
    """
    import time
    if survey_id is None or question_text is None:
        return 'ERROR -- missing data'
    if surveypage is None:
        # fetch last page number from survey
        this_survey = catch(r.get(get_survey(survey_id)),'build_text_question.get_survey')
        time.sleep(0.99)
        surveypage = last_page(this_survey)
        logging.debug( 'using page '+str(surveypage) )
    if '{{org}}' in question_text and 'org' in kw:
        question_text = question_text.replace('{{org}}',kw['org'])
    kw.update({'survey_id':survey_id,
               'title':question_text,
               'surveypage':surveypage})
    if 'type' not in kw:
        kw['type'] = 'text'
    if 'after' not in kw: #forces question to be at end of survey, unless specified
        try:
            kw['after'] = last_question_id(this_survey)
        except:
            kw['after'] = last_question_id(catch(r.get(get_survey(survey_id)),'build_text_question.get_survey[exception finding last quetsion id]')) #slower, but fallback works
            time.sleep(0.99)
    #---------------------------------------------------------------------------
    if add_question(kw)[:5] != 'ERROR':
        x = catch(r.get(add_question(kw)),'build_text_question.add_question[error]')
        time.sleep(0.99)
        logging.debug(add_question(kw))
        try:
            question_id = x.json()['data']['id']
            logging.debug( 'text %s --> (%s) %s' % (kw.get('varname'), question_id, question_text) )
        except:        
            show(x)
            logging.warning( 'Gizmo add text question ERROR: %s' % (x,) )
            return x
        return question_id
    else:
        return add_question(kw) #ERROR
        
    
def build_mcq(survey_id=None, question_text=None, surveypage=None, ans_val={}, kw={}):
    """ e.g. a 'radio' type question or a table-radio multi-part question
    REQUIRED
        survey_id,
        question_text ('title')
        ans_val ('title':'value' Ordered dictionary for each answer option)
    TYPES
        'radio','checkbox'
    OPTIONAL
        surveypage,
        'after' -- question_id in survey to follow
        'type' -- default is 'radio' but can override with 'checkbox'
        'properties[question_description_above]' -- display the 'description' field
        'properties[orientation]' -- HORZ,VERT -- how radio answers displayed
        'properties[required]' -- true/false
        'properties[url]' -- Redirect URL
        'properties[outbound][n][default]' -- Default Value to be passed when blank
        kw['varname'] -- question ref_id (feed qid from table)
    """
    import time
    if survey_id is None or question_text is None or ans_val == {}:
        return 'ERROR -- missing data'
    if surveypage is None:
        # fetch last page number from survey
        this_survey = catch(r.get(get_survey(survey_id)),'build_mcq')
        time.sleep(0.99)
        surveypage = last_page(this_survey)
        logging.debug( 'using page '+str(surveypage) )
    if '{{org}}' in question_text and 'org' in kw:
        question_text = question_text.replace('{{org}}',kw['org'])
    kw.update({'survey_id':survey_id,
               'title':question_text,
               'surveypage':surveypage})
    if 'type' not in kw:
        kw['type'] = 'radio'
    if 'after' not in kw: #forces question to be at end of survey, unless specified
        try:
            kw['after'] = last_question_id(this_survey)
        except:
            kw['after'] = last_question_id(catch(r.get(get_survey(survey_id)),'build_mcq[error finding last question_id]')) #slower, but fallback works
            time.sleep(0.99)
    #---------------------------------------------------------------------------
    # create_question
    if add_question(kw)[:5] == 'ERROR':
        logging.debug( 'gizmo_api.ERROR: '+str(add_question(kw)) )
        return add_question(kw)
    x = catch(r.get(add_question(kw)),'build_mcq.add_question') #survey_id, surveypage, type, title
    time.sleep(0.99)
    logging.debug(add_question(kw))
    question_id = x.json()['data']['id']
    logging.debug( 'mcq %s --> (%s) %s' % (kw.get('varname'), question_id, question_text) )
    # create_options
    for ans,val in ans_val.items():
        if '{{org}}' in ans and 'org' in kw:
            ans = ans.replace('{{org}}',kw['org'])        
        opts = {'survey_id':survey_id,
                'surveypage':surveypage,
                'surveyquestion':question_id,
                'title':ans,
                'value':val}
        x = catch(r.get(add_option(opts)),'build_mcq.add_option[answers]') #id, page, question, type, title, value
        time.sleep(0.99)
        logging.debug(add_option(opts))
        if x.json()['result_ok'] == 0:
            logging.debug( "ERROR adding option %s for question %s" % (ans, str(question_id)) )
    return question_id


def fetch_survey_varnames(response_object):
    """
    # takes other the response or its json() part
    # varnames in x.json()['data']['pages'][0]['questions'][0]['varname'] for table-radio questions
    fetch "sub_question_skus": [3,4,5] ---> 'varname'
    use sub_skus to match varname: "varname": {"3": "q313", "4": "q441", "5": "q505"}
    then connect complex key (question_id, sub_question_sku) to varname in lookup.
    simple questions have key:value like (question_id : varname_id)
    """ 
    try:
        if 'json' in dir(response_object):
            data = response_object.json()['data']
        else:
            data = response_object['data']
    except:
        return {'ERROR':'could not understand the input object. Must be a requests response_object or a json'}
    # iterate through and find all the gizmo internal question IDs and external varnames; create lookup dict.
    from collections import OrderedDict
    lookup = OrderedDict() #internal_id : external_id
    for page in data['pages']:
        for question in page['questions']:
            if question.get('varname') in (None,[]):
                lookup[(question['id'],0)] = None
            elif type(question['varname']) is dict: #this dictionary has arbitrary order in response_object. So lookup not order-able.
                if len(question['varname']) > 1:
                    skus = question['sub_question_skus'] #these keys are ints, but varname's keys are strings.
                    varnames = question['varname'] #string sku keys : string varnames
                    for sku,var in varnames.items():
                        lookup[(question['id'],int(sku))] = var
                elif len(question['varname']) == 1: # this shouldn't happen ever.
                    lookup[(question['id'],0)] = question['varname'][0]
            elif type(question['varname']) is list and len(question['varname']) == 1:
                lookup[(question['id'],0)] = question['varname'][0]
            else:
                raise ValueError
    return lookup

# ############################################################################################################################
# ------------------------------------- gizmo campaigns ---------------------------------------------------------------------#
# ADDED SEP 23 2015

def create_campaign(survey_id, params={}):
    #https://restapi.surveygizmo.com/v4/survey/123456/surveycampaign?_method=PUT&type=link&name=New Link Name
    """
    Parameters	Example	Required
    Authentication Credentials	user:pass=john@doe.com:1234	True
    type	link, email, html, js, blog, iframe, popup	True
    name	New Link Name	True
    language	auto, english, etc.	False
    status	active, closed, deleted	False
    slug (link only)	newlinkslug	False
    subtype (link only)	standard, private, shortlink	False
    tokenvariables	var%3Dvalue%26var2%3d=value	False"""
    auth = get_auth()
    if 'type' not in params:
        params['type'] = 'email'
    if 'name' not in params:
        import datetime
        params['name'] = 'email campaign %s' % str(datetime.date.today())
    if 'language' not in params:
        params['language'] = 'auto'
    return root + 'survey/' + str(survey_id) + '/surveycampaign?_method=PUT&' + utf8_urlencode(params) +'&'+ auth

def get_campaign(survey_id, cid = None):
    # https://restapi.surveygizmo.com/v4/survey/123456/surveycampaign/100000
    auth = get_auth()
    cid = '?' if cid == None else '?'+str(cid)+'&'
    return root + 'survey/' + str(survey_id) + '/surveycampaign/' + cid + auth

def update_campaign(survey_id, cid, params={}):
    # https://restapi.surveygizmo.com/v4/survey/123456/surveycampaign/100000?_method=POST
    auth = get_auth()
    assert len(params) > 0, "nothing changed. try {'copy' = 'true'} to copy a campaign"
    return root + 'survey/' + str(survey_id) + '/surveycampaign/' + str(cid) +'?_method=POST&' + utf8_urlencode(params) +'&' + auth
    
def delete_campaign(survey_id, cid):
    # https://restapi.surveygizmo.com/v4/survey/123456/surveycampaign/100000?_method=DELETE
    auth = get_auth()
    return root + 'survey/' + str(survey_id) + '/surveycampaign/' + str(cid) + '?_method=DELETE&' + auth


def list_contacts(survey_id, cid, kw={}):
    # https://restapi.surveygizmo.com/v4/survey/123456/surveycampaign/100000/contact
    """A single record per email address is stored per account. Email address and all standard contact fields are
    are stored at the account level. This means that changes to the standard contact fields of an existing contact 
    will be made globally wherever the contact is present"""
    # params: page, resultsperpage=100
    auth = get_auth()
    params = '?'+utf8_urlencode(kw)+'&' if len(kw) > 0 else '?'
    return root + 'survey/' + str(survey_id) + '/surveycampaign/' +str(cid)+ '/contact' + params + auth

def get_contact(survey_id, cid, contact_id):
    # https://restapi.surveygizmo.com/v4/survey/123456/surveycampaign/100000/contact/100030864
    # returns (mainly) ['semailaddress']
    # data['esubscriberstatus'] is a combination of status log response status and send status. It returns 1 of 5 values:
    # Unsent Sent Bounced 
    # Partial - Link clicked and at least one page submitted
    # Complete - Link clicked and response completed
    auth = get_auth()
    return root + 'survey/' + str(survey_id) + '/surveycampaign/' +str(cid)+ '/contact/' + str(contact_id) +'?'+ auth

def create_contact(survey_id, cid, params={}):
    # https://restapi.surveygizmo.com/v4/survey/123456/surveycampaign/100000/contact/?_method=PUT&semailaddress=newexample@email.com
    """Authentication Credentials	user:pass=john@doe.com:1234	True
    semailaddress	example@email.com	True
    sfirstname	Firstname	False
    slastname	Lastname	False
    sorganization	Organization	False
    sdepartment	Department	False
    shomephone	123-456-7890	False
    sfaxphone	123-456-7890	False
    sbusinessphone	123-456-7890	False
    smailingaddress	123 Main St	False
    smailingaddress2	Suite 100	False
    smailingaddresscity	Anycity	False
    smailingaddressstate	CO	False
    smailingaddresscountry	US	False
    smailingaddresspostal	12345	False
    stitle	Title	False
    surl	www.website.com	False
    scustomfield1-10*	custom field data 1-10	False
    custom[ID]**	custom[15]=value	False
    estatus	Active, Inactive	False
    allowdupe	true	False
    *These are the custom fields 1-10 that are available as part of the email campaign contact list.
    """
    auth = get_auth()
    assert 'semailaddress' in params, "must provide sender email"
    return root + 'survey/' + str(survey_id) + '/surveycampaign/' +str(cid)+ '/contact/?_method=PUT&' + utf8_urlencode(params) + '&'+ auth

def update_contact(survey_id, cid, contact_id, params):
    # https://restapi.surveygizmo.com/v4/survey/123456/surveycampaign/100000/contact/100030864?_method=POST
    auth = get_auth()
    assert len(params) > 0, "nothing changed"
    return root + 'survey/' + str(survey_id) + '/surveycampaign/' +str(cid)+ '/contact/' + str(contact_id) + '?_method=POST&' + utf8_urlencode(params) +'&'+ auth

def delete_contact(survey_id, cid, contact_id):
    # https://restapi.surveygizmo.com/v4/survey/123456/surveycampaign/100000/contact/100030864?_method=DELETE
    auth = get_auth()
    return root + 'survey/' + str(survey_id) + '/surveycampaign/' +str(cid)+ '/contact/' + str(contact_id) + '?_method=DELETE&' + auth


def list_emails(survey_id, cid):
    # specific to this survey and campaign ID
    # https://restapi.surveygizmo.com/v4/survey/123456/surveycampaign/100000/emailmessage
    auth = get_auth()
    return root + 'survey/' + str(survey_id) + '/surveycampaign/' +str(cid)+ '/emailmessage?' + auth

def create_email_message(survey_id, cid, params={}):
    # https://restapi.surveygizmo.com/v4/survey/123456/surveycampaign/100000/emailmessage?_method=PUT
    # no parameters are required, but I am enforcing subject and body[text] requirement here.
    # body[html] is optional, but useful
    # messagetype = plaintext or html
    # from[email] ... use from[email] = "marc@gmail.com"
    # from[name] ... use from[name = "marc maxson"
    # send = true will IMMEDIATELY send it out. (default is false)
    # NOTE: Pending is defined as a contact that this specific email message hasn't been sent to
    # and, if the message is a reminder, the contact has already been sent the initial email and any previous reminders.
    auth = get_auth()
    if 'subject' not in params or 'body[text]' not in params:
        return "ERROR: email requires subject and body[text]"
    if 'send' not in params:
        params['send'] = True
    return root + 'survey/' + str(survey_id) + '/surveycampaign/' +str(cid)+ '/emailmessage?_method=PUT&' + utf8_urlencode(params) + '&' + auth

def get_email_message(survey_id, cid, email_message_id):
    #https://restapi.surveygizmo.com/v4/survey/123456/surveycampaign/100000/emailmessage/100000
    auth = get_auth()
    return root + 'survey/' + str(survey_id) + '/surveycampaign/' +str(cid)+ '/emailmessage/' + str(email_message_id) + '?' + auth
    
def update_email_message(survey_id, cid, email_message_id, params={}):
    """# https://restapi.surveygizmo.com/v4/survey/123456/surveycampaign/100000/emailmessage/100000?_method=POST
    include params = {'send':True} to send it out immediately. Must have created contacts already for this campaign.
    *The send parameter will send the message when the call is made only if set to true. This parameter does not need to be set to false to prevent the message from sending.
    send will not work if email message is a reminder and an earlier message of type="email" has not gone out yet.
    If I send an email, then add contacts to the campaign, then try to send that same email out again, it won't re-send. Create a NEW message as type "reminder" for this.
    """
    auth = get_auth()
    assert len(params) > 0, "nothing changed"
    return root + 'survey/' + str(survey_id) + '/surveycampaign/' +str(cid)+ '/emailmessage/' + str(email_message_id) + '?_method=POST&' + utf8_urlencode(params) + '&' + auth
    
def delete_email_message(survey_id, cid, email_message_id):
    # https://restapi.surveygizmo.com/v4/survey/123456/surveycampaign/100000/emailmessage/100000?_method=DELETE
    auth = get_auth()
    return root + 'survey/' + str(survey_id) + '/surveycampaign/' +str(cid)+ '/emailmessage/' + str(email_message_id) + '?_method=DELETE&' + auth
