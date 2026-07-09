def dividir_por_cero():
    try:
        return 1 / 0
    except ZeroDivisionError:
        return 'No se puede dividir por cero'
