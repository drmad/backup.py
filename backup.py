#!/usr/bin/env python3
'''
backup.py
=========

Generador de copias de seguridad incrementales.
por Oliver Etchebarne - Paperclip X10
http://drmad.org - http://x10.pe

Genera copias de seguridad incrementales de cada ruta especificada, dentro de la carpeta destino. Comprime los ficheros y preservan dueños y permisos. No borra los ficheros si sus originales han sido borrados.

Debería de trabaja en cualquier distro de Linux con Python > 3.2

https://github.com/drmad/backup.py
'''

import subprocess, sys, re, os
import gzip, bz2, shutil, stat
import time

from datetime import datetime, timedelta

VERSION = 0.91

# Parámetros por defecto, con su ayuda. 
DEFAULT_PARAMETERS = dict(
    paths = ("Rutas donde buscar ficheros.", []),
    
    target = ("Ruta donde se guardará el backup.", ''),
    
    compressor = ("Algoritmo de compresión: 'gzip', 'bzip', o '' (solo copia).", 'gzip'),
    
    registry_file = ("Nombre del fichero de registro.", '.backup.info'),

    exclude = ("Patrones de exclusión.", []),
    
    one_dir_per_param = ("¿Generar una carpeta por parámetro? 'False' crea la estructura completa de directorios.", False),
    
    full_backup = ("¿Generar un backup completo? 'False' crea un backup incremental.", False ),
    
    follow_symlinks = ( "¿'find' debe seguir enlaces simbólicos?", False ),
    
    debug_level = ("Nivel de depuración (0 a 2)", 1),
    
    debug_file = ("Fichero de mensajes de depuración. 'False' los muestra por STDOUT.", False),
)

def fail ( reason ):
    # Grabamos en el log
    log ( 'ERROR: ' + reason )
    
    # También escribimos en stderr. Puede causar duplicados, pero meh...
    sys.stderr.write ( 'ERROR: {}\n'.format( reason ) )
    
    # Bu-bye
    sys.exit ( 1 )

def log ( what, verbose = False, no_date = False ):
    ''' Graba información de registro. Lo "verbose" se procesa, si debug_level
        es 2. '''

    # Añadimos una fecha?
    if not no_date:
        what = str(datetime.now()) + ' ' + what

    # Siempre guardamos en el fichero todo, sin importar el nivel de 'verbose'
    try:
        P['debug_file_fd'].write ( what + "\n" )
    except:
        pass

    # En la salida estándar, solo mostramos lo requerido.        
    if verbose and P['debug_level'] < 2:
        return
    
    if P['debug_level'] == 0:
        return

    print ( what )

def is_excluded ( path ):
    for regexp in P['exclude_regexp']:
    
        if regexp.search ( path ):
            return True

def get_registry ( path ):
    regpath = os.path.join ( path, P['registry_file'] )

    # Si existe el ficheor de registro, lo leemos
    if os.path.exists ( regpath ):
        with open(regpath) as f:
            return eval(f.read())

    else:
        return {}

def header( prepend = '' ):
    ''' Devuelve una cabecera para imprimir '''
    h = ''
    h = prepend + 'backup.py v{} - Generador de copias de seguridad incrementales.\n'.format(VERSION)
    h += prepend + 'por Oliver Etchebarne - Paperclip X10\n'
    h += prepend + 'http://drmad.org - http://x10.pe\n'
    
    return h

def save_registry ( path, registry ):
    ''' Graba un fichero de registro '''
    regpath = os.path.join ( path, P['registry_file'] )
    
    with open ( regpath, 'w' ) as f:
        f.write ( header ('# ') )
        f.write ( '\n# Fichero de registro de fechas de modificación. NO EDITAR\n')
        f.write ( '# {} - {}\n'.format ( path, datetime.today().strftime ('%c') ) )
        
        f.write ( '{\n' )
        
        for fn, timestamp in registry.items():
            f.write ( "  '{}': '{}',\n".format ( fn.replace("'", "\\'"), timestamp ) )

        f.write ('}\n')
            

def scan_files ( path ):
    ''' Escanea la ruta, y devuelve sus ficheros con su timestamp '''

    try:    
        raw = subprocess.check_output (
          [ 'find', '-L' if P['follow_symlinks'] else '', path, '-type', 'f', '-printf', '%C@ %P\n' ]
        )
    except subprocess.CalledProcessError as e: 
        fail ( "El proceso 'find' devolvió error. Saliendo" )

    try:    
        filelist=raw.decode('utf-8').splitlines()
    except UnicodeDecodeError as e:
        # Vamos a mostrar mas o menos dónde está el error
        pos_match = re.search ( 'position ([0-9]+):', str(e) )
        
        possible_error = ''
        if pos_match:
            pos = int(pos_match.group(1))
            
            possible_error = '\n\nEl caracter con problemas (representado con un "\\x" más dos letras o números) está en el centro de la siguiente línea:\n\n' + str(raw[pos-40:pos+40])
            
        fail ( 'Fichero con nombre mal codificado. Debes de actualizar su nombre:\n' + str(e) + possible_error )
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
    P [ key ] = data[1]

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

