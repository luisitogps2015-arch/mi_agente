import os
print("Analizando el estado del sistema y la estructura de archivos...")
archivos = os.listdir('.')
print(f"Archivos detectados: {archivos}")
if 'skills' in archivos:
    print("Estado: La carpeta de habilidades está activa.")
else:
    print("Estado: Falta la carpeta de habilidades, sugiero crearla.")
if 'agente_memoria.db' in archivos:
    print("Estado: La base de datos de memoria está activa.")
else:
    print("Estado: Base de datos no encontrada.")