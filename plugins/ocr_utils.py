import pytesseract

from PIL import Image
from pdf2image import convert_from_path


def extraer_texto_imagen(ruta):
    img = Image.open(ruta)
    return pytesseract.image_to_string(
        img,
        lang="spa"
    )


def extraer_texto_pdf_ocr(ruta_pdf):
    paginas = convert_from_path(ruta_pdf)

    textos = []

    for pagina in paginas:
        texto = pytesseract.image_to_string(
            pagina,
            lang="spa"
        )

        textos.append(texto)

    return "\n\n".join(textos)
