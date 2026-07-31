from io import BytesIO as StringIO
from PyPDF2 import PdfReader, PdfWriter

from reportlab.platypus import PageTemplate, BaseDocTemplate, SimpleDocTemplate
from reportlab.platypus import Frame, Paragraph, Table, TableStyle, Preformatted
from reportlab.platypus.flowables import PageBreak
from reportlab.pdfgen import canvas
from reportlab.lib import styles
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import *
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.rl_config import defaultPageSize
from copy import deepcopy
import os

def generate_pdf(self):
   "Generate the cover page and append the PDFs"
#   try:
   name = self.pi_name
   fn = name.split()[0][0].lower()
   ln = name.split()[-1].lower()
   filename = "%s_%s_%s.pdf" % (ln,fn,self.semester)
   
   report = StringIO()
   cover = SimpleDocTemplate(report,pagesize=letter,leftMargin=0.5*inch,rightMargin=0.5*inch)
   style = styles.getSampleStyleSheet()
   items = [ ]
   
   fontSize = 9
   kstyle = ParagraphStyle( name='Key', fontName='Times-Bold', fontSize=fontSize, leading=fontSize/2.)
   istyle = ParagraphStyle( name='Item', fontName='Courier', fontSize=fontSize, leading=fontSize/2.)
   
   infoPI = [
      ("Semester",self.semester),
      ("Investigator",self.pi_name),
      ("Department",self.department),
      ("Email",self.email),
      ("Telephone",self.telephone),
      ]
   
   elements = [ [Paragraph(key+":",kstyle), Paragraph(info,istyle)] for key,info in infoPI]
   itemPI = Table(elements)
   itemPI.setStyle(TableStyle([
      ('BOX',(0,0),(1,4),0.25,colors.black,),
      ('BOTTOMPADDING',(0,4),(1,4),fontSize/1.,),
      ]))
   itemPI._argW[0] = 1.2*inch
   itemPI._argW[1] = 2.8*inch
   itemPI.hAlign = "LEFT"
   items.append( itemPI)
   
   getkey = lambda dict,key: (key in dict and str(dict[key])) or ("")
   
   kstyle = ParagraphStyle( name='Key', fontName='Times-Bold', fontSize=fontSize, leading=fontSize)
   istyle = ParagraphStyle( name='Item', fontName='Courier', fontSize=fontSize, leading=fontSize)
   
   projects = self.projects if self.projects is not None else []
   for jp,project in enumerate(projects):
      if project:
         elements = [
                  [Paragraph("Project No. %d:" % (jp+1),kstyle), Paragraph(project["proj_title"],istyle)],
                  [Paragraph("Priority:",kstyle), Paragraph(project["priority"],istyle)],
                  [Paragraph("Co-Investigators:",kstyle), Paragraph(("coIs" in project and project["coIs"]) or "None",istyle)],
                  ]
         itemProject = Table(elements)
         itemProject.spaceBefore = 1.0*fontSize
         itemProject.setStyle(TableStyle([
            ('BOTTOMPADDING',(0,2),(1,2),fontSize/1.,),
            ('VALIGN',(0,0),(-1,-1),'TOP',),
            ]))
         itemProject._argW[0] = 1.2*inch
         itemProject._argW[1] = 5.3*inch
         itemProject.hAlign = "LEFT"
   
         itemRunsHeader = Paragraph("Observing Runs:",kstyle)
         itemRunsHeader.spaceBefore = 1*fontSize
   
         runTitles = "Run","Blocks","Nights","Max Moon","Telescope","Instr. One","Instr. Two","Service","In Person","Observers"
         runKeys = "run","nights","moon","telescope","inst1","inst2","service","in_person","observers"
         runSizes = (4,8,5,5,7,7,7,6,7,16)
   
         runs = self.runs if self.runs is not None else []
         jruns = [jrun for jrun,run in enumerate(runs) if 'project' in run and run['project'] == str(jp+1)]
         runscopy = deepcopy([run for run in runs if 'project' in run and run['project'] == str(jp+1)])
         if jruns:
            for runcopy in runscopy:
               if "service" in runcopy:
                  #runcopy["service"] = runcopy["service"].split(":")[1]
                  runcopy["service"] = runcopy["service"]
               if "in_person" in runcopy:
                  runcopy["in_person"] = runcopy["in_person"]
               if "inst1" in runcopy:
                  runcopy["inst1"] = " ".join(runcopy["inst1"].split(":")[1:])
                  runcopy["inst1"] = runcopy["inst1"].replace("&","&amp;")
                  if "inst2" in runcopy and runcopy["inst2"]:
                     runcopy["inst2"] = " ".join(runcopy["inst2"].split(":")[1:])
                     runcopy["inst2"] = runcopy["inst2"].replace("&","&amp;")
                  else:
                     runcopy["inst2"] = ""
               if "preferred" in runcopy:
                  if "fromblock" in runcopy:
                     if "toblock" in runcopy:
                       runcopy["run"] = "%s (%s-%s)" % \
                        (runcopy["preferred"], runcopy["fromblock"], runcopy["toblock"],)
                     else:
                       runcopy["run"] = "%s (%s-%s)" % \
                        (runcopy["preferred"], runcopy["fromblock"], "")
               
   
            elements = [ [ Paragraph(title,kstyle) for title in runTitles]]
            elements += [ [Paragraph("%d" % (jrun+1),istyle)]+ [Paragraph(getkey(run,key),istyle) for key in runKeys] \
                        for telescope in ["Baade","Clay","Clay-f5","Clay-AO","duPont","Swope"] \
                        for jrun,run in enumerate(runscopy) if run['telescope'] == telescope]
            itemRuns = Table(elements)
            itemRuns.setStyle(TableStyle([
                  ('GRID',(0,0),(-1,-1),0.25,colors.black,),
                  ('BOX',(0,0),(-1,-1),0.25,colors.black,),
                  ('LINEABOVE',(0,0),(-1,-1),0.25,colors.black,),
                  ('LINEBELOW',(0,0),(-1,-1),0.25,colors.black,),
                  ('RIGHTPADDING',(0,0),(-1,-1),0,),
                  ('VALIGN',(0,0),(-1,-1),'TOP',),
                  ]))
            for j in range(len(runSizes)):
               itemRuns._argW[j] = runSizes[j]*0.1*inch
            itemRuns.hAlign = "LEFT"
            itemRuns.spaceBefore = 0.5*fontSize
   
         if self.too:
            jtoos = [jtoo for jtoo,too in enumerate(self.too) if 'project' in too and too['project'] == str(jp+1)]
            toos = [too for jtoo,too in enumerate(self.too) if 'project' in too and too['project'] == str(jp+1)]
            #print('********',toos)
   
            if toos:
               itemTOOHeader = Paragraph("Target of Opportunity Requests:",kstyle)
               itemTOOHeader.spaceBefore = 1*fontSize
   
               elements = [ [Paragraph("No.",kstyle), Paragraph("Hours",kstyle), Paragraph("Telescope(s)",kstyle)] ]
               elements += [[Paragraph("%d" % (j+1),istyle), Paragraph(getkey(too,"hours"),istyle), Paragraph(getkey(too,"telescopes"),istyle)] for j,too in zip(jtoos,toos)]
               itemTOO = Table(elements)
               itemTOO.setStyle(TableStyle([
                      ('GRID',(0,0),(-1,-1),0.25,colors.black,),
                      ('BOX',(0,0),(-1,-1),0.25,colors.black,),
                      ('LINEABOVE',(0,0),(-1,-1),0.25,colors.black,),
                      ('LINEBELOW',(0,0),(-1,-1),0.25,colors.black,),
                      ('RIGHTPADDING',(0,0),(-1,-1),0,),
                      ('VALIGN',(0,0),(-1,-1),'TOP',),
                      ]))
               itemTOO._argW[0] = 0.1*inch * 5
               itemTOO._argW[1] = 0.1*inch * 10
               itemTOO._argW[2] = 0.1*inch * 30
               itemTOO.hAlign = "LEFT"
               itemTOO.spaceBefore = 0.5*fontSize
            else:
               itemTOO = Paragraph("None",istyle)
               itemTOO.spaceBefore = 0.5*fontSize
   
         elements = [[itemProject],]
         if self.runs and jruns: elements += [[itemRunsHeader], [itemRuns],]
         if self.too and jtoos: elements +=  [ [itemTOOHeader], [itemTOO],]
         itemRunsTable = Table(elements)
         itemRunsTable.setStyle(TableStyle([
               ('BOX',(0,0),(-1,-1),0.25,colors.black,),
               ('VALIGN',(0,0),(-1,-1),'TOP',),
               ]))
         itemRunsTable.spaceBefore = 1.0*fontSize
         itemRunsTable.hAlign = "LEFT"
         items.append( itemRunsTable)
   
   itemConflicts = Paragraph("Conflicts:",kstyle)
   itemConflicts.spaceBefore = 2*fontSize
   items.append( itemConflicts)
   
   if self.conflicts:
      itemConflicts = Paragraph(str(self.conflicts),istyle)
      itemConflicts.spaceBefore = 0.5*fontSize
      items.append( itemConflicts)
   else:
      itemConflicts = Paragraph("None",istyle)
      itemConflicts.spaceBefore = 0.5*fontSize
      items.append( itemConflicts)
   
   itemRequire = Paragraph("Special or Additional Requirements:",kstyle)
   itemRequire.spaceBefore = 2*fontSize
   items.append( itemRequire)
   
   if self.requirements:
      itemRequire = Paragraph(str(self.requirements),istyle)
      itemRequire.spaceBefore = 0.5*fontSize
      items.append( itemRequire)
   else:
      itemRequire = Paragraph("None",istyle)
      itemRequire.spaceBefore = 0.5*fontSize
      items.append( itemRequire)
   
   items.append( PageBreak())
   
   cover.build(items)
   
   pdfCover = PdfReader(report)
   output = PdfWriter()
   #numPages = pdfCover.getNumPages()
   numPages = len(pdfCover.pages)
   [output.add_page(pdfCover.pages[j]) for j in range(numPages)]
   
   if self.abstract is not None:
      abs = self.abstract.data
      pdfStream = StringIO(abs)
      pdfReader = PdfReader(pdfStream)
      numPages = len(pdfReader.pages)
      [output.add_page(pdfReader.pages[j]) for j in range(numPages)]
   
   if self.target_list is not None:
      targ = self.target_list.data
      pdfStream = StringIO(targ)
      pdfReader = PdfReader(pdfStream)
      numPages = len(pdfReader.pages)
      [output.add_page(pdfReader.pages[j]) for j in range(numPages)]
   
   if self.justification is not None:
      just = self.justification.data
      pdfStream = StringIO(just)
      pdfReader = PdfReader(pdfStream)
      numPages = len(pdfReader.pages)
      [output.add_page(pdfReader.pages[j]) for j in range(numPages)]
   

   if self.progress_to_date is not None:
      prog = self.progress_to_date.data
      pdfStream = StringIO(prog)
      pdfReader = PdfReader(pdfStream)
      numPages = len(pdfReader.pages)
      [output.add_page(pdfReader.pages[j]) for j in range(numPages)]
   
   proposal = StringIO()
   output.write(proposal)
   result = proposal.getvalue()
   
   return result


