from plone import schema
from plone import api
from plone.dexterity.content import Container
from plone.dexterity.browser.add import DefaultAddForm, DefaultAddView
from plone.supermodel import model
from zope.interface import implementer
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from plone.namedfile.file import NamedBlobFile
from .generate_pdf import generate_pdf,TBDgenerate_pdf
from tarfile import TarFile, TarInfo
from io import BytesIO,StringIO
from . import utils


class IProposalFolder(model.Schema):
    """Dexterity-Schema for Proposal"""

    semester = schema.TextLine(
        title='Semester (e.g., 2025B, 2026A, ...)',
        description='The proposals semester',
        required=True,
    )
    is_tbd = schema.Bool(
        title='TBD Proposals',
        description='Select if proposals are for TBD time, so shorter PDFs',
        required=False
    )


@implementer(IProposalFolder)
class ProposalFolder(Container):
    """Instance class"""

    def get_tgz_file(self):
        """Return the tgz file if it exists, else None"""
        tid = self.id+".tgz"
        if tid in self.objectIds():
            return self[tid]
        return None

    def Title(self):
        """Return the title of the folder"""
        if self.is_tbd:
           return "TBD Proposals for semester "+self.semester
        else:
           return "Proposals for semester "+self.semester

class AddForm(DefaultAddForm):

    def create(self, data):
        # override to give custom short name

        if data['is_tbd']:
           fname = "TBDproposal_listing"+data['semester'].lower()
        else:
           fname = "proposal_listing"+data['semester'].lower()

        # Create object the usual way
        obj = super().create(data)
        obj.id = fname
        return obj

class AddView(DefaultAddView):
    form = AddForm

        
class View(BrowserView):
    """Default view for ProposalFolder"""

    def get_items(self):
        """Return all proposals on the site with given semesters"""
        semester = self.context.semester
        TBD = self.context.is_tbd

        run = self.request.form.get('run',None)
        telescope = self.request.form.get('telescope',None)
        instrument = self.request.form.get('instrument',None)

        # Check if user is a Manager
        if "Manager" in api.user.get_roles():
            if TBD:
               brains = api.content.find(
                   portal_type='TBDproposal', semester=semester)
            else:
               brains = api.content.find(
                   portal_type='proposal', semester=semester)
        else:
            if TBD:
               brains = api.content.find(
                   portal_type='TBDproposal', semester=semester,
                   review_state="submitted")
            else:
               brains = api.content.find(
                   portal_type='proposal', semester=semester,
                   review_state="submitted")

        if run is not None or telescope is not None or instrument is not None:
            filtered = []
            objs = [brain.getObject() for brain in brains]

            for brain in brains:
                obj = brain.getObject()
                include = False
                if not obj.runs: continue
                for r in obj.runs:
                    if run is not None and r['preferred'] == run:
                        include=True
                        break
                    if telescope is not None and r['telescope'] == telescope:
                        include = True
                        break
                    if instrument is not None:
                        if r['inst1'] and r['inst1'].find(instrument) >= 0:
                            include = True
                            break
                        if r['inst2'] and r['inst2'].find(instrument) >= 0:
                            include = True
                            break
                if include:  filtered.append(brain)
            return filtered
            
        return brains


class TGZView(BrowserView):
    """View for ProposalFolder to generate a tgz file of all proposals"""

    def __call__(self):
        messages = IStatusMessage(self.request)
        semester = self.context.semester
        tid = self.context.id+".tgz"

        # All proposals for this semester
        if self.context.is_tbd:
           brains = api.content.find(
               portal_type='TBDproposal', semester=semester, state='submitted')
        else:
           brains = api.content.find(
               portal_type='proposal', semester=semester, state='submitted')

        # Frist, check if the tgz file already exists, and if so, only re-make
        # if any proposal is newer than the tgzfile.
        exists = tid in self.context.objectIds()
        if exists:
            tmod = self.context[tid].modified()
            for brain in brains:
                if brain.modified > tmod:
                    api.content.delete(obj=self.context[tid])
                    exists = None
                    break
        if not exists:
            # Make an in-memoery tgz file
            tarout = BytesIO()
            pdf_names = []
            with TarFile.open(fileobj=tarout, mode='w:gz') as tar:
                for brain in brains:
                    proposal = brain.getObject()
                    name = proposal.pi_name
                    fn = name.split()[0][0].lower()
                    ln = name.split()[-1].lower()
                    idx = 0
                    if self.context.is_tbd:
                        prefix = 'tbd'
                    else:
                        prefix = ''
                    pdfname = f"{fn}_{ln}_{prefix}{proposal.semester}_{idx}.pdf" 
                    while pdfname in pdf_names:
                        idx += 1
                        pdfname = f"{fn}_{ln}_{proposal.semester}_{idx}.pdf" 
                    pdfname = pdfname.replace("_0.pdf",".pdf")
                    pdf_names.append(pdfname)
                    
                    if self.context.is_tbd:
                        pdf = TBDgenerate_pdf(proposal)
                    else:
                        pdf = generate_pdf(proposal)
                    # Create a file-like object for the PDF
                    pdf_file = BytesIO(pdf)
                    # Create a TarInfo object for the PDF file
                    tarinfo = TarInfo(name=f"{tid}/{pdfname}")
                    tarinfo.size = len(pdf)
                    tarinfo.mtime = proposal.modified()
                    # Add the PDF file to the tar archive
                    tar.addfile(tarinfo, fileobj=pdf_file)

            # Create the tgz file
            blob_file = NamedBlobFile(data=tarout.getvalue(), 
                                      contentType="application/gzip", 
                                      filename=tid)
            api.content.create(
                container=self.context,
                type='File',
                id=tid,
                title='Proposal TGZ file',
                file=blob_file
            )
            messages.add(u"TGZ file updated successfully.", type="info")

        else:
            messages.add(u"TGZ file exists and is up to date", type="info")

        item_url = self.context.absolute_url()
        return self.request.response.redirect(item_url)

