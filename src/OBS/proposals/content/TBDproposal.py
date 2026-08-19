from plone import schema
from Acquisition import aq_inner
from plone.autoform import directives
from plone import api
from plone.dexterity.content import Container
from plone.dexterity.browser.add import DefaultAddForm, DefaultAddView
from plone.dexterity.browser.view import DefaultView
from plone.dexterity.browser.edit import DefaultEditForm, DefaultEditView
from plone.schema.email import Email
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model
from z3c.form.browser.text import TextWidget
from z3c.form import button
from zope.interface import implementer,invariant
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.browser import BrowserView
from Products.CMFPlone.resources import add_resource_on_request
from Products.statusmessages.interfaces import IStatusMessage
from plone.protect.authenticator import createToken
from .generate_pdf import TBDgenerate_pdf
from . import validators, utils
import csv
from io import StringIO


from collective.z3cform.datagridfield.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.row import DictRow

from .vocabularies import YESNO,NUMBERS


class ITBDProjectSchema(model.Schema):
   directives.mode(proj_number="display")
   directives.widget("proj_number", TextWidget, size=5)
   proj_number = schema.TextLine(
       title = "Project",
       required=False,
       default='1',
   )
   priority = schema.Choice(
       title = "Priority",
       required=False,
       vocabulary=NUMBERS,
       default='1'
   )
   proj_title = schema.TextLine(
       title='Project Title',
       required=True,
   )

   coIs = schema.TextLine(
       title="Co-Investigators",
       required=False,
   )

class ITBDProposal(model.Schema):
    """Dexterity-Schema for Proposal"""

    pi_name = schema.TextLine(
        title='Name',
        description='The lead investigator on the observing proposal',
        required=True,
    )
    department = schema.TextLine(
        title='Department',
        description='Institution and/or department',
        required=True
    )

    email = Email(
        title='Email',
        description='Email adress of the PI',
        required=True,
    )

    conflicts = schema.Text(
        title='Conflicts',
        description='For example, a list of dates for which you cannot observe',
        required=False,
    )

    requirements = schema.Text(
        title='Special or Additional Requirements',
        description='A list of extra requirements, such as specific dates for'\
                    ' mandatory observing or additional needs.',
        required=False,
    )

    justification = NamedBlobFile(
        title='Scientific and Technical Justification (5 page max)',
        description='A PDF with scientific and technical justifications    of proposal, '\
                    'including figures and references',
        required=False,
        constraint=validators.validate_PDF_TBD_SJ,
    )

    projects = schema.List(
        title="Projects",
        value_type=DictRow(
            title="Project List",
            schema=ITBDProjectSchema,
        )
    )
    directives.widget("projects", DataGridFieldFactory,
                      auto_append=False)


@implementer(ITBDProposal)
class TBDProposal(Container):
    """TBD Proposal instance class"""
    
    def statusMessage(self):
        '''Returns the current status of the proposal'''
        missing = []
        conflict = []
        message = ""
        if self.justification is None:
            missing.append("Need Scientific Justification")
        if missing or conflict:
            message += "\n".join(missing+conflict)
            return message
        return "Your proposal appears to satisfy the requirements for submission"


    def status(self):
        '''Returns True if proposal is ready for submission'''
        wf_state = api.content.get_state(self)
        if wf_state == "submitted":
           return "Submitted"

        # At this point, we should be "private"
        if self.justification is None: return "Incomplete"

        return "Ready for Submission"

    def Title(self):
        '''Returns an appropriate title'''
        return self.id


#### Forms ####

def noExistingProposal(form):
    '''Return False if there exists a proposal for this semester. Logic is
    backwards because we're asking if we shoudl allow submission.'''
    context = aq_inner(form.context)
    l = context.listFolderContents(contentFilter={"portal_type":"TBDproposal"})
    semester = api.portal.get_registry_record("proposals.semester")
    result = True
    for i in l:
        if i.semester == semester:
            result = False
    return result

class AddForm(DefaultAddForm):

    template = ViewPageTemplateFile('myTBDadd.pt')

    def update(self):
        super().update()

        # To avoid the problem of field validation errors being printed
        # on blank datagridfield rows, we have to look for such blank
        # rows and null out their errors befofe the form is rendered.
        # Turns out this is easy: if length of DGF widgets is 1, it's blank.

        for field in ['projects']:
            datagrid_widget = self.widgets.get(field)
            if datagrid_widget and hasattr(datagrid_widget, 'widgets'):
                if len(datagrid_widget.widgets) == 1:
                    # a blank line, null out the errors
                    for v,subw in datagrid_widget.widgets[0].widgets.items():
                        subw.error = None

    def updateActions(self):
        # If we already have a proposal, disable submit and do a message
        super().updateActions()

        TBD = api.portal.get_registry_record("proposals.TBD")
        print("TBD:",TBD)
        if not TBD:
            self.request.response.redirect(self.nextURL())
            IStatusMessage(self.request).addStatusMessage(
                "Sorry, TBD proposals are not open at this time", "error")

        res = noExistingProposal(self)
        if not res:
            self.request.response.redirect(self.nextURL())
            IStatusMessage(self.request).addStatusMessage(
                "Sorry, only one TBD proposal per semester allowed", "error")
    
    def create(self, data):
        # override to give custom short name
        member = api.user.get_current()

        sname = member.getId()
        semester = api.portal.get_registry_record("proposals.semester")
        fname = sname+"_TBDproposal"+semester.strip().lower()

        # Create object the usual way
        obj = super().create(data)
        obj.id = fname
        obj.semester = semester
        return obj

