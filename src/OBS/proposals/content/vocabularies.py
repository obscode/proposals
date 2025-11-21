from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

def makeVocabFromList(l):
   'Given a list of strings, make simple vocab'
   voc = SimpleVocabulary([SimpleTerm(value=item, title=item) \
                          for item in l])
   return voc

yesno_list = ['Yes', 'No']
block_list = [
   '2026_D01',
   '2026_L01',
   '2026_D02',
   '2026_L02',
   '2026_D03',
   '2026_L03',
   '2026_D04',
   '2026_L04',
   '2026_D05',
   '2026_L05',
   '2026_D06',
   '2026_L06',
]
moon_list = ['|{}|'.format(i) for i in range(14,0,-1)]
moon_list += ['{:+d}'.format(i) for i in range(-14, 15)]

tel_list = ['Baade', 'Clay', 'Swope']

inst_list = [
'Baade:IMACS:f/2',
'Baade:IMACS:f/4',
'Baade:IMACS:GISMO',
'Baade:IMACS:Rosie-IFU',
'Baade:FourStar',
'Baade:FIRE',
'Baade:MagE',
'Baade:LLAMAS',
'Clay:MIKE',
'Clay:LDSS3-C',
'Clay:PFS',
'Clay:M2FS',
'Clay:IFU-M',
'Clay:WINERED',
'Clay:MegaCam',
'Clay:MagAO-X',
'Clay:Lightspeed',
'Swope:Direct',
]

YESNO = makeVocabFromList(yesno_list)
BLOCKNAMES = makeVocabFromList(block_list)
MOONPHASES = makeVocabFromList(moon_list)
TELESCOPES = makeVocabFromList(tel_list)
INSTRUMENTS = makeVocabFromList(inst_list)