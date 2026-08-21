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
from z3c.form.interfaces import WidgetActionExecutionError
from zope.interface import implementer,invariant, Invalid
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.browser import BrowserView
from Products.CMFPlone.resources import add_resource_on_request
from Products.statusmessages.interfaces import IStatusMessage
from plone.protect.authenticator import createToken
from .generate_pdf import generate_pdf, generate_targ
from . import validators, utils
import csv
from io import StringIO


from collective.z3cform.datagridfield.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.row import DictRow

from .vocabularies import YESNO,NUMBERS


class IObservingRunSchema(model.Schema):
   """One row of the observing runs"""
   #project = schema.Int(
   #   title='Project',
   #   required=True,
   #   default=1
   #)
   #directives.widget("project", TextWidget, size=5)

   project = schema.Choice(
       title='Project',
       vocabulary=NUMBERS,
       required=False,
       default='1',
   )
   preferred = schema.Choice(
      vocabulary="proposals.RUNS",
      required=True,
      title="Preferred"
      #default='D01'
   )

   fromblock = schema.Choice(
      title='From',
      vocabulary="proposals.RUNS",
      required=True,
      #default='--'
   )

   toblock = schema.Choice(
      title='To',
      vocabulary="proposals.RUNS",
      required=True,
      #default='--'
   )

   nights = schema.Int(
      title='Nights',
      required=True,
   )
   directives.widget("nights", TextWidget, size=5)

   moon = schema.Choice(
      title='Moon',
      vocabulary="proposals.MOONPHASES",
      required=True,
      #default='--'
   )   

   telescope = schema.Choice(
       title='Telescope',
       vocabulary="proposals.TELESCOPES",
       required=True,
       #default='--'
   )

   inst1 = schema.Choice(
       title='instr. one',
       vocabulary="proposals.INSTRUMENTS",
       required=True,
       #default='--'
   )

   inst2 = schema.Choice(
       title='instr. two',
       vocabulary="proposals.INSTRUMENTS",
       required=False,
       #default='--'
   )

   service = schema.Choice(
       title='Service',
       required=False,
       vocabulary=YESNO,
       default='No',
   )

   in_person = schema.Choice(
       title='In Person',
       required=False,
       vocabulary=YESNO,
       default='No',
   )

   observers = schema.TextLine(
       title='Observers',
       required=True,
   )

class IProjectSchema(model.Schema):
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

class ITOORequestSchema(model.Schema):
    """Schema for Target of Opportunity Request"""
    project = schema.Choice(
         title='Project',
         required=False,
         vocabulary=NUMBERS,
         default='1',
    )
    hours = schema.TextLine(
         title='Hours',
         required=True,
    )
    telescopes = schema.TextLine(
        title='Telescopes',
        required=True,
    )

class ITargetSchema(model.Schema):
    """Schema for a single target in a target list"""
    name = schema.TextLine(
        title='Target Name',
        required=False,
    )
    ra1 = schema.TextLine(
        title='RA',
        required=False,
        #constraint=validators.validate_RA,
    )
    ra2 = schema.TextLine(
        title='RA end*',
        required=False,
        #constraint=validators.validate_RA,
    )
    dec1 = schema.TextLine(
        title='Dec (start)',
        required=False,
        #constraint=validators.validate_DEC,
    )
    dec2 = schema.TextLine(
        title='Dec end*',
        required=False,
        #constraint=validators.validate_DEC,
    )
    mag = schema.TextLine(
        title='Magnitude',
        required=False,
    )
    epoch = schema.TextLine(
        title='JD start',
        required=False,
        #constraint=validators.validate_JD,
    )

    epoch2 = schema.TextLine(
        title="JD end",
        required=False,
        #constraint=validators.validate_JD,
    )