class AddView(DefaultAddView):
    form = AddForm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self):
        add_resource_on_request(self.request, 'proposals-fixforms')
        return super(AddView, self).__call__()

class EditForm(DefaultEditForm):

    template = ViewPageTemplateFile('myTBDedit.pt')
    enable_form_tabbing = True

    def update(self):
        super().update()

        # To avoid the problem of field validation errors being printed
        # on blank datagridfield rows, we have to look for such blank
        # rows and null out their errors befofe the form is rendered.
        # Turns out this is easy: if length of DGF widgets is 1, it's blank.

        for field in ['projects']:
            datagrid_widget = self.widgets.get(field)
            if datagrid_widget and hasattr(datagrid_widget, 'widgets'):
                if len(datagrid_widget.widgets) == 1:
                    # a blank line, null out the errors
                    for v,subw in datagrid_widget.widgets[0].widgets.items():
                        subw.error = None

    def applyChanges(self, data):
        super().applyChanges(data)


class EditView(DefaultEditView):

    def __call__(self):
        add_resource_on_request(self.request, 'proposals-fixforms')
        #add_resource_on_request(self.request, 'proposals-nextprev')
        return super(EditView, self).__call__()

class View(DefaultView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def update(self):
        # Disable the menu bar
        #self.request.set('disable_border', True)
        super().update()

    # The following are needed for the simple reason that TAL is limited in
    # what it can do, particularly having python: code produce a string with
    # a single quote in it.
    def editTag(self):
        return "window.location='{}/edit?_authenticator={}'".format(
           self.context.absolute_url(), createToken())

    def deleteTag(self):
        return "window.location='{}/delete_confirmation?_authenticator={}'".format(
           self.context.absolute_url(), createToken())

    def shareTag(self):
        return "window.location='{}/@@sharing?_authenticator={}'".format(
           self.context.absolute_url(), createToken())

    def transitionTag(self):
        stat = self.context.status()
        if stat == "Submitted":
           return "window.location='{}/transition?_authenticator={}&transition={}'".format(
              self.context.absolute_url(), createToken(),'retract')
        elif stat == "Incomplete":
           return "''"
        return "window.location='{}/transition?_authenticator={}&transition={}'".format(
           self.context.absolute_url(), createToken(),'submit')

    def transitionLab(self):
        stat = self.context.status()
        if stat == "Submitted":
           return "Retract"
        return "Submit"


class PDFView(BrowserView):
    """Custom view to generate a PDF of the proposal"""

    def __call__(self):
        context = self.context
        request = self.request
        pdf = TBDgenerate_pdf(context)
        request.response.setHeader('Content-Type', 'application/pdf')
        request.response.setHeader('Content-Disposition', 'inline; filename="TBDproposal.pdf"')
        request.response.setHeader('Content-Length', len(pdf))
        return pdf


class TransitionView(BrowserView):
    """Custom view to change the workflow state of a content item that
    can handle a came_from paramter."""

    def __call__(self):
        context = self.context
        request = self.request
        messages = IStatusMessage(request)
        transition = request.form.get('transition', None)
        successes = {"submit":"TBD Proposal Submitted",
                     "retract":"TBD Proposal Retracted"}
        errors = {"submit":"Failed to submit TBD proposal",
                   "retract":"Failed to retract TBD proposal"}

        # If transition is specified and valid, use it. Otherwise, use a 
        # "toggle"-like transition:  private --> submitted --> private ...
        if transition is not None:
            if transition not in ['submit','retract']:
                messages.add(u"Invalid Workflow Transition", type="error")
        else:
            # Get current state and toggle
            state = api.content.get_state(obj=context)
            if state == 'draft':
                transition = 'submit'
            else:
                transition = 'retract'

        try:
            # 2. Trigger the transition
            api.content.transition(obj=context, transition=transition)
            messages.add(u"{}".format(successes[transition]), type="info")

        except PloneAPIError as e:
            messages.add(u"{}: {}".format(errors[transition],str(e)), 
                         type="error")

        # Now, let's figure out where to end up. If came_from is set,
        # respect that, otherwise, stay put
        came_from = request.form.get("came_from", None)
        if came_from is not None:
            return request.response.redirect(came_from)

        item_url = context.absolute_url()
        return request.response.redirect(item_url)
 
