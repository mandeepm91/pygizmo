#A python wrapper for Survey Gizmo's API (v4)
### depends on requests and rauth (for oauth handling) or you can just use your api_key and token from gizmo's admin page. Optionally, you can integrate with slack and uncomment stuff for that, and there are obvious places where using a mysql database to handle fetched keys would help.

At a bare minimum, clone this and edit the ``gizmo_api.py`` get_auth() function to return your specific API_KEY and API_TOKEN. This gets added to all API calls.

# note on using pygizmo with python's rauth module versus requests module:

    All CALLs using rauth.sessions that *modify data* must include a _method parameter, and separate parameters for everything
    after the '?' in the url / endpoint to work. These existing calls work with requests just fine, which can accept strings with
    parameters, but rauth cannot.
    
    These calls include:

* add_question()
* add_option()
* update_survey_page()
add_page()
update_survey()
create_survey()
delete_email_message()
update_email_message()
create_email_message()
delete_contact()
update_contact()
create_contact()
delete_campaign()
update_campaign()
create_campaign()
