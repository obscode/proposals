from plone import api
from plone.app.contenttypes.interfaces import IFolder

def set_member_area_default_view(obj, event):
   """Automatically forces the custom view layout when a member folder is created."""
   # Safety Check: Ensure we are dealing with a Folder content type
   if not IFolder.providedBy(obj):
      return

   # Target checking: Ensure its parent folder is exactly "Members"
   parent = obj.aq_parent
   if parent and parent.getId() == 'Members':
      # Force the custom browser view name as the default layout handler
      obj.setLayout('custom-member-area-view')

