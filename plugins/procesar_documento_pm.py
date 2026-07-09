import os
from datetime import datetime

from pypdf import PdfReader
from docx import Document
from plugins.generar_paquete_pm import run as generar_paquete
from plugins.ocr_utils import extraer_texto_imagen, extraer_texto_pdf_ocr

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def leer_txt_md(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read().strip()


def leer_pdf(ruta):
    reader = PdfReader(ruta)
    textos = []

    for page in reader.pages:
        texto = page.extract_text() or ""
        textos.append(texto)

    return "\n\n".join(textos).strip()


def leer_docx(ruta):
    doc = Document(ruta)
    textos = []

    for p in doc.paragraphs:
        if p.text.strip():
            textos.append(p.text.strip())

    return "\n".join(textos).strip()


def run(params=None):
    params = params or {}

    proyecto_id = params.get("proyecto_id", "proyecto_001")
    ruta = params.get("ruta", "").strip()
    titulo = params.get("titulo", "Documento procesado por PM Copilot")

    if not ruta:
        return {"ok": False, "error": "No se recibió ruta del documento."}

    ruta_absoluta = ruta if os.path.isabs(ruta) else os.path.join(BASE_DIR, ruta)

    if not os.path.exists(ruta_absoluta):
        return {"ok": False, "error": f"No existe el documento: {ruta}"}

    extension = os.path.splitext(ruta_absoluta)[1].lower()
    metodo_extraccion = ""

    try:
        if extension in [".txt", ".md"]:
            contenido = leer_txt_md(ruta_absoluta)
            metodo_extraccion = "texto_directo"

        elif extension == ".docx":
            contenido = leer_docx(ruta_absoluta)
            metodo_extraccion = "docx"

        elif extension == ".pdf":
            contenido = leer_pdf(ruta_absoluta)
            metodo_extraccion = "pdf_texto"

            if not contenido:
                contenido = extraer_texto_pdf_ocr(ruta_absoluta)
                metodo_extraccion = "pdf_ocr"

        elif extension in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
            contenido = extraer_texto_imagen(ruta_absoluta)
            metodo_extraccion = "imagen_ocr"

        else:
            return {
                "ok": False,
                "error": f"Formato no soportado: {extension}. Soportados: .txt, .md, .pdf, .docx, .jpg, .jpeg, .png, .bmp, .tiff"
            }

    except Exception as e:
        return {"ok": False, "error": f"No se pudo extraer texto del documento: {e}"}

    contenido = contenido.strip()

    if not contenido:
        return {
            "ok": False,
            "error": "No se pudo extraer texto del documento, incluso usando OCR."
        }

    resultado_paquete = generar_paquete({
        "proyecto_id": proyecto_id,
        "titulo": titulo,
        "contenido": contenido
    })

    return {
        "ok": resultado_paquete.get("ok", False),
        "mensaje": "Documento PM procesado correctamente" if resultado_paquete.get("ok") else "Documento procesado con errores",
        "proyecto_id": proyecto_id,
        "ruta_documento": ruta_absoluta,
        "extension": extension,
        "metodo_extraccion": metodo_extraccion,
        "caracteres_extraidos": len(contenido),
        "fecha": datetime.utcnow().isoformat() + "Z",
        "resultado_paquete": resultado_paquete
    }
