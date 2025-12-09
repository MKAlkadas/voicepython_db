from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# لتحويل وعرض العربي بشكل صحيح
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except ImportError:
    raise ImportError("Please install dependencies: pip install arabic-reshaper python-bidi")

def reshape_ar(text: str) -> str:
    """Re-shape and bidi-fix Arabic text for ReportLab Paragraph."""
    if not text:
        return ""
    try:
        reshaped = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped)
        return bidi_text
    except Exception:
        # إذا حدث خطأ في المكتبات، ارجع النص كما هو (أفضل من توقف كامل)
        return text

class PDFGenerator:
    def __init__(self, output_dir="temp", font_path="fonts/Amiri-Regular.ttf", font_name="ArabicFont"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        self.font_path = font_path
        self.font_name = font_name

        # تأكد من وجود ملف الخط
        if not os.path.isfile(self.font_path):
            raise FileNotFoundError(f"Arabic font file not found: {self.font_path}\n"
                                    "Place a TTF Arabic font (e.g., Amiri-Regular.ttf) next to the script or provide full path.")

        # تسجيل الخط
        try:
            pdfmetrics.registerFont(TTFont(self.font_name, self.font_path))
        except Exception as e:
            raise RuntimeError(f"Failed to register font {self.font_path}: {e}")

    def generate_quote(self, data: dict, filename="quote.pdf"):
        filepath = os.path.join(self.output_dir, filename)
        doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        elements = []

        styles = getSampleStyleSheet()

        # أنماط عربية تستخدم الخط المسجل
        arabic_style = ParagraphStyle(
            name="Arabic",
            parent=styles["Normal"],
            fontName=self.font_name,
            fontSize=12,
            leading=14,
            alignment=2,  # right alignment
        )

        title_style = ParagraphStyle(
            name="TitleArabic",
            parent=styles["Heading1"],
            fontName=self.font_name,
            fontSize=18,
            leading=22,
            alignment=2,
        )

        # عنوان (مع إعادة تشكيل اللغة العربية)
        title_text = "عرض سعر / Price Quote"
        # اجعل الجزء العربي ظاهرًا بشكل صحيح
        title_ar = "عرض سعر"
        elements.append(Paragraph(reshape_ar(title_ar) + " / Price Quote", title_style))
        elements.append(Spacer(1, 12))

        # معلومات العميل
        customer_id = data.get('customer_id', 'Unknown')
        elements.append(Paragraph(reshape_ar(f"رقم العميل: {customer_id}"), arabic_style))
        elements.append(Spacer(1, 10))

        # إعداد بيانات الجدول
        # Headers: Item, Qty, Price, Total, Specs
        headers = [
            Paragraph(reshape_ar("المواصفات"), arabic_style),
            Paragraph(reshape_ar("الإجمالي"), arabic_style),
            Paragraph(reshape_ar("السعر"), arabic_style),
            Paragraph(reshape_ar("الكمية"), arabic_style),
            Paragraph(reshape_ar("اسم المنتج"), arabic_style)
        ]
        
        table_data = [headers]
        
        items = data.get('items', [])
        # Handle legacy format if items is missing (fallback)
        if not items and 'product_name' in data:
             items = [{
                 'product_name': data.get('product_name'),
                 'quantity': data.get('quantity'),
                 'price': 0,
                 'total': 0,
                 'specs': data.get('specs')
             }]

        grand_total = 0
        
        for item in items:
            name = str(item.get('product_name', 'N/A'))
            qty = str(item.get('quantity', 0))
            price = f"{item.get('price', 0):.2f}"
            total = f"{item.get('total', 0):.2f}"
            specs = str(item.get('specs', ''))
            
            grand_total += item.get('total', 0)
            
            row = [
                Paragraph(reshape_ar(specs), arabic_style),
                Paragraph(total, arabic_style),
                Paragraph(price, arabic_style),
                Paragraph(qty, arabic_style),
                Paragraph(reshape_ar(name), arabic_style)
            ]
            table_data.append(row)

        # Add Grand Total Row
        table_data.append([
            Paragraph("", arabic_style),
            Paragraph(f"{grand_total:.2f}", arabic_style),
            Paragraph(reshape_ar("الإجمالي الكلي"), arabic_style),
            "",
            ""
        ])

        # Column widths (adjust as needed)
        # Specs, Total, Price, Qty, Name
        col_widths = [150, 70, 70, 50, 150]
        
        t = Table(table_data, colWidths=col_widths, hAlign='RIGHT')

        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            # Grand Total Row Style
            ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
            ('SPAN', (2, -1), (4, -1)), # Span "Grand Total" label
        ]))

        elements.append(t)
        elements.append(Spacer(1, 20))

        footer = "تم إنشاء المستند بواسطة النظام"
        elements.append(Paragraph(reshape_ar(footer), arabic_style))

        # بناء الملف
        try:
            doc.build(elements)
        except Exception as e:
            raise RuntimeError(f"Failed to build PDF: {e}")

        return filepath

# Example usage:
if __name__ == "__main__":
    data = {
        "customer_id": "CUST-001",
        "items": [
            {"product_name": "كمبيوتر محمول", "quantity": 2, "price": 4500, "total": 9000, "specs": "i7, 16GB"},
            {"product_name": "ماوس", "quantity": 5, "price": 50, "total": 250, "specs": "Wireless"}
        ]
    }

    gen = PDFGenerator(output_dir="temp", font_path="fonts/Amiri-Regular.ttf")
    # Ensure font exists or use default if testing locally without font
    try:
        out = gen.generate_quote(data, "quote_ar_multi.pdf")
        print("Created:", out)
    except Exception as e:
        print(e)
