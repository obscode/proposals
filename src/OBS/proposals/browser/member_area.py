from plone import api
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView

class CustomMemberAreaView(BrowserView):

   def get_owner_profile(self):
      """Fetches profile properties for the owner of this specific folder."""
      folder_owner_id = self.context.getId()  # The folder ID is the username
      
      mtool = getToolByName(self.context, 'portal_membership')
      member = mtool.getMemberById(folder_owner_id)
      
      if not member:
         return None
          
      return {
         'username': folder_owner_id,
         'fullname': member.getProperty('fullname') or folder_owner_id,
         'email': member.getProperty('email'),
         'location': member.getProperty('location', ''),
         'description': member.getProperty('description', '')
      }

   def get_member_content(self):
      """Plone 6 safe method to fetch immediate children of this folder."""
      return api.content.find(
         context=self.context,
         depth=1,  # Only fetch immediate children, not sub-folders
         sort_on='modified',
         sort_order='reverse'
      )

   def addProp(self):
      return "window.location='"+self.context.absolute_url() + \
             "/++add++proposal" + "';"

