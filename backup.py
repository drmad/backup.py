#!/usr/bin/env python3
'''
backup.py
=========

Generador de copias de respaldo incrementales e históricas.
por Oliver Etchebarne Bejarano
https://drmad.org

Genera copias de seguridad incrementales de cada ruta especificada, dentro de
la carpeta destino. Comprime los ficheros y preservan dueños y permisos.

Debería de trabaja en cualquier distro de Linux con Python > 3.2

https://github.com/drmad/backup.py
'''

import subprocess, sys, re, os
import gzip, bz2, shutil, stat
import time, activitylog, json

from datetime import datetime, timedelta

VERSION = 0.2
METADATA_FILENAME = ".backup.metadata"

# Parámetros por defecto, con su ayuda.
DEFAULT_PARAMETERS = dict(
    paths = ("Rutas donde buscar ficheros.", []),
    target = ("Ruta destino, donde se guardará la copia de respaldo.", ''),
    compressor = ("Algoritmo de compresión: 'gzip', 'bzip', o '' (solo copia).", 'gzip'),
    exclude = ("Patrones de exclusión.", []),
    full_backup = ("¿Generar una copia de respaldo completa? 'False' crea un copia de respaldo incremental.", False),
    historic_backup = ("¿Genera un copia de respaldo histórica? 'True' crea una subcarpeta por cada copia de respaldo.", False),
    follow_symlinks = ("¿'find' debe seguir enlaces simbólicos?", False),
    debug_level = ("Nivel de depuración (0 a 2)", 1),
    debug_file = ("Fichero de mensajes de depuración. 'False' los muestra por STDOUT.", False),
)

# Logger
logger = activitylog.ActivityLog()

def is_excluded (path):
    for regexp in P['exclude_regexp']:

        if regexp.search(path):
            return True

def header(prepend = ''):
    ''' Devuelve una cabecera para imprimir '''
    h = prepend + 'backup.py v{} - Generador de copias de seguridad incrementales.\n'.format(VERSION)
    h += prepend + 'por Oliver Etchebarne Bejarano\n'
    h += prepend + 'https://drmad.org\n'

    return h

def scan_files (path):
    ''' Escanea la ruta, y devuelve sus ficheros con su timestamp '''

    # Si no existe la ruta, salimos
    if not os.path.exists ( path ):
        return {}

    try:
        raw = subprocess.check_output(
          ['find', '-L' if P['follow_symlinks'] else '-P', path, '-type', 'f', '-printf', '%T@ %P\n']
        )
    except subprocess.CalledProcessError as e:
        logger.fail("El proceso 'find' devolvió error. Saliendo")

    try:
        filelist = raw.decode('utf-8').splitlines()
    except UnicodeDecodeError as e:
        # Vamos a mostrar mas o menos dónde está el error
        pos_match = re.search('position ([0-9]+):', str(e))

        possible_error = ''
        if pos_match:
            pos = int(pos_match.group(1))

            possible_error = '\n\nEl caracter con problemas (representado con un "\\x" más dos letras o números) está en el centro de la siguiente línea:\n\n' + str(raw[pos-40:pos+40])

        logger.fail('Fichero con nombre mal codificado. Debes de actualizar su nombre:\n' + str(e) + possible_error)
        # Iuuu, un fichero que no está en UTF8

    files = {}

    for f in filelist:

        # Verificamos si es un excluido
        if not is_excluded ( f ):
            # Process!

            # Devolvemos un array fichero => timestamp
            parts = f.split (" ", 1)

            # Al revés
            parts.reverse()

            files [ parts[0] ] = parts[1]

    return files


# Creamos el dict P con los parámetros por defecto
P = {}
for key, data in DEFAULT_PARAMETERS.items():
    P [key] = data[1] # data[0] es la descripción

# Sacamos una copia de los argumentos
args = sys.argv[:]

# Medio raro... python no trabaja bien con colas :P asi que le
# damos la vuelta a los parámetros, y usamos el pop
args.reverse()

# Botamos el primero, no nos sirve
args.pop()

# True imprimirá toda la configuración de la línea de comandos.
print_config = False

paths = []

