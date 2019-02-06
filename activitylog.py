from datetime import datetime
import sys

class ActivityLog:
    DEBUG = 3
    INFO = 2
    WARNING = 1
    ERROR = 0

    LEVEL_LABEL = {
        DEBUG : 'debug',
        INFO : 'info',
        WARNING : 'warning',
        ERROR : 'error',
    }

    log_fd = None
    log_level = 2 # Solo errores

    def set_log_level(self, log_level):
        self.log_level = log_level
        return self

    def set_log_file(self, log_file):
        self.log_fd = open(log_file, "a", 0)
        return self

    def log(self, level, message, set_date = False):
        # Añadimos la fecha, de ser necesario
        message ="{} {}".format(datetime.now(), message)

        # Siempre guardamos todos los mensajes en el fichero de registro
        if self.log_fd:
            self.log_fd.write(message + "\n")

        if level <= self.log_level:
            print(message)

    def debug(self, message, set_date = False):
        self.log(self.DEBUG, message, set_date)

    def info(self, message, set_date = False):
        self.log(self.INFO, message, set_date)

    def warning(self, message, set_date = False):
        self.log(self.WARNING, message, set_date)

    def error(self, message, set_date = False):
        self.log(self.ERROR, message, set_date)

    def fail(self, message, set_date = False):
        ''' Igual que 'error', pero acaba el programa '''
        self.error(message, set_date)
        sys.exit(1)
