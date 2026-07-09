def verificar_sistema():
    import datetime
    fecha_hora_actual = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open('log_sistema.txt', 'a') as archivo:
        archivo.write(fecha_hora_actual + '\n')
    # Resto del código de la función...