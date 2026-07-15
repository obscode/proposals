from logging import getLogger
logger = getLogger("OBS.proposals")

def upgrade_types(context):
    """Reload typeinfo ste to apply new content type fields."""
    setup = context.portal_setup
    setup.runImportStepFromProfile("OBS.proposals:default", "typeinfo")
    logger.info("Reloaded typeinfo to apply new content type fields.")