class IProposal(model.Schema):
    """Dexterity-Schema for Proposal"""

    model.fieldset("Justification",
        label="Science Justification PDFs",
        fields=['abstract','justification','progress_to_date'],
    )

    model.fieldset("Targets",
        label="List of Targets",
        fields=["notargets","targets","target_list"],
    )

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
        description='Email address of the PI',
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

    abstract = NamedBlobFile(
        title='Abstract',
        description='A PDF file that contains the abstract for all projects',
        required=False,
        constraint = validators.validate_PDF,
    )
    target_list = NamedBlobFile(
        title='Target List',
        description='A PDF or CSV file with targets for all projects (see Help documentation '\
                    'for sample CSV file).',
        required=False,
        constraint = validators.validate_PDF_or_CSV,
    )

    targets = schema.List(
        title="Targets",
        description="Enter targets manually (if you don't have too many). Only RA and DEC are "\
                    "required and can be in either decimal degrees or HH:MM:SS.SS for RA, "\
                    "+DD:MM:SS.SS for DEC. 'JD begin' and 'JD end' are for specific timed "\
                    "observations (e.g., transits). *If you have a range of RA/DEC, use 'RA' "\
                    "for minimum and 'RA end' for maximum and "\
                    "likewise for DEC. For large lists, upload a CSV (preferred) or PDF file below.",
        value_type=DictRow(
            title="Target List",
            schema=ITargetSchema,
        ),
        required=False,
    )
    directives.widget("targets", DataGridFieldFactory,
                     auto_append=False)

    notargets = schema.Bool(
        title="No Specific Targets",
        description="Check this box if you do not have specific targets, for example "\
                    "because you are requesting ToO time for yet-to-be-discovered objects "\
                    "or you have targets distributed all across the sky.",
        required=False,
    )

    justification = NamedBlobFile(
        title='Scientific and Technical Justification (5 page max)',
        description='A PDF with scientific and technical justifications for the proposal, '\
                    'including figures and references',
        required=False,
        constraint=validators.validate_PDF_SJ,
    )
    progress_to_date = NamedBlobFile(
        title='Progress to Date on Previous Allocations (1 page)',
        description='A PDF discussing progress to date on data obtained during nights '\
                    'allocated over the previous 3 years',
        required=False,
        constraint=validators.validate_PDF_PD,
    )

    projects = schema.List(
        title="Projects",
        required = False,
        value_type=DictRow(
            title="Project List",
            schema=IProjectSchema,
        )
    )
    directives.widget("projects", DataGridFieldFactory,
                      auto_append=False)

    runs = schema.List(
        title="Runs",
        required = False,
        value_type=DictRow(
           title="Run",
           schema=IObservingRunSchema,
        )
    )
    directives.widget("runs", DataGridFieldFactory,
                     auto_append=False)

    too = schema.List(
        title="Target of Opportunity Requests",
        required=False,
        value_type=DictRow(
           title="ToO Request",
           schema=ITOORequestSchema,
        )
    )
    directives.widget("too", DataGridFieldFactory,
                     auto_append=False)

    @invariant
    def field_validation(data):
        valid,message = validators.extra_proposal_validation(data)
        if not valid:
            raise Invalid(message)



