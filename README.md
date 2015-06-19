backup.py
=========

Generador de copias de seguridad incrementales.<br />
por Oliver Etchebarne - Paperclip X10<br />
http://drmad.org - http://x10.pe<br />

<p>Genera copias de seguridad incrementales de cada ruta especificada, dentro de la carpeta destino. Comprime los ficheros y preservan dueños y permisos.</p>

<p>Debería de trabaja en cualquier distro de Linux con Python > 3.2</p>

<pre>backup.py [opciones] ruta [ruta...] destino</pre>

Opciones:
<pre>
 -b         Comprime los ficheros con BZ2. Por defecto comprime con Gzip (más 
            rápido). 
 -n         No comprime los ficheros. 
 -f         Crea una copia completa, en vez de incremental. 
 -x pat     Excluye los ficheros que encajan con el patrón de shell "pat". Se 
            puede especificar varias veces. 
 -l fich    Graba el registro de actividad completo en el fichero "fich". 
 -d         Muestra mayor información en la salida estándar. 
 -q         Suprime la salida de información en la salida estándar. 
 -o         Crea un directorio por cada ruta especificada, en vez de recrear el 
            árbol completo en el directorio destino. 
 -F         Fuerza a "find" a seguir enlaces simbólicos 
 -g         Genera un fichero de configuración con las opciones especificadas 
            en la línea de comandos. 
 -c conf    Usa los parámetros almacenados en el fichero de configuración 
            "conf". Las opciones especificadas después de esta opción reemplazarán a 
            las guardadas en el fichero. 
 --help     Esta ayuda. 
 --version  Versión de éste script. 
</pre>
