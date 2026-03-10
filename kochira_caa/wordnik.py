"""
Wordnik API.

For when you want to do terrible things with words.
"""

from kochira import config
from kochira.service import Service, Config

service = Service(__name__, __doc__)

@service.config
class Config(Config):
    api_key = config.Field(doc="Wordnik API key")

@service.setup
def make_api(ctx):
    async def wordnik_get_word(part_of_speech, min_corpus_count=1000):
        r = await ctx.bot.http.get("https://api.wordnik.com/v4/words.json/randomWord", params={
            'hasDictionaryDef': 'true',
            'includePartOfSpeech': part_of_speech,
            'minCorpusCount': min_corpus_count,
            'minLength': 5,
            'api_key': ctx.config.api_key,
        })
        return r.json()['word']

    ctx.storage.get_word = wordnik_get_word

@service.command(r"^:amatsukaze:$")
async def amatsukaze(ctx):
    """
    :amatsukaze:

    That's surely very advanced for computers.
    """
    adjective = await ctx.storage.get_word('adjective')
    noun = await ctx.storage.get_word('noun')

    await ctx.message("That's surely very {adjective} for {noun}.".format(
        adjective=adjective,
        noun=noun,
    ))

@service.command(r"^:szi:$")
async def szi(ctx):
    """
    :szi:

    <szi> Choose this, whips out axiom of choice
    """
    verb = await ctx.storage.get_word('verb-transitive')
    noun = await ctx.storage.get_word('noun')

    await ctx.message("<szi> {verb} this, whips out {noun}".format(
        verb=verb,
        noun=noun,
    ))

@service.command(r"^(\w+ )((on|onto|in|at|out|for|to|by|off|about) )?this$")
async def szi_partial(ctx):
    """
    autism on this

    <szi> bring this <szi> whips out your deliverance from a startup that won't make money
    """
    noun = await ctx.storage.get_word('noun')

    await ctx.message("whips out {noun}".format(
        noun=noun
    ))
