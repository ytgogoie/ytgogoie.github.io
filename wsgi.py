
from app import app as application

# This file is used by WSGI servers like Apache with mod_wsgi
# or other shared hosting configurations

if __name__ == "__main__":
    application.run()
