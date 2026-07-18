from plone import schema
from plone import api
from plone.dexterity.content import Container
from plone.supermodel import model
from zope.interface import implementer
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from plone.namedfile.file import NamedBlobFile
from .generate_pdf import generate_pdf
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
    def create(self, data):
        # override to give custom short name

        if self.is_tbd:
           fname = "TBDproposal_listing"+self.semester.lower()
        else:
           fname = "proposal_listing"+self.semester.lower()

        # Create object the usual way
        obj = super().create(data)
        obj.id = fname
        return obj

    def get_tgz_file(self):
        """Return the tgz file if it exists, else None"""
        tid = self.id+".tgz"
        if tid in self.objectIds():
            return self[tid]
        return None

    def Title(self):
        """Return the title of the folder"""
        return "Proposals for semester "+self.semester

        
class View(BrowserView):
    """Default view for ProposalFolder"""

    def get_items(self):
        """Return all proposals on the site with given semesters"""
        catalog = self.context.portal_catalog
        semester = self.context.semester
        brains = api.content.find(
            portal_type='proposal', semester=semester)
        return brains

class TGZView(BrowserView):
    """View for ProposalFolder to generate a tgz file of all proposals"""

    def __call__(self):
        messages = IStatusMessage(self.request)
        semester = self.context.semester
        tid = self.context.id+".tgz"

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
                    pdfname = f"{fn}_{ln}_{proposal.semester}_{idx}.pdf" 
                    while pdfname in pdf_names:
                        idx += 1
                        pdfname = f"{fn}_{ln}_{proposal.semester}_{idx}.pdf" 
                    pdfname = pdfname.replace("_0.pdf",".pdf")
                    pdf_names.append(pdfname)
                    
                    pdf = generate_pdf(proposal)
                    # Create a file-like object for the PDF
                    pdf_file = BytesIO(pdf)
                    # Create a TarInfo object for the PDF file
                    tarinfo = TarInfo(name=f"{tid}/{proposal.id}.pdf")
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
                    csvname = pdfname.replace('.pdf','.txt')

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