class TargView(BrowserView):
    """View for ProposalFolder to generate a tgz file of all targets"""

    def __call__(self):
        messages = IStatusMessage(self.request)
        semester = self.context.semester

        if self.context.is_tbd:
            # No target lists
            messages.add(u"TBD Proposals do not have target lists", type="error")
            item_url = self.context.absolute_url()
            return self.request.response.redirect(item_url)

        tid = self.context.id+"_targ.tgz"
        tdir = self.context.id+"_targ"

        # All proposals for this semester
        brains = api.content.find(
            portal_type='proposal', semester=semester, state='submitted')

        # Frist, check if the tgz file already exists, and if so, only re-make
        # if any proposal is newer than the tgzfile.
        exists = tid in self.context.objectIds()
        if exists:
            tmod = self.context[tid].modified()
            for brain in brains:
                if brain.modified > tmod:
                    api.content.delete(obj=self.context[tid])
                    exists = None
                    break
        if not exists:
            # Make an in-memoery tgz file
            tarout = BytesIO()
            pdf_names = []
            with TarFile.open(fileobj=tarout, mode='w:gz') as tar:
                for brain in brains:
                    proposal = brain.getObject()
                    name = proposal.pi_name
                    fn = name.split()[0][0].lower()
                    ln = name.split()[-1].lower()
                    idx = 0
                    pdfname = f"{fn}_{ln}_{proposal.semester}_{idx}_targ.pdf" 
                    while pdfname in pdf_names:
                        idx += 1
                        pdfname = f"{fn}_{ln}_{proposal.semester}_{idx}_targ.pdf" 
                    pdfname = pdfname.replace("_0.pdf",".pdf")
                    pdf_names.append(pdfname)
                    txtname = pdfname.replace('.pdf','.txt')
                    csvname = pdfname.replace('.pdf','.csv')

                    # Now figure out how to proceed based on what we've got
                    pdf = proposal.getTargetPDF()
                    pdf_file = BytesIO(pdf)
                    # Create a TarInfo object for the PDF file
                    tarinfo = TarInfo(name=f"{tdir}/{pdfname}")
                    tarinfo.size = len(pdf)
                    tarinfo.mtime = proposal.modified()
                    # Add the PDF file to the tar archive
                    tar.addfile(tarinfo, fileobj=pdf_file)

                    csv = proposal.getTargetCSV()
                    if csv is None and proposal.target_list is not None:
                        # a PDF is involved. do the magic:
                        txt = utils.pdf2ascii(proposal.target_list.data)
                        txt_file = BytesIO(txt)
                        tarinfo = TarInfo(name=f"{tdir}/{txtname}")
                        tarinfo.size = len(txt)
                        tarinfo.mtime = proposal.modified()
                        tar.addfile(tarinfo, fileobj=txt_file)
                    elif csv is None:
                        continue
                    else:
                        csv_file = BytesIO(csv.encode('utf-8'))
                        tarinfo = TarInfo(name=f"{tdir}/{csvname}")
                        tarinfo.size = len(csv)
                        tarinfo.mtime = proposal.modified()
                        tar.addfile(tarinfo, fileobj=csv_file)
            # Create the tgz file
            blob_file = NamedBlobFile(data=tarout.getvalue(), 
                                      contentType="application/gzip", 
                                      filename=tid)
            api.content.create(
                container=self.context,
                type='File',
                id=tid,
                title='Proposal Target TGZ file',
                file=blob_file
            )
            messages.add(u"Target TGZ file updated successfully.", type="info")

        else:
            messages.add(u"Target TGZ file exists and is up to date", type="info")

        item_url = self.context.absolute_url()
        return self.request.response.redirect(item_url)

