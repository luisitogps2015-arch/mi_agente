import re
def analizar_logs(archivo_log):
    # Abrir el archivo de log y leer su contenido
    with open(archivo_log, 'r') as f:
        log_contenido = f.read()

    # Extraer informacion util del log usando expresiones regulares
    errores = re.findall(r'Error: (.*)', log_contenido)
    advertencias = re.findall(r'Warning: (.*)', log_contenido)

    # Imprimir los resultados
    print("Errores encontrados:")
    for error in errores:
        print(error)

    print("\nAdvertencias encontradas:")
    for advertencia in advertencias:
        print(advertencia)

# Ejecutar la funcion con el archivo de log detectado
analizar_logs('agente.log')