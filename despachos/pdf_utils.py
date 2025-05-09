from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.units import inch
from django.conf import settings
import os
from django.utils import timezone

def generate_despacho_pdf(despacho):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Configuración inicial
    width, height = letter
    styles = getSampleStyleSheet()
    
    # Margen horizontal simétrico
    margin_horizontal = 50  # 50 puntos (aproximadamente 0.7 pulgadas)
    
    # Logo de la empresa
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo.png')
    if os.path.exists(logo_path):
        c.drawImage(logo_path, margin_horizontal, height - 100, width=100, height=80, preserveAspectRatio=True)
    
    # Encabezado - Nombre de la empresa CENTRADO
    c.setFont("Helvetica-Bold", 16)
    text_width = c.stringWidth("TRANSPORTADORA TC", "Helvetica-Bold", 16)
    centered_x = (width - text_width) / 2
    c.drawString(centered_x, height - 50, "TRANSPORTADORA TC")
    
    # Subtítulo centrado también
    c.setFont("Helvetica", 12)
    subtitle_width = c.stringWidth("Comprobante de Entrega", "Helvetica", 12)
    centered_subtitle_x = (width - subtitle_width) / 2
    c.drawString(centered_subtitle_x, height - 70, "Comprobante de Entrega")
    
    # Información del despacho
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin_horizontal, height - 120, "Información del Despacho:")
    c.setFont("Helvetica", 12)
    
    info_y = height - 140
    c.drawString(margin_horizontal, info_y, f"Cliente: {despacho.cliente.nombre}")
    c.drawString(margin_horizontal, info_y - 20, f"Número de Guía: {despacho.guia}")
    if despacho.observaciones:
        observaciones = despacho.observaciones[:100] + "..." if len(despacho.observaciones) > 100 else despacho.observaciones
        c.drawString(margin_horizontal, info_y - 60, f"Observaciones: {observaciones}")
    
    # Tabla de items
    items = despacho.items.all()
    data = [["Producto", "Cantidad"]]
    
    for item in items:
        data.append([item.inventario.producto.nombre, str(item.cantidad)])
    
    # Ancho de la tabla (ancho total menos márgenes izquierdo y derecho)
    table_width = width - (2 * margin_horizontal)
    
    # Ajustamos la altura de la tabla según la cantidad de items
    table_height = len(items) * 20
    table_y_position = info_y - 120 - table_height if (info_y - 120 - table_height) > 200 else 200
    
    # Creamos la tabla con márgenes simétricos
    table = Table(data, colWidths=[table_width * 0.8, table_width * 0.2])  # 80% para producto, 20% para cantidad
    
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4F81BD")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#DCE6F1")),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#4F81BD")),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    table.wrapOn(c, table_width, height)
    table.drawOn(c, margin_horizontal, table_y_position)  # Usamos el mismo margen izquierdo aquí
    
    # Sección de firma
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin_horizontal, 180, "Recibí conforme:")
    
    c.setFont("Helvetica", 12)
    c.drawString(margin_horizontal, 150, "Nombre: _________________________________________________")
    c.drawString(margin_horizontal, 120, "Cédula: __________________________________________________")
    c.drawString(margin_horizontal, 90, "Firma: ___________________________________________________")
    
    # Pie de página
    c.setFont("Helvetica", 8)
    c.drawString(margin_horizontal, 50, "Transportadora TC - Todos los derechos reservados")    
    c.save()
    buffer.seek(0)
    return buffer