while (1):
    try:
        arg = args.pop()
    except IndexError:
        break

    # Si empieza el arg con DOS guiones, comandos GNU!
    if arg[0:2] == '--':
        long_cmd = arg[2:]
        if long_cmd == "help":
            log ( header(), no_date = True )

            # Ahora, la ayda:
            log ( 'Copia el conteido de cada ruta especificada dentro de la carpeta destino,\ncomprimiendo los ficheros y preservando dueños y permisos.\n\nEste script no borra los ficheros si sus originales si lo han sido borrados.\n', no_date = True)
            log ( 'backup.py [opciones] ruta [ruta..] destino\n', no_date = True)
            log ( 'Opciones:', no_date = True )
            
            options = (
                ( '-b', 'Comprime los ficheros con BZ2. Por defecto comprime con Gzip (más rápido).' ),
                ( '-n', 'No comprime los ficheros.' ),
                ( '-f', 'Crea una copia completa, en vez de incremental.'),
                ( '-x pat', 'Excluye los ficheros que encajan con el patrón de shell "pat". Se puede especificar varias veces.' ),
                ( '-l fich', 'Graba el registro de actividad completo en el fichero "fich".' ),
                ( '-d', 'Muestra mayor información en la salida estándar.' ),
                ( '-q', 'Suprime la salida de información en la salida estándar.' ),
                ( '-o', 'Crea un directorio por cada ruta especificada, en vez de recrear el árbol completo en el directorio destino.' ),
                ( '-F', 'Fuerza a "find" a seguir enlaces simbólicos' ), 
                ( '-g', 'Genera un fichero de configuración con las opciones especificadas en la línea de comandos.' ),
                ( '-c conf', 'Usa los parámetros almacenados en el fichero de configuración "conf". Las opciones especificadas después de esta opción reemplazarán a las guardadas en el fichero.'),
                ( '--help', 'Esta ayuda.' ),
                ( '--version', 'Versión de éste script.')
            )
            
            # Ok, nice formatting!
            descr_tab = max( [len(o[0]) for o in options] )
            descr_tab += 3
            
            for o in options:
                opt = ' ' + o[0]
                des = o[1]
            
            
                print ( "{}{}".format ( opt, ' ' * (descr_tab - len (opt))), end="")
                # Ahora, imprimimos la descripción
                x = descr_tab
                for word in des.split (' '):
                    x += len(word)
                    
                    if x > 70:
                        print ( "\n" + ' ' * descr_tab, end='' )
                        x = descr_tab
                    
                    print (word+ " ", end="")

                print()
            
            sys.exit()
        elif long_cmd == "version":
            log ( header() )
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
                    fail ( 'Falta un patrón de exclusión.' )

                
                P['exclude'].append ( pat )

            # Fichero de registro
            elif a == 'l':
                try:
                    P['debug_file'] = args.pop()
                except IndexError:
                    fail ( 'Falta el fichero de registro' )
                    
            # Reporte detallado
            elif a == 'd':
                P['debug_level'] = 2
                
            # Sin reporte
            elif a == 'q':
                P['debug_level'] = 0
                
            # Una carpeta por ruta?
            elif a == 'o':
                P['one_dir_per_param'] = True

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
                

    
    # Si no empieza con '-', entonces son las rutas
    else:
        paths.append ( arg )

# Procesamos las rutas. Tiene que haber AL MENOS 2 rutas
if P['target'] == '' or P['paths'] == []:
    if ( len (paths) < 2 ):
        fail ( 'Debes especificar al menos una ruta de origen, y la ruta de destino. Prueba la opción --help.' )
        
    # La ruta de destino es la última
    P['target'] = paths[-1]
    P['paths'] = paths[:-1]


# Queremos imprimir la configuración?
if print_config:
    print ( header('# ') )
    print ( "# Fichero de configuración generado a partir de esta línea de comandos:\n#")
    print ( "#  "  + " ".join(sys.argv) )
    print ( "#\n# Fecha de generación: {}\n".format ( str(datetime.now()) ) )

    print ( "dict(" )
    for var, rawval in P.items():
        # Formateamos el valor
        if type( rawval ) == str:
            val = '"{}"'.format( rawval )
        elif type( var ) == bool:
            val = 'True' if val else 'False'
        else:
            val = rawval

        # Imprimimos su ayuda
        print ( "  # {}".format ( DEFAULT_PARAMETERS [var][0] ) )
            
        print ( "  {} = {},\n". format ( var, val ) )
        
    print ( ")" )

    sys.exit()


# Abrimos el fichero de registro, sin buffer.
try:
    P['debug_file_fd'] = open ( P['debug_file'], 'a', 1 )
except Exception as e:
    fail ( 'No se pudo abrir el fichero de registro: ' + str (e) )


# Añadimos el fichero de registro a la lista de exclusión. Esto
# lo hacemos después de haber grabado el fichero de configuración.
P['exclude'].append ( P['registry_file'] )

