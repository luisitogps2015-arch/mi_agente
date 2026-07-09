import qrcode

def crear_qr(texto):
    img = qrcode.make(texto)
    img.save('archivo_qr.png')
    return 'Archivo QR creado correctamente'