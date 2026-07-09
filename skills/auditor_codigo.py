import os
import ast

def auditoria_codigo():
    # Obtener la lista de habilidades en el directorio 'skills'
    if not os.path.exists('skills'):
        print("La carpeta 'skills' no existe.")
        return
        
    habilidades = os.listdir('skills')

    # Iterar sobre cada habilidad para analizarla
    for habilidad in habilidades:
        if not habilidad.endswith('.py'):
            continue
            
        ruta_archivo = f'skills/{habilidad}'
        with open(ruta_archivo, 'r') as archivo:
            contenido = archivo.read()

            # Analizar el código utilizando el módulo ast
            try:
                tree = ast.parse(contenido)
            except SyntaxError as e:
                print(f'Error de sintaxis en {habilidad}: {e}')
                continue
            
            # Buscar funciones definidas pero no utilizadas (en el mismo archivo)
            funciones_no_utilizadas = []
            for nodo in ast.walk(tree):
                if isinstance(nodo, ast.FunctionDef):
                    # Comprobamos si el nombre de la función aparece más de una vez (definición + uso)
                    if contenido.count(nodo.name) <= 1:
                        funciones_no_utilizadas.append(nodo.name)
            
            if funciones_no_utilizadas:
                print(f'Funciones no utilizadas en {habilidad}: {funciones_no_utilizadas}')
            
            # Buscar líneas de código duplicadas usando un set para mayor eficiencia
            lineas = contenido.split('\n')
            vistas = set()
            lineas_duplicadas = set()
            
            for linea in lineas:
                linea_limpia = linea.strip()
                if not linea_limpia or linea_limpia.startswith('#'):
                    continue
                if linea_limpia in vistas:
                    lineas_duplicadas.add(linea_limpia)
                else:
                    vistas.add(linea_limpia)
            
            if lineas_duplicadas:
                print(f'Líneas de código duplicadas en {habilidad}: {list(lineas_duplicadas)}')

# Punto de entrada para ejecución directa
if __name__ == "__main__":
    auditoria_codigo()
