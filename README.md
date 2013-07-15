**backup.py v0.9** - Generador de copias de seguridad incrementales.<br />
por Oliver Etchebarne - Paperclip X10<br />
http://drmad.org - http://x10.pe<br />

<p>
Copia el conteido de cada ruta especificada dentro de la carpeta destino,
comprimiendo los ficheros y preservando dueños y permisos.
</p>

<p>Este script no borra los ficheros si sus originales si lo han sido borrados.</p>

<p>backup.py [opciones] ruta [ruta..] destino</p>

Opciones:
<pre>
 -b         Comprime los ficheros con BZ2. Por defecto comprime con Gzip (más 
            rápido). 
 -n         No comprime los ficheros. 
 -f         Crea una copia completa, en vez de incremental. 
 -x pat     Excluye los ficheros que encajan con el patrón de shell "pat". Se 
            puede especificar varias veces. 
 -l fich    Graba los mensajes en el fichero "fich". Por defecto lo muestra por la 
            salida estándar. 
 -d         Detalla cada fichero que está siendo procesado. 
 -q         No muestra mensaje alguno. 
 -s         Crea un directorio por cada ruta especificada, en vez de recrear el 
            árbol completo en el directorio destino. 
 -g         Genera un fichero de configuración con las opciones especificadas 
            en la línea de comandos. 
 -c conf    Usa los parámetros almacenados en el fichero de configuración 
            "conf". Las opciones especificadas después de esta opción reemplazarán a 
            las guardadas en el fichero. 
 --help     Esta ayuda. 
 --version  Versión de éste script. 
</pre>
