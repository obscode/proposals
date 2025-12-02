from plone import schema
from plone.autoform import directives
from plone.dexterity.content import Container
from plone.dexterity.browser.add import DefaultAddForm, DefaultAddView
from plone.schema.email import Email
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model
from z3c.form.browser.text import TextWidget
from zope.interface import implementer
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFPlone.resources import add_resource_on_request


from collective.z3cform.datagridfield.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.blockdatagridfield import \
    BlockDataGridFieldWidgetFactory
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
      title='Preferred',
      vocabulary="proposals.RUNS",
      required=False,
      #default='D01'
   )

   fromblock = schema.Choice(
      title='From',
      vocabulary="proposals.RUNS",
      required=False,
      #default='--'
   )

   toblock = schema.Choice(
      title='To',
      vocabulary="proposals.RUNS",
      required=False,
      #default='--'
   )

   nights = schema.Int(
      title='Nights',
      required=False,
   )
   directives.widget("nights", TextWidget, size=5)

   moon = schema.Choice(
      title='Moon',
      vocabulary="proposals.MOONPHASES",
      required=False,
      #default='--'
   )   

   telescope = schema.Choice(
       title='Telescope',
       vocabulary="proposals.TELESCOPES",
       required=False,
       #default='--'
   )

   inst1 = schema.Choice(
       title='instr. one',
       vocabulary="proposals.INSTRUMENTS",
       required=False,
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
       required=False,
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
       required=False,
   )

   coIs = schema.TextLine(
       title="Co-Investigators",
       required=False,
   )




class IProposal(model.Schema):
    """Dexterity-Schema for Proposal"""

    model.fieldset("Justification",
        label="Science Justification PDFs",
        fields=['abstract','target_list','justification','progress_to_date'],
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
        description='Email adress of the PI',
        required=True,
    )

    telephone = schema.TextLine(
        title='Telephone',
        required=True,
    )

    too = NamedBlobFile(
        title='Target of Opportunity Time Request(s)',
        required=False,
    )

    conflicts = schema.Text(
        title='Conflicts',
        description='For example, a list of dates for which you cannot observe',
        required=False,
    )

    conflicts = schema.Text(
        title='Special or Additional Requirements',
        description='A list of extra requirements, such as specific dates for'\
                    ' mandatory observing or additional needs.',
        required=False,
    )

    abstract = NamedBlobFile(
        title='Abstract',
        description='A PDF file that contains the abstract for all projects',
        required=False,
    )
    target_list = NamedBlobFile(
        title='Target List',
        description='A PDF with targets for all projects',
        required=False,
    )

    justification = NamedBlobFile(
        title='Scientific and Technical Justification (5 page max)',
        description='A PDF with scientific and technical justifications of proposal, '\
                    'including figures and references',
        required=False,
    )
    progress_to_date = NamedBlobFile(
        title='Progress ot Date on Previous Allocations (1 page)',
        description='A PDF discussion progress to adte on data obtained during nights '\
                    'allocated over the previous 3 years',
        required=False,
    )

    projects = schema.List(
        title="Projects",
        value_type=DictRow(
            title="Project List",
            schema=IProjectSchema,
        )
    )
    directives.widget("projects", DataGridFieldFactory,
                      auto_append=False)

    runs = schema.List(
        title="Runs",
        value_type=DictRow(
           title="Run",
           schema=IObservingRunSchema,
        )
    )
    directives.widget("runs", DataGridFieldFactory,
                     auto_append=False)


@implementer(IProposal)
class Proposal(Container):
    """Proposal instance class"""

#### Forms ####

class AddForm(DefaultAddForm):

    template = ViewPageTemplateFile('myadd.pt')

    def update(self):
        super().update()

    def updateWidgets(self):
        super().updateWidgets()
    
    def create(self, data):
        return super().create(data)

class AddView(DefaultAddView):
    form = AddForm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ignoreRequiredOnExtract = True

    def __call__(self):
        add_resource_on_request(self.request, 'proposals-fixforms')
        return super(AddView, self).__call__()

