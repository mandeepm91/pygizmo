#A python wrapper for Survey Gizmo's API (v4)
### depends on requests and rauth (for oauth handling) or you can just use your api_key and token from gizmo's admin page. Optionally, you can integrate with slack and uncomment stuff for that, and there are obvious places where using a mysql database to handle fetched keys would help.

At a bare minimum, clone this and edit the ``gizmo_api.py`` get_auth() function to return your specific API_KEY and API_TOKEN. This gets added to all API calls.