while True:
    try:
        arg = args.pop()
    except IndexError:
        break

    # Si empieza el arg con DOS guiones, comandos GNU!
    if arg[0:2] == '--':
        long_cmd = arg[2:]
        if long_cmd == "help":
            print (header())

            # Ahora, la ayda:
            print('Copia y comprime los ficheros de las rutas especificadas, preservando dueños y permisos.\n\n')
            print('backup.py [opciones] ruta [ruta..] destino\n')
            print('Opciones:')

            options = (
                ('-b', 'Comprime los ficheros con BZ2. Por defecto comprime con Gzip (más rápido).'),
                ('-n', 'No comprime los ficheros.'),
                ('-f', 'Crea una copia completa, en vez de incremental. No es compatible con -h.'),
                ('-h', 'Crea una copia histórica. No es compatible con -f.'),
                ('-H nombre', 'Nombre del directorio para la copia histórica. De omitirse se usará la fecha y hora actual.'),
                ('-x pat', 'Excluye los ficheros que encajan con el patrón de shell "pat". Se puede especificar varias veces.'),
                ('-l fich', 'Graba el registro de actividad completo en el fichero "fich".'),
                ('-d', 'Muestra mayor información en la salida estándar.'),
                ('-q', 'Suprime la salida de información en la salida estándar.'),
                ('-F', 'Fuerza a "find" a seguir enlaces simbólicos'),
                ('-g', 'Genera un fichero de configuración con las opciones especificadas en la línea de comandos.'),
                ('-c conf', 'Usa los parámetros almacenados en el fichero de configuración "conf". Las opciones especificadas después de esta opción reemplazarán a las guardadas en el fichero.'),
                ('--help', 'Esta ayuda.'),
                ('--version', 'Versión de éste script.')
            )

            # Ok, nice formatting!
            descr_tab = max( [len(o[0]) for o in options] )
            descr_tab += 3

            for o in options:
                opt = ' ' + o[0]
                des = o[1]

                print ("{}{}".format ( opt, ' ' * (descr_tab - len (opt))), end="")
                # Ahora, imprimimos la descripción
                x = descr_tab
                for word in des.split (' '):
                    x += len(word)

                    if x > 70:
                        print ("\n" + ' ' * descr_tab, end='')
                        x = descr_tab

                    print (word+ " ", end="")

                print()

            sys.exit()
        elif long_cmd == "version":
            print (header())
            sys.exit()

    # Si empieza con un guión, entonces lo separamos por letras
    elif arg[0] == '-':
        for a in arg:

            # Fichero de configuración?
            if a == 'c':
                try:
                    config_file = args.pop()
                except:
                    fail ( 'Falta el fichero de configuración' )

                # Lo evaluamos.
                with open(config_file) as f:
                    P = eval(f.read())

            # Backup completo
            elif a == 'f':
                P['full_backup'] = True

            # Sigue enlaces simbólicos
            elif a == 'F':
                P['follow_symlinks'] = True

            # Patron a excluir
            elif a == 'x':
                try:
                    pat = args.pop()
                except IndexError:
                    logger.fail('Falta un patrón de exclusión.')

                # Si hay ',' en el patron de exclusión, los dividimos
                if ',' in pat:
                    P['exclude'].extend(pat.split(','))
                else:
                    P['exclude'].append(pat)

            # Fichero de registro
            elif a == 'l':
                try:
                    P['debug_file'] = args.pop()
                except IndexError:
                    logger.fail('Falta el fichero de registro')

            # Reporte detallado
            elif a == 'd':
                P['debug_level'] = 2

            # Sin reporte
            elif a == 'q':
                P['debug_level'] = 0

            # Sigue symlinks?
            elif a == 's':
                P['follow_symlinks'] = True

            # Bzip?
            elif a == 'b':
                P['compressor'] = 'bzip'

            # Sin compresión.
            elif a == 'u':
                P['compressor'] = ''

            # Activamos la grabación de la configuración
            elif a == 'g':
                print_config = True

            # Copia histórica?
            elif a == 'h':
                P['historic_backup'] = True

            elif a == 'H':
                try:
                    P['historic_backup_dir'] = args.pop()
                except IndexError:
                    logger.fail('Falta el nombre del directorio para esta copia histórica.')

    # Si no empieza con '-', entonces son las rutas
    else:
        paths.append ( arg )


# No puede haber full_backup e historic_backup
if P['full_backup'] and P['historic_backup']:
    logger.fail('No se acepta -f y -h juntos.')

# Procesamos las rutas. Tiene que haber AL MENOS 2 rutas
if P['target'] == '' or P['paths'] == []:
    if len(paths) < 2:
        logger.fail('Debes especificar al menos una ruta de origen, y la ruta de destino. Prueba la opción --help.')

    # La ruta de destino es la última
    P['target'] = paths[-1]
    P['paths'] = paths[:-1]

