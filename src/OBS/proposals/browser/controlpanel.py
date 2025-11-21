from plone import schema
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.autoform import directives
from plone.restapi.controlpanels import RegistryConfigletPanel
from zope.component import adapter
from zope.interface import Interface

#import json

'''VOCABULARY_SCHEMA = json.dumps(
    {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "token": {"type": "string"},
                        "titles": {
                            "type": "object",
                            "properties": {
                                "lang": {"type": "string"},
                                "title": {"type": "string"},
                            },
                        },
                    },
                },
            }
        },
    }
)'''

class IProposalsSettings(Interface):

   semester = schema.TextLine(
      title="Semester",
      description="The Semester code (e.g., 2024A)",
      default="2026A",
      required=False,
   )

   '''runs = schema.JSONField(
      title="Runs vocabulary",
      description="List of runs for this semester",
      required=False,
      schema=VOCABULARY_SCHEMA,
      default={
         "items": [
            {
               "token": "D01",
               "titles": {
                  "en": "D01"
               },
            },
         ]
      },
      missing_value={"items: []"},
   )'''

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
