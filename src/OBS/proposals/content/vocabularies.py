from plone import api
from zope.interface import provider
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

def makeVocabFromList(l):
   'Given a list of strings, make simple vocab'
   voc = SimpleVocabulary([SimpleTerm(value=item, title=item) \
                          for item in l])
   return voc



yesno_list = ['Yes', 'No']

YESNO = makeVocabFromList(yesno_list)

@provider(IVocabularyFactory)
def RUNS(context):
   runs = api.portal.get_registry_record("proposals.run_vocab")
   return makeVocabFromList(runs.split('\n'))

@provider(IVocabularyFactory)
def MOONPHASES(context):
   moons = api.portal.get_registry_record("proposals.moon_vocab")
   return makeVocabFromList(moons.split('\n'))

@provider(IVocabularyFactory)
def TELESCOPES(context):
   telescopes = api.portal.get_registry_record("proposals.telescope_vocab")
   return (makeVocabFromList(telescopes.split('\n')))

@provider(IVocabularyFactory)
def INSTRUMENTS(context):
   instruments = api.portal.get_registry_record("proposals.instrument_vocab")
   return makeVocabFromList(instruments.split('\n'))

@provider(IVocabularyFactory)
def SERVICE(context):
   services = api.portal.get_registry_record("proposals.service_vocab")
   return makeVocabFromList(services.split('\n'))