from io import BytesIO
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

reader = PdfReader("pdfs/Empty.pdf")
first_page = reader.pages[0]
page_width = float(first_page.mediabox.width)
page_height = float(first_page.mediabox.height)

buffer = BytesIO()
c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
c.setFont("Helvetica", 36)
c.setFillColorRGB(0.8, 0, 0)
c.drawString(100, page_height - 100, "Test")
c.save()
buffer.seek(0)

overlay_reader = PdfReader(buffer)
writer = PdfWriter(clone_from=reader)

writer.pages[0].merge_page(overlay_reader.pages[0])

for page in reader.pages[1:]:
    writer.add_page(page)

with open("pdfs/output_stamped.pdf", "wb") as f:
    writer.write(f)

print("Done.")