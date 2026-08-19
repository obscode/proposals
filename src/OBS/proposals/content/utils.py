'''Some utilities for dealing with data.'''

from csv import reader
import re
from math import floor
import tempfile
import os
import subprocess

# Regular expressions for coordinates
float_pat = re.compile(r'^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$')
hms_pat = re.compile(r'^([01]\d|2[0-3])\s*[h:]?\s*([0-5]\d)\s*[m:]?\s*([0-5\
]\d(?:\.\d+)?)\s*[s]?$')
dms_pat = re.compile(r'''^([+\-])?(\d{1,2})[d\u00b0: ](\d{1,2})['m: ](\d{1,2}(?:\.(?:\d+)?)?)(?:['"s])?$''')

def dec2hms(val):
   '''convert decimal degrees to H:M:S format consistently'''
   val = val / 15
   h = int(floor(val))
   val = (val - h)*60
   m = int(floor(val))
   val = (val - m)*60
   return f"{h:02d}:{m:02d}:{val:5.2f}"

def dec2dms(val):
   '''convert decimal degrees to H:M:S format consistently'''
   neg = val < 0
   val = abs(val)
   d = int(floor(val))
   val = (val - d)*60
   m = int(floor(val))
   val = (val - m)*60
   pref = ["+","-"][neg]
   return pref+f"{d:02d}:{m:02d}:{val:5.2f}"

def parse_ra(rastr):
   '''Figure out RA and convert to decimal degrees'''
   res = float_pat.match(rastr)
   if res:  return float(res.group(0))

   res = hms_pat.match(rastr)
   if res:
      h,m,s = res.groups()
      return 15*(int(h)+float(m)/60+float(s)/3600)
   return None

def parse_dec(destr):
   '''Figure out RA and convert to decimal degrees'''
   res = float_pat.match(destr)
   if res:  return float(res.group(0))

   res = dms_pat.match(destr)
   if res:
      pm,d,m,s = res.groups()
      negative = pm == '-'
      degs = int(d) + float(m)/60.0 + float(s)/3600.0
      if negative:  degs = -degs
      return degs
   return None
   

def parse_csv(reader, str_output=True):
   '''Given an open csv.reader object, parse the lines into a standard format.
   If str_output = False, return numerical values for RA/DEC/epoch instead of
   formatted strings.'''   
   data = []
   header = next(reader)
   extras = []    # extra columns we'll keep
   raidx = None   # RA index
   deidx = None   # DEC index 
   fidx = None    # field index
   midx = None   # magnitude index
   eidx = None    # epoch index
   for i,field in enumerate(header):
      field = field.lower()
      if field in ['dec','declination','delta','de']:
         deidx = i
         continue
      elif field in ['ra','alpha','right ascension']:
         raidx = i
         continue
      elif field in ['field','obj','object','region','name','object name']:
         fidx = i
         continue
      elif field in ['epoch','date','date-obs']:
         eidx = i
         continue
      elif field in ['mag','magnitude']:
         midx = i
         continue
      else:
         extras.append(i)
      
      # Bare minimum:  RA's and DEC's
   if raidx is None or deidx is None: 
      #print('error:  no RA and/or DEC')
      return None, "Error:  no RA and/or DEC found"
   data.append([])
   if fidx is not None:  data[-1].append('field')
   data[-1].append('RA')
   data[-1].append('DEC')
   if midx is not None:  data[-1].append('Mag')
   if eidx is not None:  data[-1].append('Epoch')
   for idx in extras: data[-1].append(header[idx])

   # Now for the data
   for row in reader:
      data.append([])
      if fidx is not None: data[-1].append(row[fidx])
      # RA
      ra = parse_ra(row[raidx])
      if ra is None:  
         #print("failed to parse:",row[raidx])
         return None, "Error:  failed to parse {}".format(row[raidx])

      if str_output: ra = dec2hms(ra)
      data[-1].append(ra)
      dec = parse_dec(row[deidx])
      if dec is None:  
         #print("failed to parse:",row[deidx])
         return None, "Error:  failed to parse {}".format(row[deidx])
      if str_output: dec = dec2dms(dec)
      data[-1].append(dec)
      if midx is not None: data[-1].append(row[midx])
      if eidx is not None: 
         if str_output:
            epoch = row[eidx]
         else:
            try:
               epoch = float(row[eidx])
            except:
               print("float didn't float:", row[eidx])
               return None, "Error:  failed to parse {}".format(row[eidx])
         data[-1].append(epoch)
      for idx in extras: data[-1].append(row[idx])
   return data, "Success"
   
def pdf2ascii(pdf):
   '''Given PDF content as a bytes(), try to convert it to ascii'''

   cmd = ["/usr/bin/ps2ascii"]
   result = subprocess.run(cmd, input=pdf, capture_output=True)
   text = result.stdout
   # Get rid of carriage returns
   text = text.replace(b'\r',b'')
   return text

    

   


