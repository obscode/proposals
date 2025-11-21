from plone import schema
from plone.autoform import directives
from plone.dexterity.content import Container
from plone.schema.email import Email
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.browser.radio import RadioFieldWidget
from zope.interface import implementer
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class IProposalFolder(model.Schema):
    """Dexterity-Schema for Proposal"""

    semester = schema.TextLine(
        title='Semester (e.g., 2025B, 2026A, ...',
        description='The proposals semester',
        required=True,
    )
    is_tbd = schema.Bool(
        title='TBD Proposals',
        description='Select if proposals are for TBD time, so shorter PDFs',
        required=True
    )


@implementer(IProposalFolder)
class ProposalFolder(Container):
    """Talk instance class"""