@implementer(IProposal)
class Proposal(Container):
    """Proposal instance class"""
    
    def get_runs_too(self, projnum):
        '''Return list of runs and too's for project number projnum'''
        runs = []
        if self.runs is not None:
           runs = runs + [run for run in self.runs \
                          if run['project'] == str(projnum)]
        if self.too is not None:
           for too in self.too:
              if too['project'] == str(projnum):
                 runs.append(dict(project=str(projnum), preferred='ToO', 
                         fromblock='ToO', toblock='ToO', 
                         nights="{:.2f}".format(float(too['hours'])/24), 
                         moon='--', telescope=too['telescopes'], 
                         inst1='--:--', inst2='--:--', service='--', in_person='--',
                         observers='--'))

        if not runs: 
           # Return dummy data
           runs = [dict(project=projnum, preferred='--', fromblock='--',
                  toblock='--', nights='--', moon='--',
                  telescope='--', inst1='--:--', inst2='--:--',
                  service='--', in_person='--', observers='--')]

        return runs

    def get_runs(self, projnum):
        '''Return list of runs for project number projnum'''
        runs = []
        if self.runs is not None:
           runs = runs + [run for run in self.runs \
                          if run['project'] == str(projnum)]
        return runs
        #if not runs: 
        #   # Return dummy data
        #   runs = [dict(project=projnum, preferred='--', fromblock='--',
        #          toblock='--', nights='--', moon='--',
        #          telescope='--', inst1='--:--', inst2='--:--',
        #          service='--', in_person='--', observers='--')]

        return runs

    def get_num_projects(self):
        '''Returns the number of projects in this proposal'''
        if self.projects is None: return 0
        return len(self.projects)
        prjs = []
        if self.runs is None: return 0
        for run in self.runs:
            if run['project'] not in prjs:  prjs.append(run['project'])
        return len(prjs)

    def get_toos(self, projnum):
        '''Return list of ToO requests for project number projnum'''
        if self.too is None:
            return []
        return [too for too in self.too if too['project'] == str(projnum)]

    def statusMessage(self):
        '''Returns the current status of the proposal'''
        missing = []
        conflict = []
        message = ""
        if self.abstract is None:
            missing.append("Need Abstract")
        if self.target_list is None and not self.targets and not self.notargets:
            missing.append("Need Target List")
        if self.notargets and (self.targets is not None or self.target_list is not None):
            conflict.append("Cannot have both 'No Specific Targets' and a target list")
        if self.targets is not None and self.target_list is not None:
            conflict.append("Either uplaod a targets list of enter targets manually, not both")
        if self.justification is None:
            missing.append("Need Scientific Justification")
        if self.progress_to_date is None:
            missing.append("Need Progress to Date")
        if not self.projects:
            missing.append("Need at least one project")
        else:
            for project in self.projects:
                runs = self.get_runs(project['proj_number'])
                toos = self.get_toos(project['proj_number'])
                if not runs and not toos:
                    missing.append("Need at least one run or ToO for "\
                                   "project {}".format(project['proj_number']))
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
        message = self.statusMessage()
        if message.find('satisfy') > 0:
           return "Ready for Submission"
        else:
            return "Incomplete"

    def Title(self):
        '''Returns an appropriate title'''
        return self.id

    def getTargetsList(self, str_output=True):
        '''Get the list of targets based on what's in the proposal in a standard
        format as a list of lists (good for table views)'''
        if self.notargets:
            # Eeasy peasy
            return [[]]," No specific targets specified"
        
        if self.targets is not None:
            if not str_output:
                l = [['Name','RA start','RA end','DEC start','DEC end','Mag','JD start','JD end']]
            else:
                l = [['Name','RA','DEC','Mag','JD start','JD end']]
            for targ in self.targets:
                if str_output:
                    ra = utils.dec2hms(utils.parse_ra(targ['ra1']))
                    if targ['ra2'] is not None:
                        ra = ra + " - " + utils.dec2hms(utils.parse_ra(targ['ra2']))
                    dec = utils.dec2dms(utils.parse_dec(targ['dec1']))
                    if targ['dec2'] is not None:
                        dec = dec + " - " + utils.dec2dms(utils.parse_ra(targ['dec2']))
                    l.append([targ['name'],ra, dec,
                              targ['mag'],targ['epoch'],targ['epoch2']])
                else:
                    l.append([targ['name'],targ['ra1'],targ['ra2'],targ['dec1'],
                              targ['dec2'],targ['mag'],targ['epoch'],targ['epoch2']])
            return l,"Targets specified manually"

        if self.target_list is not None:
            # could be a CSV file or PDF. Try CSV first
            try:
               # CSV are string objects, but NamedFileBlobs store in bytes
               strdata = self.target_list.data.decode('utf-8')
               fileobj = StringIO(strdata)
               reader = csv.reader(fileobj)
               l,message = utils.parse_csv(reader, str_output=str_output)
               return l,message
            except:
               #fileobj.close()
               # PDF then, nothing to do
               return [],"Error: problem parsing the CSV file."
        return [], "Error: how did I get here?"
    
    def getTargetCSV(self):
        '''Get the targest list as a CSV based on what's in the proposal'''
        if self.notargets:
            return "Field,RA,DEC,Mag,Epoch\n"

        l,message = self.getTargetsList(str_output=False)
        if len(l) == 0: return None
        csv = ""
        for row in l:
            csv += ",".join([str(f)for f in row])
            csv += "\n"
        return csv
        
    
    def getTargetPDF(self):
        '''Get a PDF of the targets based on what's in the proposal'''
        l,message = self.getTargetsList()
        if self.target_list is not None and len(l) == 0:
            # Must be a PDF
            return self.target_list.data

        return generate_targ(l)



            