def generate_cuenta_cobro_pdf(despacho):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Configuración inicial
    width, height = letter
    styles = getSampleStyleSheet()
    
    # Margen horizontal simétrico
    margin_horizontal = 50
    
    # Logo de la empresa
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo.png')
    if os.path.exists(logo_path):
        c.drawImage(logo_path, margin_horizontal, height - 100, width=100, height=80, preserveAspectRatio=True)
    
    # Encabezado - Nombre de la empresa CENTRADO
    c.setFont("Helvetica-Bold", 16)
    text_width = c.stringWidth("TRANSPORTADORA TC", "Helvetica-Bold", 16)
    centered_x = (width - text_width) / 2
    c.drawString(centered_x, height - 50, "TRANSPORTADORA TC")
    
    # Subtítulo centrado
    c.setFont("Helvetica-Bold", 14)
    subtitle = "CUENTA DE COBRO No. {}".format(despacho.guia)
    subtitle_width = c.stringWidth(subtitle, "Helvetica-Bold", 14)
    centered_subtitle_x = (width - subtitle_width) / 2
    c.drawString(centered_subtitle_x, height - 80, subtitle)
    
    # Información del cliente y despacho
    c.setFont("Helvetica", 10)
    c.drawString(margin_horizontal, height - 120, f"Cliente: {despacho.cliente.nombre}")
    c.drawString(margin_horizontal, height - 140, f"N° Guía: {despacho.guia}")
    
    # Tabla de items con valores
    items = despacho.items.all()
    data = [["Producto", "Cantidad", "Valor Unitario", "Valor Total"]]
    
    # Calcular totales
    subtotal = 0
    for item in items:
        valor_total = item.cantidad * item.valor_unitario
        data.append([
            item.inventario.producto.nombre,
            str(item.cantidad),
            "${:,.2f}".format(item.valor_unitario),
            "${:,.2f}".format(valor_total)
        ])
        subtotal += valor_total
    
    # Añadir fila de subtotal
    data.append(["SUBTOTAL", "", "", "${:,.2f}".format(subtotal)])
    
    # Añadir fila de flete
    flete = despacho.valor_flete if despacho.valor_flete else 0
    data.append(["FLETE", "", "", "${:,.2f}".format(flete)])
    
    # Añadir fila de TOTAL
    total = subtotal + flete
    data.append([
        "TOTAL A PAGAR", 
        "", 
        "", 
        Paragraph("<b>${:,.2f}</b>".format(total), styles['Normal'])
    ])
    
    # Configuración de la tabla
    table_width = width - (2 * margin_horizontal)
    table = Table(data, colWidths=[
        table_width * 0.5,    # Producto
        table_width * 0.15,   # Cantidad
        table_width * 0.15,   # Valor Unitario
        table_width * 0.2     # Valor Total
    ])
    
    # Estilo de la tabla
    table.setStyle(TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4F81BD")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Alinear nombres de productos a la izquierda
        ('ALIGN', (3, 1), (3, -1), 'RIGHT'), # Alinear valores a la derecha
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        
        # Filas de datos
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor("#DCE6F1")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#4F81BD")),
        
        # Totales
        ('LINEABOVE', (0, -3), (-1, -3), 1, colors.black),
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.black),
        ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -3), (-1, -1), colors.HexColor("#F2F2F2")),
    ]))
    
    # Posicionar tabla
    table.wrapOn(c, table_width, height)
    table.drawOn(c, margin_horizontal, height - 300)
    
    # Observaciones
    c.setFont("Helvetica", 10)
    if despacho.observaciones:
        observaciones = "Observaciones: " + despacho.observaciones
        observaciones = observaciones[:120] + "..." if len(observaciones) > 120 else observaciones
        c.drawString(margin_horizontal, height - 320, observaciones)
    
    # Firma
    c.setFont("Helvetica-Bold", 10)
    c.drawString(width - margin_horizontal - 200, 150, "RECIBIDO POR:")
    c.setFont("Helvetica", 10)
    c.drawString(width - margin_horizontal - 200, 130, "Nombre: _________________________")
    c.drawString(width - margin_horizontal - 200, 110, "Cédula: _________________________")
    c.drawString(width - margin_horizontal - 200, 90, "Firma: _________________________")
    
    # Pie de página
    c.setFont("Helvetica", 8)
    c.drawString(margin_horizontal, 50, "Transportadora TC - Todos los derechos reservados")
    
    c.save()
    buffer.seek(0)
    return buffer   