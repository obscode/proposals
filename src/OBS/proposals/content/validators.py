from zope.interface import Invalid
from plone import api
from PyPDF2 import PdfReader
from io import BytesIO,StringIO
from .utils import parse_ra,parse_dec,parse_csv
import csv
from astropy.time import Time


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

   if data.targets is not None and len(data.targets) > 0:
      # Make sure at least RA/DEC are set and JD's are consistent
      for ir,row in enumerate(data.targets):
         if row['ra1'] is None:
            valid = False
            messages.append(f"Target {ir+1} must have RA set in the target list")
         else:
            ra1 = parse_ra(row['ra1'])
            if ra1 is None:
               valid = False
               messages.append(f"RA value for target {ir+1} ({row['ra1']}) is not valid")
         if row['ra2'] is not None:
            ra2 = parse_ra(row['ra2'])
            if ra2 is None:
               valid = False
               messages.append(f"RA value for target {ir+1} ({row['ra2']}) is not valid")
         if row['dec1'] is None:
            valid = False
            messages.append(f"Target {ir+1} must have DEC set in the target list")
         else:
            dec1 = parse_dec(row['dec1'])
            if dec1 is None:
               valid = False
               messages.append(f"DEC value for target {ir+1} ({row['dec1']}) is not valid")
         if row['dec2'] is not None:
            dec2 = parse_dec(row['dec2'])
            if dec2 is None:
               valid = False
               messages.append(f"DEC value for target {ir+1} ({row['dec2']}) is not valid")
         # Make sure that JDstart <= JDend
         if row['epoch'] is not None:
            try:
               jd1 = float(row['epoch'])
            except:
               valid = False
               messages.append(f"JD start for target {ir+1} must be valid number")
         else:
            jd1 = None
         if row['epoch2'] is not None:
               try:
                  jd2 = float(row['epoch2'])
               except:
                  valid = False
                  messages.append(f"JD end for target {ir+1} must be valid number")
         else:
            jd2 = None
         if jd1 is not None and jd2 is not None and jd1 > jd2:
            valid = False
            messages.append(f"JD start must be before JD end for target {ir+1}")

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

def validate_JD(value):
   '''Check this is a reasonable JD'''
   try:
      val = float(value)
   except:
      raise Invalid(f"JD {value} is not a valid number")

   JDnow = Time.now().jd
   if val < JDnow:
      raise Invalid(f"JD {value} is in the past")
   if val > JDnow + 365.0*2:
      raise Invalid(f"JD {value} is more than 2 years in the future")
   return True



   
