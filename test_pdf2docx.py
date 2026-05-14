from pdf2docx import Converter

pdf_file = "C:/Users/Admin/Desktop/HAJTEJ-20260514_092000.pdf"
docx_file = "C:/Users/Admin/Desktop/HAJTEJ-20260514_092000.docx"

cv = Converter(pdf_file)
cv.convert(docx_file)
cv.close()