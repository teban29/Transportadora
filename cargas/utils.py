import os
import tempfile
from io import BytesIO
import barcode
from barcode.writer import ImageWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import mm, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER
from django.utils import timezone
from PIL import Image

def generar_codigo_barras_unico(inventario):
    """
    Genera un PDF para impresora de labels (80x100mm) con:
    - Código de barras escaneable (IDs numéricos)
    - Información legible en formato: cliente|producto|carga|remisión
    """
    # Tamaño personalizado (100x80mm en landscape = 10x8cm)
    label_width, label_height = 100*mm, 80*mm
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape((label_width, label_height)))
    
    # Margenes reducidos para aprovechar espacio
    margin = 5*mm
    inner_width = label_width - 2*margin
    inner_height = label_height - 2*margin
    
    # 1. Código escaneable (formato numérico)
    codigo_unico = f"{inventario.carga.cliente.id}-{inventario.producto.id}-{inventario.carga.id}-{inventario.carga.remision}"
    
    # 2. Información legible (formato texto)
    info_legible = f"{inventario.carga.cliente.nombre}|{inventario.producto.nombre}|{inventario.carga.nombre}|{inventario.carga.remision}"
    
    if not inventario.codigo_barras:
        inventario.codigo_barras = codigo_unico
        inventario.info_legible = info_legible
        inventario.fecha_generacion_codigo = timezone.now()
        inventario.save()

    try:
        # Configuración optimizada para impresión
        options = {
            'write_text': False,
            'module_width': 0.3,  # Más grueso para mejor lectura
            'module_height': 12,
            'quiet_zone': 4,
            'font_size': 0,
            'background': 'white',
            'foreground': 'black'
        }
        
        # Generar código de barras
        code = barcode.get('code128', codigo_unico, writer=ImageWriter())
        barcode_buffer = BytesIO()
        code.write(barcode_buffer, options=options)
        barcode_buffer.seek(0)
        
        # Convertir a imagen
        img = Image.open(barcode_buffer)
        temp_path = os.path.join(tempfile.gettempdir(), f"barcode_{inventario.id}.png")
        img.save(temp_path, 'PNG', dpi=(300,300))  # Alta resolución

        # --- DISEÑO OPTIMIZADO PARA LABEL ---
        # 1. Código de barras (60% del espacio)
        barcode_height = 45*mm  # Más grande
        barcode_width = 80*mm
        c.drawImage(temp_path,
                  (label_width - barcode_width)/2,  # Centrado
                  label_height - barcode_height - 10*mm,
                  width=barcode_width,
                  height=barcode_height,
                  preserveAspectRatio=True,
                  mask='auto')
        
        # 2. Información textual (40% del espacio)
        styles = getSampleStyleSheet()
        style = styles["Normal"]
        style.alignment = TA_CENTER
        style.fontSize = 7  # Tamaño ajustado
        style.leading = 3   # Espaciado entre líneas
        
        info_lines = [
            f"<b>CLI:</b> {inventario.carga.cliente.nombre[:20]}",
            f"<b>PROD:</b> {inventario.producto.nombre[:20]}",
            f"<b>CARGA:</b> {inventario.carga.nombre}",
            f"<b>REM:</b> {inventario.carga.remision}",
            f"<b>ID:</b> {codigo_unico}"
        ]
        
        y_position = 10*mm
        for line in info_lines:
            p = Paragraph(line, style)
            p.wrapOn(c, inner_width, 10*mm)
            p.drawOn(c, margin, y_position)
            y_position += 7*mm  # Espaciado vertical

    except Exception as e:
        raise Exception(f"Error generando código: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    c.save()
    buffer.seek(0)
    return buffer