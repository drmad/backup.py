# backup.py

Generador de copias de seguridad incrementales e históricas

Desarrollado por Oliver Etchebarne - https://drmad.org.

Este script genera copias de seguridad incrementales de cada ruta especificada, dentro de la carpeta destino. Comprime los ficheros preservando dueño, permiso, y _timestamp_.

Opcionalmente puede activarse el modo 'histórico', en el cual genera una carpeta por cada ejecución del script, conteniendo la copia de seguridad actual. Los ficheros no modificados son un _hard link_ la copia de seguridad anterior.

Debería de trabaja en cualquier distro de Linux con Python > 3.2

## Uso

    backup.py [opciones] ruta [ruta...] destino

Opciones:

```
-b         Comprime los ficheros con BZ2. Por defecto comprime con Gzip (más
           rápido).
-n         No comprime los ficheros.
-f         Crea una copia completa, en vez de incremental. No es compatible con -h
-h         Crea una copia histórica. No es compatible con -f.
-H nombre  Nombre del directorio para la copia histórica. De omitirse se usará
           la fecha y hora actual.
-x pat     Excluye los ficheros que encajan con el patrón de shell "pat". Se
           puede especificar varias veces.
-l fich    Graba el registro de actividad completo en el fichero "fich".
-d         Muestra mayor información en la salida estándar.
-q         Suprime la salida de información en la salida estándar.
-F         Fuerza a "find" a seguir enlaces simbólicos
-g         Genera un fichero de configuración con las opciones especificadas
           en la línea de comandos.
-c conf    Usa los parámetros almacenados en el fichero de configuración
           "conf". Las opciones especificadas después de esta opción reemplazarán a
           las guardadas en el fichero.
--help     Esta ayuda.
--version  Versión de éste script.

```

## Notas para el backup histórico

El backup histórico trabaja asumiendo que los parámetros no han variado desde la ejecución anterior, e.g. el compresor o la distribución de los directorios.