def TBDgenerate_pdf(self):
   "Generate the cover page and append the PDFs for a TBD Proposal (simpler than"
   "regular proposals)"
#   try:
   name = self.pi_name
   fn = name.split()[0][0].lower()
   ln = name.split()[-1].lower()
   filename = "%s_%s_%s.pdf" % (ln,fn,self.semester)
   
   report = StringIO()
   cover = SimpleDocTemplate(report,pagesize=letter,leftMargin=0.5*inch,rightMargin=0.5*inch)
   style = styles.getSampleStyleSheet()
   items = [ ]
   
   fontSize = 9
   kstyle = ParagraphStyle( name='Key', fontName='Times-Bold', fontSize=fontSize, leading=fontSize/2.)
   istyle = ParagraphStyle( name='Item', fontName='Courier', fontSize=fontSize, leading=fontSize/2.)
   
   infoPI = [
      ("Semester",self.semester),
      ("Investigator",self.pi_name),
      ("Department",self.department),
      ("Email",self.email),
      ("Telephone",self.telephone),
      ]
   
   elements = [ [Paragraph(key+":",kstyle), Paragraph(info,istyle)] for key,info in infoPI]
   itemPI = Table(elements)
   itemPI.setStyle(TableStyle([
      ('BOX',(0,0),(1,4),0.25,colors.black,),
      ('BOTTOMPADDING',(0,4),(1,4),fontSize/1.,),
      ]))
   itemPI._argW[0] = 1.2*inch
   itemPI._argW[1] = 2.8*inch
   itemPI.hAlign = "LEFT"
   items.append( itemPI)
   
   getkey = lambda dict,key: (key in dict and str(dict[key])) or ("")
   
   kstyle = ParagraphStyle( name='Key', fontName='Times-Bold', fontSize=fontSize, leading=fontSize)
   istyle = ParagraphStyle( name='Item', fontName='Courier', fontSize=fontSize, leading=fontSize)
   
   projects = self.projects if self.projects is not None else []
   for jp,project in enumerate(projects):
      if project:
         elements = [
                  [Paragraph("Project No. %d:" % (jp+1),kstyle), Paragraph(project["proj_title"],istyle)],
                  [Paragraph("Priority:",kstyle), Paragraph(project["priority"],istyle)],
                  [Paragraph("Co-Investigators:",kstyle), Paragraph(("coIs" in project and project["coIs"]) or "None",istyle)],
                  ]
         itemProject = Table(elements)
         itemProject.spaceBefore = 1.0*fontSize
         itemProject.setStyle(TableStyle([
            ('BOTTOMPADDING',(0,2),(1,2),fontSize/1.,),
            ('VALIGN',(0,0),(-1,-1),'TOP',),
            ]))
         itemProject._argW[0] = 1.2*inch
         itemProject._argW[1] = 5.3*inch
         itemProject.hAlign = "LEFT"
   
         itemRunsHeader = Paragraph("Observing Runs:",kstyle)
         itemRunsHeader.spaceBefore = 1*fontSize
   
         elements = [[itemProject],]
         itemRunsTable = Table(elements)
         itemRunsTable.setStyle(TableStyle([
               ('BOX',(0,0),(-1,-1),0.25,colors.black,),
               ('VALIGN',(0,0),(-1,-1),'TOP',),
               ]))
         itemRunsTable.spaceBefore = 1.0*fontSize
         itemRunsTable.hAlign = "LEFT"
         items.append( itemRunsTable)
   
   itemConflicts = Paragraph("Conflicts:",kstyle)
   itemConflicts.spaceBefore = 2*fontSize
   items.append( itemConflicts)
   
   if self.conflicts:
      itemConflicts = Paragraph(str(self.conflicts),istyle)
      itemConflicts.spaceBefore = 0.5*fontSize
      items.append( itemConflicts)
   else:
      itemConflicts = Paragraph("None",istyle)
      itemConflicts.spaceBefore = 0.5*fontSize
      items.append( itemConflicts)
   
   itemRequire = Paragraph("Special or Additional Requirements:",kstyle)
   itemRequire.spaceBefore = 2*fontSize
   items.append( itemRequire)
   
   if self.requirements:
      itemRequire = Paragraph(str(self.requirements),istyle)
      itemRequire.spaceBefore = 0.5*fontSize
      items.append( itemRequire)
   else:
      itemRequire = Paragraph("None",istyle)
      itemRequire.spaceBefore = 0.5*fontSize
      items.append( itemRequire)
   
   items.append( PageBreak())
   
   cover.build(items)
   
   pdfCover = PdfReader(report)
   output = PdfWriter()
   #numPages = pdfCover.getNumPages()
   numPages = len(pdfCover.pages)
   [output.add_page(pdfCover.pages[j]) for j in range(numPages)]
   
   if self.justification is not None:
      just = self.justification.data
      pdfStream = StringIO(just)
      pdfReader = PdfReader(pdfStream)
      numPages = len(pdfReader.pages)
      [output.add_page(pdfReader.pages[j]) for j in range(numPages)]
   
   proposal = StringIO()
   output.write(proposal)
   result = proposal.getvalue()
   
   return result


