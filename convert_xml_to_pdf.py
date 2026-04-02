import os
import xml.etree.ElementTree as ET
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak

def create_pdf_from_xml(xml_path, output_pdf):
    if not os.path.exists(xml_path):
        print(f"File not found: {xml_path}")
        return

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing XML: {e}")
        return

    # PDF Document Settings
    doc = SimpleDocTemplate(output_pdf, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = styles['Title'].clone('title_style')
    title_style.fontSize = 24
    title_style.textColor = colors.HexColor("#2C3E50")
    title_style.alignment = 1 # Center

    header_style = styles['Heading2'].clone('header_style')
    header_style.fontSize = 18
    header_style.textColor = colors.HexColor("#2980B9")
    header_style.spaceAfter = 10
    
    product_name_style = styles['Heading3'].clone('pname')
    product_name_style.fontSize = 14
    product_name_style.textColor = colors.darkblue
    
    body_style = styles['Normal'].clone('body')
    body_style.fontSize = 10
    body_style.leading = 14

    elements = []

    # 1. Page Header (Store Info)
    store_name = root.findtext('name', "Store Catalog")
    location = root.findtext('location', "")
    phone = root.findtext('.//phone', "")
    email = root.findtext('.//email', "")

    elements.append(Paragraph(store_name, title_style))
    elements.append(Paragraph(f"<b>Location:</b> {location}", body_style))
    elements.append(Paragraph(f"<b>Contact:</b> {phone} | {email}", body_style))
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("--- PRODUCT CATALOG ---", header_style))
    elements.append(Spacer(1, 15))

    # 2. Iterate Products
    products = root.findall('.//product')
    for p in products:
        p_name = p.findtext('name', 'Product')
        p_id = p.findtext('id', 'N/A')
        p_price = p.find('price').text if p.find('price') is not None else "0.00"
        p_curr = p.find('price').get('currency') if p.find('price') is not None else "USD"
        p_rating = p.findtext('.//average', "0")
        p_reviews = p.findtext('.//totalReviews', "0")
        p_stock = "Yes" if p.findtext('inStock', "false") == "true" else "No"

        # Product Header Table
        p_header_data = [
            [Paragraph(f"<b>{p_name}</b> (ID: {p_id})", product_name_style), ""],
            [f"Price: {p_price} {p_curr}", f"In Stock: {p_stock}"],
            [f"Rating: {p_rating}/5.0 ({p_reviews} reviews)", ""]
        ]
        
        t_header = Table(p_header_data, colWidths=[350, 150])
        t_header.setStyle(TableStyle([
            ('SPAN', (0, 0), (1, 0)),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TEXTCOLOR', (0,1), (0,1), colors.darkgreen),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica-Bold'),
        ]))
        elements.append(t_header)

        # Details
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("<b>Specifications:</b>", body_style))
        
        details = p.find('details')
        if details is not None:
            dim = details.find('dimensions')
            d_str = f"Dimensions: {dim.findtext('length', '-')} x {dim.findtext('width', '-')} x {dim.findtext('height', '-')}" if dim is not None else "N/A"
            weight = details.findtext('weight', 'N/A')
            elements.append(Paragraph(f"• {d_str} | Weight: {weight}", body_style))
            
            features = [f.text for f in details.findall('.//feature')]
            if features:
                elements.append(Paragraph(f"• <b>Features:</b> {', '.join(features)}", body_style))

        # Variants
        variants = p.findall('.//variant')
        if variants:
            v_items = [f"{v.findtext('color', '')} @ {v.findtext('price', '')} {p_curr}" for v in variants]
            elements.append(Paragraph(f"• <b>Variants:</b> {', '.join(v_items)}", body_style))

        # Shipping
        shipping = p.find('shipping')
        if shipping is not None:
            std = shipping.find('standard')
            exp = shipping.find('express')
            ship_text = f"<b>Standard:</b> {std.findtext('cost', '0')} ({std.findtext('deliveryTime', '')}) | " \
                        f"<b>Express:</b> {exp.findtext('cost', '0')} ({exp.findtext('deliveryTime', '')})"
            elements.append(Paragraph(f"• <b>Shipping:</b> {ship_text}", body_style))

        elements.append(Spacer(1, 20))
        elements.append(Table([['']], colWidths=[500], rowHeights=[1], style=TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.lightgrey)]))) # Divider line
        elements.append(Spacer(1, 20))

    # Build the PDF
    doc.build(elements)
    print(f"Product created: {output_pdf}")

def process_directory(input_dir, output_dir):
    # Tạo thư mục output nếu chưa có
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        except Exception as e:
            print(f"Error creating output directory: {e}")
            return

    if not os.path.exists(input_dir):
        print(f"Input directory not found: {input_dir}")
        return

    # Quét tất cả file .xml trong thư mục input
    xml_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.xml')]
    
    if not xml_files:
        print(f"No XML files found in '{input_dir}'")
        return

    print(f"Found {len(xml_files)} file(s). Starting conversion...")

    for filename in xml_files:
        xml_path = os.path.join(input_dir, filename)
        # Tên file PDF giống tên file XML
        pdf_name = os.path.splitext(filename)[0] + ".pdf"
        pdf_path = os.path.join(output_dir, pdf_name)
        
        print(f"Converting: {filename} -> {pdf_name}")
        create_pdf_from_xml(xml_path, pdf_path)

if __name__ == "__main__":
    # Cài đặt thư mục làm việc của bạn ở đây
    # Ở đây tôi mặc định tạo folder 'input' và 'output' ngay trong dự án
    CURRENT_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
    INPUT_FOLDER = os.path.join(CURRENT_PROJECT_DIR, 'input')
    OUTPUT_FOLDER = os.path.join(CURRENT_PROJECT_DIR, 'output')

    print(f"--- Batch PDF Converter ---")
    print(f"Input: {INPUT_FOLDER}")
    print(f"Output: {OUTPUT_FOLDER}")
    
    process_directory(INPUT_FOLDER, OUTPUT_FOLDER)
