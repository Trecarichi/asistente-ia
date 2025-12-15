import os
import time

fecha_modificacion = os.path.getmtime('datos_tierras.csv')
fecha_modificacion_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(fecha_modificacion))

# Imprime la fecha de modificación
print('Fecha de modificación:', fecha_modificacion_str)