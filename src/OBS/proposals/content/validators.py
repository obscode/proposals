from zope.interface import Invalid
from PyPDF2 import PdfReader
from io import BytesIO,StringIO
import csv


def validate_PDF(value):
   '''Check that the content is a propoer PDF'''
   if value is None:
      return True

   try:
      pdf = value.open()
      reader = PdfReader(pdf)
      pdf.close()
      return True
   except:
      raise Invalid("File is not a valid PDF")
   return True

def validate_CSV(value):
   '''Check that the content is a CSV file and we need
   to make sure the header has RA and DEC'''
   if value is None:
      return True
   
   try:
      # CSV are string objects, but NamedFileBlobs store in bytes
      strdata = value.data.decode('utf-8')
      fileobj = StringIO(strdata)
      reader = csv.reader(fileobj)
   except:
      fileobj.close()
      raise Invalid("File is not a valid CSV file")

   header = next(reader)
   fileobj.close()
   fields = [field.lower() for field in header]
   if 'ra' not in fields or 'dec' not in fields:
      raise Invalid("Target lists need RA and DEC fields")
   
   return True

def validate_PDF_or_CSV(value):
   '''Check if PDF or CSV'''
   try:
      validate_PDF(value)
   except Invalid:
      validate_CSV(value)
   return True

         
def validate_PDF_SJ(value):
   # First make sure it's a PDF
   if value is None: return True
   maxpages = 5

   try:
      pdf = value.open()
      reader = PdfReader(pdf)

   except:
      pdf.close()
      raise Invalid("File is not a valid PDF")
   npages = len(reader.pages)
   pdf.close()
   if npages > maxpages:
      raise Invalid(f"PDF exceeds {maxpages} pages")
   return True


def validate_PDF_PD(value):
   # First make sure it's a PDF
   if value is None: return True
   maxpages = 1

   try:
      pdf = value.open()
      reader = PdfReader(pdf)

   except:
      pdf.close()
      raise Invalid("File is not a valid PDF")
   npages = len(reader.pages)
   pdf.close()
   if npages > maxpages:
      raise Invalid(f"PDF exceeds {maxpages} pages")
   return True




   