# Compilamos los patrones de exclusión
P['exclude_regexp'] = []
for pat in P['exclude']:
    # Convertimos el patrón a un regexp.-
    #   - Los asteriscos los reemplazamos por .*
    #   - Las interrogaciones por .
    #   - Los puntos los escapamos.
    #   - Lo anclamos al final de la liena con $                

    pat = pat.replace ( '.', '\.' )
    pat = pat.replace ( '?', '.' )
    pat = pat.replace ( '*', '.*' )
    pat += '$'
    
    P['exclude_regexp'].append ( re.compile(pat) )


# Empezamos el proceso
log ( header(), no_date = True ) 

if ( P['full_backup'] ):
    log ( 'Ejecutando copia completa la siguiente línea de comandos:', verbose=True )
else:
    log ( 'Ejecutando copia incremental con la siguiente línea de comandos:', verbose=True )
    
log ( ' {}'.format ( ' '.join(sys.argv) ), verbose=True )

for path in P['paths']:

    # El path tiene que estar en ABSOLUTO.
    path = os.path.abspath ( path )
    
    # Grabamos el momento que se inició el backup.
    start_time = time.time()

    # Leemos su fichero de registro, si existe. 
    if ( P['full_backup'] ):
        registry = {}
    else:
        registry = get_registry ( path )



    # Escaneamos el contenido de 'path'    
    log ( '{}: Escaneando ruta...'.format ( path ), verbose=True )
    files_data = scan_files ( path )
    
    # Calculamnos la carpeta destino, dependiendo
    # si quieremos solo una, o toda la ruta completa

    if P["one_dir_per_param"]:

        # El nombre de la carpeta será la ruta absoluta, 
        # con los \ reemplazados por _ 
        base_path = path[1:].strip('/')
        base_path = base_path.replace('/', '_')
        base_path = base_path.replace(' ', '_')

        target_path = os.path.join ( P['target'], base_path)

    else:
        # 'path' contiene la ruta absoluta del fichero que
        # queremos. Le removemos el 1er slash para que
        # os.path.join no descarte los parámetros anteriores
        # ( http://docs.python.org/3.2/library/os.path.html#os.path.join )    
        target_path = os.path.join ( P['target'], path[1:] )


    log ( '{}: {} ficheros. Destino: "{}", iniciando copia.'.format ( path, len(files_data), target_path ) )

    # Aquí irá el registro con los nuevos timestamps
    new_registry = registry.copy()
    
    # Contadores
    c_new = 0
    c_updated = 0

    # Escaneamos sus ficheros
    for filename, timestamp in files_data.items():
        # No existe, o ha variado?
        copy = False
        
        if not filename in registry:
            copy = "Guardando"
            c_new += 1
        elif registry [ filename ] != timestamp:
            copy = "Actualizando"
            c_updated += 1

        if copy:
            # Empezamos la generación de la copia de seguridad.
            target_filename = os.path.join (  target_path, filename )

            log ( "- {} {}...".format(copy, filename ), verbose = True )

            # Creamos la carpeta destino, si no existe. Con algo de suerte,
            # podemos ignorar tranquilamente los errores
            try:
                os.makedirs ( os.path.dirname ( target_filename ) ) 
            except:
                pass

            source_filename = os.path.join ( path, filename )
            
            if P['compressor'] == 'bzip':
                target_filename += '.bz2'
                target_module = bz2.BZ2File
            elif P['compressor'] == 'gzip':
                target_filename += '.gz'
                target_module = gzip.GzipFile
            else:   
                # Sin compresión. Copiamos
                target_module = False

            # Ya que también copiamos los atributos del fichero, puede sucede
            # que cuando actualizamos, el fichero anterior no tiene permisos
            # de escritura. Asi que le forzamos primero
            
            # Si no podemos camiarle, no podemos psss :)
            try:
                os.chmod (target_filename, stat.S_IWUSR)
            except:
                pass

                
            if target_module:
                # Intentamos abrir el fichero
                try:
                    with target_module ( target_filename, 'wb' ) as target_fd, open ( source_filename, 'rb' ) as source_fd:
                        
                        # Procesamos en 9000k a la vez (10 chunks de 900k, 
                        # el usado por la máxima compresión del gzip. Debe de
                        # ser igual para bzip2)
                        while 1:
                            count = target_fd.write (source_fd.read(9216000) )
                            if count == 0:
                                break;
                        
                except Exception as e:
                    fail ( 'No se pudo realizar la copia: ' + str(e) )
                    
            else:
                # Si no hay target, es una simple copia.
                shutil.copy ( source_filename, target_filename )
                
            # Después de copiar, actualizamos permisos y dueño
            st = os.stat ( source_filename )

            os.chmod ( target_filename, st.st_mode )
            os.chown ( target_filename, st.st_uid, st.st_gid )
            
            # Y actualizamos el fichero de registro
            new_registry [ filename ] = timestamp

    # Regeneramos el registro, con las nuevas fechas de actualización.
    save_registry ( path, new_registry )
    
    # Calculamos el tiempo tomado
    elapsed_time = str(timedelta ( seconds = time.time() - start_time ))
    
    log ( '{}: Finalizado. Nuevos: {}, Actualizados: {}, Duración: {}'. format ( path, c_new, c_updated, elapsed_time ) )
    