#### Forms ####

def noExistingProposal(form):
    '''Return False if there exists a proposal for this semester. Logic is
    backwards because we're asking if we shoudl allow submission.'''
    context = aq_inner(form.context)
    l = context.listFolderContents(contentFilter={"portal_type":"proposal"})
    semester = api.portal.get_registry_record("proposals.semester")
    result = True
    for i in l:
        if i.semester == semester:
            result = False
    return result

class AddForm(DefaultAddForm):

    template = ViewPageTemplateFile('myadd.pt')

    def update(self):
        super().update()

        # To avoid the problem of field validation errors being printed
        # on blank datagridfield rows, we have to look for such blank
        # rows and null out their errors befofe the form is rendered.
        # Turns out this is easy: if length of DGF widgets is 1, it's blank.

        for field in ['projects','runs','too']:
            datagrid_widget = self.widgets.get(field)
            if datagrid_widget and hasattr(datagrid_widget, 'widgets'):
                if len(datagrid_widget.widgets) == 1:
                    # a blank line, null out the errors
                    for v,subw in datagrid_widget.widgets[0].widgets.items():
                        subw.error = None
     

    def updateActions(self):
        # If we already have a proposal, disable submit and do a message
        super().updateActions()
        res = noExistingProposal(self)
        if not res:
            self.request.response.redirect(self.nextURL())
            IStatusMessage(self.request).addStatusMessage(
                "Sorry, only one proposal per semester allowed", "error")
    
    def create(self, data):
        # override to give custom short name
        member = api.user.get_current()

        sname = member.getId()
        semester = api.portal.get_registry_record("proposals.semester")
        fname = sname+"_proposal"+semester.strip().lower()

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

    template = ViewPageTemplateFile('myedit.pt')
    enable_form_tabbing = True

    def update(self):
        super().update()

        # To avoid the problem of field validation errors being printed
        # on blank datagridfield rows, we have to look for such blank
        # rows and null out their errors befofe the form is rendered.
        # Turns out this is easy: if length of DGF widgets is 1, it's blank.

        for field in ['projects','runs','too']:
            datagrid_widget = self.widgets.get(field)
            if datagrid_widget and hasattr(datagrid_widget, 'widgets'):
                if len(datagrid_widget.widgets) == 1:
                    # a blank line, null out the errors
                    for v,subw in datagrid_widget.widgets[0].widgets.items():
                        subw.error = None
     

    def applyChanges(self, data):
        # Ensure we have a running number for each project:
        for i,proj in enumerate(data['projects']):
            proj['proj_number'] = i+1
        super().applyChanges(data)


class EditView(DefaultEditView):

    def __call__(self):
        add_resource_on_request(self.request, 'proposals-fixforms')
        add_resource_on_request(self.request, 'proposals-nextprev')
        return super(EditView, self).__call__()

class View(DefaultView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def update(self):
        # Disable the menu bar
        #self.request.set('disable_border', True)
        super().update()

    def instrument(self, inst):
        '''Given a complete instrument string in the form 
           [telescope]:[instrument], return only instrument'''
        if not inst:
            return '--'
        if ':' in inst:
            return ':'.join(inst.split(':')[1:])
        else:
            return inst

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
        pdf = generate_pdf(context)
        request.response.setHeader('Content-Type', 'application/pdf')
        request.response.setHeader('Content-Disposition', 'inline; filename="proposal.pdf"')
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
        successes = {"submit":"Proposal Submitted",
                     "retract":"Proposal Retracted"}
        errors = {"submit":"Failed to submit proposal",
                   "retract":"Failed to retract proposal"}

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
 
