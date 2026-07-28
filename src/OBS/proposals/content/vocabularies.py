from plone import api
from zope.interface import provider
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

def makeVocabFromList(l):
   'Given a list of strings, make simple vocab'
   voc = SimpleVocabulary([SimpleTerm(value=item, token=item, title=item) \
                          for item in l])
   return voc



yesno_list = ['Yes', 'No']

YESNO = makeVocabFromList(yesno_list)

NUMBERS = makeVocabFromList(['1','2','3','4','5'])

@provider(IVocabularyFactory)
def RUNS(context):
   runs = api.portal.get_registry_record("proposals.block_vocab")
   semester = api.portal.get_registry_record("proposals.semester")
   runs = [run.strip().split(',')[0] for run in runs.split('\n')]
   runs = [run+"_"+semester for run in runs]
   return makeVocabFromList(runs)

@provider(IVocabularyFactory)
def MOONPHASES(context):
   moons = api.portal.get_registry_record("proposals.moon_vocab")
   moons = [moon.strip() for moon in moons.split('\n')]
   return makeVocabFromList(moons)

@provider(IVocabularyFactory)
def TELESCOPES(context):
   telescopes = api.portal.get_registry_record("proposals.telescope_vocab")
   telescopes = [tel.strip() for tel in telescopes.split('\n')]
   return makeVocabFromList(telescopes)

@provider(IVocabularyFactory)
def INSTRUMENTS(context):
   instruments = api.portal.get_registry_record("proposals.instrument_vocab")
   instruments = [inst.strip() for inst in instruments.split('\n')]
   return makeVocabFromList(instruments)

@provider(IVocabularyFactory)
def SERVICE(context):
   services = api.portal.get_registry_record("proposals.service_vocab")
   services = [s.strip() for s in services.split('\n')]
   return makeVocabFromList(services)
