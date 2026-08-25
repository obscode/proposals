from logging import getLogger
from plone import api
logger = getLogger("OBS.proposals")

def upgrade_types(context):
    """Reload typeinfo ste to apply new content type fields."""
    setup = context.portal_setup
    setup.runImportStepFromProfile("OBS.proposals:default", "typeinfo")
    logger.info("Reloaded typeinfo to apply new content type fields.")

def upgrade_phone(context):
    # Reload type definitions from profiles/default/types/...
    setup = context.portal_setup
    setup.runImportStepFromProfile("OBS.proposals:default", "typeinfo")
    
    # Clean up old telephoneattributes from existing content objects in the ZODB
    portal = api.portal.get()
    catalog = portal.portal_catalog

    brains = catalog(portal_type='proposal')
    for brain in brains:
        obj = brain.getObject()
        if hasattr(obj, 'teleophone'):
            delattr(obj, 'telephone')
            obj._p_changed = True
        if not hasattr(obj, 'epoch2'):
            obj.epoch2 = None
            obj._p_changed = True

    brains = catalog(portal_type='TBDproposal')
    for brain in brains:
        obj = brain.getObject()
        if hasattr(obj, 'teleophone'):
            delattr(obj, 'telephone')
            obj._p_changed = True

                
def upgrade_hours(context):
    # Reload type definitions from profiles/default/types/...
    setup = context.portal_setup
    setup.runImportStepFromProfile("OBS.proposals:default", "typeinfo")
    
    # Clean up old telephoneattributes from existing content objects in the ZODB
    portal = api.portal.get()
    catalog = portal.portal_catalog

    brains = catalog(portal_type='proposal')
    for brain in brains:
        obj = brain.getObject()
        if obj.too:
            for too in obj.too:
                try:
                    too.hours = float(too.hours)
                except:
                    too.hours = 0.0
            obj._p_changed = True
            

                
