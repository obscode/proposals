from zope.interface import Invalid
from plone import api
from PyPDF2 import PdfReader
from io import BytesIO,StringIO
from .utils import parse_ra,parse_dec,parse_csv
import csv


def extra_proposal_validation(data):
   '''Here is where to do multi-field validation if needed'''
   valid = True
   messages = []
   # This is in the original proposals site.
   if data.runs is not None:
      RUNS = api.portal.get_vocabulary(
         name='proposals.RUNS',
         context=data)
      RUNS = [item.value for item in RUNS]
      for ridx,run in enumerate(data.runs):
         if (run['inst1'].find('M2FS') >=0 or \
            (run['inst2'] and run['inst2'].find('M2FS') >= 0)) and run['service'].lower()=='yes':
            valid = False
            messages.append("One cannot request service observing with M2FS")
         # check that "preferred" is between begin and end. Note that we assume
         # the runs vocabulary is ordered by date!
         pref_idx = RUNS.index(run['preferred'])
         from_idx = RUNS.index(run['fromblock'])
         to_idx = RUNS.index(run['toblock'])
         if not from_idx <= to_idx:
            messages.append(f"The 'from' block for run {ridx+1} should not be after the"
                            " 'to' block.")
            valid = False
         if not from_idx <= pref_idx <= to_idx:
            messages.append(f"The 'preferred' block for run {ridx+1} should be "\
                            "between the 'from' and 'to' blocks.")
            valid = False

   if data.projects is not None and len(data.projects) > 1:
      priorities = set([proj['priority'] for proj in data.projects])
      if len(priorities) < len(data.projects):
         valid = False
         messages.append("Each project must have a different priority")

   return valid,"\n".join(messages)
   

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

   l,message = parse_csv(reader)
   fileobj.close()
   if l is None:
      raise Invalid(message)
   
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

def validate_PDF_TBD_SJ(value):
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


def validate_RA(value):
   '''Check that the RA is valid'''
   if value is None: return True
   ra = parse_ra(value)
   if ra is None:
      raise Invalid(f"RA {value} is not valid")
   return True

def validate_DEC(value):
   '''Check that the DEC is valid'''
   if value is None: return True
   dec = parse_dec(value)
   if dec is None:
      raise Invalid(f"DEC {value} is not valid")
   return True

   