# Queremos imprimir la configuración?
if print_config:
    print(header('# '))
    print("# Fichero de configuración generado a partir de esta línea de comandos:\n#")
    print("#  "  + " ".join(sys.argv))
    print("#\n# Fecha de generación: {}\n".format ( str(datetime.now())))

    print ("dict(")
    for var, rawval in P.items():
        # Formateamos el valor
        if type(rawval) == str:
            val = '"{}"'.format(rawval)
        elif type(var) == bool:
            val = 'True' if val else 'False'
        else:
            val = rawval

        # Imprimimos su ayuda
        print("  # {}".format(DEFAULT_PARAMETERS [var][0]))

        print("  {} = {},\n". format(var, val))

    print(")")

    sys.exit()

# Compilamos los patrones de exclusión
P['exclude_regexp'] = []
for pat in P['exclude']:
    # Convertimos el patrón a un regexp.-
    #   - Los asteriscos los reemplazamos por .*
    #   - Las interrogaciones por .
    #   - Los puntos los escapamos.

    #   - Lo anclamos al final de la linea con $

    pat = pat.replace ( '.', '\.' )
    pat = pat.replace ( '?', '.' )
    pat = pat.replace ( '*', '.*' )
    pat += '$'

    P['exclude_regexp'].append ( re.compile(pat) )


# Definimos qué compresor vamos a usar.
target_extension = ''
if P['compressor'] == 'bzip':
    target_extension = '.bz2'
    target_module = bz2.BZ2File
elif P['compressor'] == 'gzip':
    target_extension = '.gz'
    target_module = gzip.GzipFile
else:
    # Sin compresión. Copiamos
    target_module = False

start_time = time.time()

# Obtenemos la lista de ficheros para sacar backup.
source_files = {}
for path in P['paths']:
    # El path tiene que estar en ABSOLUTO.
    path = os.path.abspath(path)


# Empezamos el proceso
logger.info(header())
logger.info('Línea de comandos: {}'.format (' '.join(sys.argv)))

if P['full_backup']:
    logger.info('Iniciando copia completa.')
elif P['historic_backup']:
    logger.info('Iniciando copia incremental histórica.')
else:
    logger.info('Iniciando copia incremental.')


# Podemos escribir en la carpeta destino?
if not os.access(P['target'], os.W_OK):
    logger.fail('No puedo escribir en la carpeta destino {}'.format(P['target']))

# Existe metadata en la ruta destino?
MD = {}
metadata_file = P["target"] + "/" + METADATA_FILENAME
if os.path.exists(metadata_file):
    with open(metadata_file) as f:
        try:
            MD = json.loads(f.read())
        except json.decoder.JSONDecodeError:
            logger.warning("Fichero de metadata existe, pero es ilegible. Eliminando...")
            os.unlink(metadata_file)

# En historic_backup, debemos añadir una carpeta raiz extra
historic_path = ''
if P['historic_backup']:
    if not P['historic_backup_dir']:
        P['historic_backup_dir'] = datetime.now().strftime('%Y%m%d%H%M%S')

    historic_path = P['historic_backup_dir']

