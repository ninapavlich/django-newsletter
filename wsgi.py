"""
# WSGI Application
"""
import os
import sys

# -- Hot Link Libs
ROOT_APP            = os.path.dirname( __file__ )
ROOT                = u'/'.join( ROOT_APP.split('/')[0:-1] )

sys.path.append( os.path.join( ROOT, "libs" ) )

# -- Import Settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")

# -- Import and Run Server
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()