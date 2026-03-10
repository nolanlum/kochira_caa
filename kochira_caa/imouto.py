"""
Say hello to imouto.

See the world from kedo's point of view.
"""
from kochira.service import Service
from nltk.stem.snowball import SnowballStemmer
import re

stemmer = SnowballStemmer('english')

service = Service(__name__, __doc__)

def case_corrected_imouto(word, imouto):
    if all(c.isupper() for c in word):
        return imouto.upper()

    if word.capitalize() == word:
        return imouto.capitalize()

    return imouto

def imouto_factory(imouto):
    def stemmed_imouto(match):
        word = match.group(0)
        word_stem = stemmer.stem(word)
        if word != word_stem and word.startswith(word_stem):
            return case_corrected_imouto(word, imouto) + word[len(word_stem):]
        else:
            return case_corrected_imouto(word, imouto)
    return stemmed_imouto

@service.command("!imouto(?: (?P<text>.+))?")
def imouto(ctx, text=None):
    """
    Imouto.

    Imouto-ify some text.
    """
    if text is None:
        if len(ctx.client.backlogs[ctx.target]) == 1:
            return

        _, text = ctx.client.backlogs[ctx.target][1]

    text = re.sub(r"\w\w\w\w\w+", imouto_factory('imouto'), text)
    ctx.message(text)


@service.command("!kimchi(?: (?P<text>.+))?")
def kimchi(ctx, text=None):
    """
    Korean Imouto.

    Imouto-ify some Korean.
    """
    if text is None:
        if len(ctx.client.backlogs[ctx.target]) == 1:
            return

        _, text = ctx.client.backlogs[ctx.target][1]

    text = re.sub(r"\w\w\w\w\w+", imouto_factory('nida'), text)
    ctx.message(text)
