def reportar_errores(errores):
    with open('resumen_auditoria.txt', 'w') as f:
        for error in errores:
            f.write(error + '\n')