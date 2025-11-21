from plone import schema
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.autoform import directives
from plone.restapi.controlpanels import RegistryConfigletPanel
from zope.component import adapter
from zope.interface import Interface

'''This module defines the schema for a Proposals site registry.
Here we store data needed by proposals to construct vocabularies
dynamically. This used to be done with the portal_properties,
which no longer exists.'''

default_block_vocab = '''11 Jan 2026,26 Jan 2026,16
27 Jan 2026,10 Feb 2026,15
11 Feb 2026,24 Feb 2026,14
25 Feb 2026,11 Mar 2026,14
12 Mar 2026,25 Mar 2026,14
26 Mar 2026,09 Apr 2026,14
10 Apr 2026,23 Apr 2026,14
24 Apr 2026,08 May 2026,14
09 May 2026,22 May 2026,14
23 May 2026,07 Jun 2026,15
08 Jun 2026,20 Jun 2026,13
21 Jun 2026,06 Jul 2026,15'''

default_run_vocab = '''2026_D01
2026_L01
2026_D02
2026_L02
2026_D03
2026_L03
2026_D04
2026_L04
2026_D05
2026_L05
2026_D06
2026_L06
'''

default_instrument_vocab = '''Baade:IMACS:f/2,
Baade:IMACS:f/4
Baade:IMACS:GISMO
Baade:IMACS:Rosie-IFU
Baade:FourStar
Baade:FIRE
Baade:MagE
Baade:LLAMAS
Clay:MIKE
Clay:LDSS3-C
Clay:PFS
Clay:M2FS
Clay:IFU-M
Clay:WINERED
Clay:MegaCam
Clay:MagAO-X
Clay:Lightspeed
Swope:Direct
'''

default_telescope_vocab = "Baade\nClay\nSwope"
default_service_vocab = []
for tel in default_telescope_vocab.split('\n'):
   default_service_vocab.append(tel+":No")
   default_service_vocab.append(tel+":Yes")
default_service_vocab = "\n".join(default_service_vocab)
default_moon_vocab = []
for i in range(14,0,-1):
   default_moon_vocab.append('|{}|'.format(i))
for i in range(-14,15):
   default_moon_vocab.append('{:+d}'.format(i))
default_moon_vocab = '\n'.join(default_moon_vocab)


class IProposalsSettings(Interface):

   block_vocab = schema.Text(
      title="Block Vacabulary",
      description="One block per line, comma-separated lines with:"\
                  " start date, end data and number of nights",
      default=default_block_vocab,
      required=False
   )

   semester = schema.TextLine(
      title="Semester",
      description="The Semester code (e.g., 2024A)",
      default="2026A",
      required=False,
   )

   run_vocab = schema.Text(
      title="Run Vocabulary",
      description="Vocabulary of run names, one per line",
      default=default_run_vocab,
      required=False,
   )

   service_vocab = schema.Text(
      title="Service Vocabulary",
      description="Service observing by telescope, one per line",
      default=default_service_vocab,
      required=False,
   )

   instrument_vocab = schema.Text(
      title="Instrument Vocabulary",
      description="Instrument listing, one per line",
      default=default_instrument_vocab,
      required=False
   )

   moon_vocab = schema.Text(
      title="Moon phase Vocabulary",
      description="Moon phases listing, one per line",
      default=default_moon_vocab,
      required=False
   )

   telescope_vocab = schema.Text(
      title="Available Telescopes Vocabulary",
      description="List of available telescopes, one per line",
      default=default_telescope_vocab,
      required=False
   )

class ProposalsRegistryEditForm(RegistryEditForm):
   schema = IProposalsSettings
   schema_prefix = "proposals"
   label = "Propoals Settings"

class ProposalsControlPanelFormWrapper(ControlPanelFormWrapper):
   form = ProposalsRegistryEditForm

@adapter(Interface, Interface)
class ProposalsRegistryConfigletPanel(RegistryConfigletPanel):
    schema = IProposalsSettings
    schema_prefix = "proposals"
    configlet_id = "proposals-controlpanel"
    configlet_category_id = "Products"
    title = "Propospals Settings"
    group = "Products"
