from plone import api
from Products.CMFPlone.interfaces import IRedirectAfterLogin
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface

@implementer(IRedirectAfterLogin)
@adapter(Interface, Interface)
class ForceHomeFolderRedirect:
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, came_from=None, is_initial_login=False):
        # Always check for the home folder first, completely ignoring root came_from variables
        mtool = api.portal.get_tool(name="portal_membership")
        portal_id = api.portal.get().getId()
        home_folder = mtool.getHomeFolder()
        if home_folder:
            tail = home_folder.absolute_url().split('/')[-1]
            path = f"/{portal_id}/Members/{tail}"
        
            return path
            
        # Fall back to site root if no folder exists
        return api.portal.get().absolute_url()