for path in P['paths']:

    # El path tiene que estar en ABSOLUTO.
    path = os.path.abspath(path)

    # Grabamos el momento que se inició la copia de respaldo.
    start_time = time.time()


    # Calculamnos la carpeta destino, dependiendo
    # si quieremos solo una, o toda la ruta completa

    # 'path' contiene la ruta absoluta del fichero que
    # queremos. Le removemos el 1er slash para que
    # os.path.join no descarte los parámetros anteriores
    # (http://docs.python.org/3.2/library/os.path.html#os.path.join)
    target_path = os.path.join(P['target'], historic_path, path[1:])

    # Creamos la carpeta destino siempre. Para que el find no falle
    try:
        os.makedirs(target_path)
    except:
        pass

    # Primero, escaneamos el origen
    logger.info('{}: Escaneando origen...'.format (path))
    files_data = scan_files (path)

    # Luego escaneamos el destino, si no pide un full_backup
    registry = {}

    # scan_path puede ser target_path para backups regulares
    # o el anterior directorio creado, para historicos-
    target_scan_path = target_path

    if P['historic_backup']:
        if 'last_historic_dir' in MD:
            target_scan_path = os.path.join(P['target'], MD['last_historic_dir'], path[1:])
        else:
            target_scan_path = None

    if not target_scan_path:
        logger.info('{}: Primer backup. Usando backup total'.format(path))
    elif not P['full_backup']:
        logger.info('{}: Escaneando destino...'.format(path))
        registry = scan_files (target_scan_path)

    logger.info('{}: {} ficheros. Destino: "{}", iniciando copia.'.format ( path, len(files_data), target_path))

    # Aquí irá el registro con los nuevos timestamps
    new_registry = registry.copy()

    # Aqui quedarán los ficheros por borrar
    erase_list = registry.copy()

    # Contadores
    c_new = 0
    c_updated = 0
    c_deleted = 0
    c_old = 0


    # Escaneamos sus ficheros
    for filename, timestamp in files_data.items():

        # De este timestamp sacamos el usuario, grupo, y permisos
        # TODO

        # No existe, o ha variado?
        copy = False

        # Hardlink para historic_backup?
        hardlink = False

        if not filename + target_extension in registry:
            # Nuevo fichero.
            copy = "GUARDANDO"
            c_new += 1
        elif registry [ filename + target_extension ] != timestamp:

            # Actualizando uno antiguo
            copy = "ACTUALIZANDO"
            c_updated += 1
            del erase_list[filename + target_extension]
        else:
            # Igual, si no está modificado, lo borramos del erase_list
            del erase_list[filename + target_extension]

            # Si es un historic_backup, hacemos un hardlink de la copia de respaldo anterior
            hardlink = True

        if copy:
            # Empezamos la generación de la copia de seguridad.
            target_filename = os.path.join (target_path, filename)

            logger.debug("{} {}...".format(copy, filename))

            # Creamos la carpeta destino, si no existe. Con algo de suerte,
            # podemos ignorar tranquilamente los errores
            try:
                os.makedirs(os.path.dirname(target_filename))
            except Exception as e :
                pass

            source_filename = os.path.join(path, filename)

            # Ya que también copiamos los atributos del fichero, puede sucede
            # que cuando actualizamos, el fichero anterior no tiene permisos
            # de escritura. Asi que le damos permisos de escritura primero.

            # Si no podemos camiarle, no podemos psss :)
            try:
                os.chmod (target_filename, stat.S_IWUSR)
            except:
                pass


            # Comprimimos?
            if target_module:
                target_filename += target_extension

                # Intentamos abrir el fichero
                try:
                    with target_module(target_filename, 'wb') as target_fd, open (source_filename, 'rb') as source_fd:

                        # Procesamos en 9000k a la vez (10 chunks de 900k,
                        # el usado por la máxima compresión del gzip. Debe de
                        # ser igual para bzip2)
                        while 1:
                            count = target_fd.write (source_fd.read(9216000) )
                            if count == 0:
                                break;

                except Exception as e:
                    logger.warning('No pude copiar {} ({}) '.format(filename, str(e)))

            else:
                # Si no hay target, es una simple copia.
                try:
                    shutil.copy (source_filename, target_filename)
                except Exception as e:
                    logger.warning('ADVERTENCIA: No pude copiar {} ({}) '.format(filename, str(e)))


            try:
                # Después de copiar, actualizamos permisos y dueño
                st = os.stat (source_filename)

                shutil.copystat (source_filename, target_filename)
                os.chown (target_filename, st.st_uid, st.st_gid)
            except Exception as e:
                # No pudimos cambiarle de permisos!
                logger.warning('No pude copiar permisos ni dueño de {} ({}).'.format ( filename, str(e) ) )

            # Y actualizamos el fichero de registro
            new_registry [ filename ] = timestamp

        if hardlink:
            source_filename = os.path.join(target_scan_path, filename + target_extension)
            target_filename = os.path.join(target_path, filename + target_extension)


            # Creamos la carpeta destino, si no existe. Con algo de suerte,
            # podemos ignorar tranquilamente los errores
            try:
                os.makedirs(os.path.dirname(target_filename))
            except Exception as e :
                pass

            os.link(source_filename, target_filename)

            # BIG BIG CHANGE

    # Hay por borrar? Solo si NO estamos en backup historico
    if erase_list and not P['historic_backup']:
        # Calculamos cuál sería el fichero destino
        c_deleted = len (erase_list)
        for filename in erase_list.keys():

            # borramos
            logger.debug("BORRANDO {}...".format(filename))
            try:
                target_filename = os.path.join(target_path, filename)
                os.unlink(target_filename)
            except Exception as e:
                logger.warning('No pude eliminar {} ({}).'.format(filename, str(e)))

    # Calculamos el tiempo tomado
    elapsed_time = str(timedelta(seconds = time.time() - start_time))

    logger.info('{}: Finalizado. {} nuevos, {} actualizados, {} borrados. Duración: {}'. format(path, c_new, c_updated, c_deleted, elapsed_time))

# Si hay un historic_path, lo guardamos para la siguiente vez
if historic_path:
    MD['last_historic_dir'] = historic_path

# Si hay metadata, la grabamos
if MD:
    with open(metadata_file, 'w') as f:
        f.write(json.dumps(MD))