def generate_targ(targets):
   '''Given a list of targets with RA,DEC, make a PDF table. We are simply
   making a table from list of lists. The parser has made sure it has the
   desired format'''
   report = StringIO()
   cover = SimpleDocTemplate(report,pagesize=letter,leftMargin=0.5*inch,rightMargin=0.5*inch)
   style = styles.getSampleStyleSheet()
   fontSize = 9
   items = [ ]
   
   getkey = lambda dict,key: (key in dict and str(dict[key])) or ("")
   
   tstyle = ParagraphStyle( name='Title', fontName='Times-Bold', fontSize=16, leading=16)
   kstyle = ParagraphStyle( name='Title', fontName='Times-Bold', fontSize=fontSize, leading=16)
   istyle = ParagraphStyle( name='Item', fontName='Courier', fontSize=fontSize, leading=fontSize)
   items.append(Paragraph("Targets", tstyle))

   if not targets:
      items.append(Paragraph("This proposal has no specific targets", kstyle))
      cover.build(items)
      return report.getvalue()

   Titles = targets[0]
   msizes = []
   for i in range(len(Titles)):
      msizes.append(max([len(str(row[i])) for row in targets]))
   tsize = sum(msizes)

   elements = [ [ Paragraph(title,kstyle) for title in Titles]]
   for row in targets[1:]:
      elements.append([Paragraph(str(field), istyle) for field in row])
   
      itemTargets = Table(elements)
      itemTargets.setStyle(TableStyle([
            ('GRID',(0,0),(-1,-1),0.25,colors.black,),
            ('BOX',(0,0),(-1,-1),0.25,colors.black,),
            ('LINEABOVE',(0,0),(-1,-1),0.25,colors.black,),
            ('LINEBELOW',(0,0),(-1,-1),0.25,colors.black,),
            ('RIGHTPADDING',(0,0),(-1,-1),0,),
            ('VALIGN',(0,0),(-1,-1),'TOP',),
            ]))
      for j in range(len(msizes)):
         itemTargets._argW[j] = msizes[j]/tsize*7*inch
      itemTargets.hAlign = "LEFT"
      itemTargets.spaceBefore = 0.5*fontSize
   
   items.append( itemTargets )
   cover.build(items)
   return report.getvalue()