import os
import tempfile
from io import BytesIO
import barcode
from barcode.writer import ImageWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import mm, A6  # Tamaño A6 (105x148mm)
from reportlab.lib.pagesizes import landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER

def generar_codigo_barras_unico(inventario):
    """
    Genera un PDF con código de barras único para el producto
    Mantiene el formato visual existente pero el código escaneable contendrá:
    cliente|producto|carga|remisión
    """
    # Configuración del PDF (tamaño A6 en horizontal) - SIN CAMBIOS VISUALES
    buffer = BytesIO()
    pdf_width, pdf_height = landscape(A6)
    c = canvas.Canvas(buffer, pagesize=(pdf_width, pdf_height))
    
    # Margenes y áreas definidas - SIN CAMBIOS
    margin = 10*mm
    inner_width = pdf_width - 2*margin
    inner_height = pdf_height - 2*margin
    
    # SOLO CAMBIO AQUÍ: Formato del código escaneable (usando pipe como separador)
    codigo_unico = (
        f"{inventario.carga.cliente.nombre}|"
        f"{inventario.producto.nombre}|"
        f"{inventario.carga.nombre}|"
        f"{inventario.carga.remision}"
    )
    
    # Generar imagen del código de barras (usando archivo temporal) - RESTO SIN CAMBIOS
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            options = {
                'write_text': False,
                'module_height': 12,
                'quiet_zone': 5,
                'font_size': 0,
                'text_distance': 1
            }
            code = barcode.get('code128', codigo_unico, writer=ImageWriter())
            code.write(temp_file, options=options)
            temp_path = temp_file.name
        
        # --- DISEÑO DEL STICKER (MISMO FORMATO EXACTO) ---
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(1.5)
        c.rect(margin, margin, inner_width, inner_height)
        
        barcode_height = 25*mm
        header_height = 15*mm
        info_height = inner_height - barcode_height - header_height - 5*mm
        
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(pdf_width/2, margin + inner_height - 12*mm, "CONTROL DE INVENTARIO")
        
        barcode_y = margin + info_height + 5*mm
        c.drawImage(temp_path, 
                   (pdf_width-80*mm)/2, 
                   barcode_y, 
                   width=80*mm, 
                   height=barcode_height,
                   preserveAspectRatio=True)
        
        styles = getSampleStyleSheet()
        style = styles["Normal"]
        style.alignment = TA_CENTER
        style.fontSize = 10
        style.leading = 12
        
        c.setFont("Helvetica-Bold", 16)
        
        info_text = [
            f"<b>Carga:</b> {inventario.carga.nombre}",
            f"<b>Cliente:</b> {inventario.carga.cliente.nombre}",
            f"<b>Remisión:</b> {inventario.carga.remision}",
        ]
        
        y_position = margin + info_height - 10*mm
        for line in info_text:
            p = Paragraph(line, style)
            p.wrapOn(c, inner_width - 20*mm, 15*mm)
            p.drawOn(c, margin + 10*mm, y_position)
            y_position -= 8*mm
        
        os.unlink(temp_path)
        
    except Exception as e:
        raise Exception(f"Error generando código de barras: {str(e)}")
    
    c.save()
    buffer.seek(0)
    return buffer