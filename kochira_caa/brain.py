"""
Artificial (un)intelligence.

Allows the bot to reply whenever its nickname is mentioned.
"""

import re

from kochira import config
from kochira.service import Service, background, Config
from cobe.brain import Brain
from cobe.scoring import Scorer, ScorerGroup, LengthScorer

service = Service(__name__, __doc__)

@service.config
class Config(Config):
    brain_file = config.Field(doc="Location to store the brain in.", default="brain.db")

# cobe's ScorerGroup.score has a bug, so rather than address the problem
# directly, let's monkeypatch it.
def scorergroup_score(self, reply):
    # normalize to 0..1
    score = 0.
    for weight, scorer in self.scorers:
        s = scorer.score(reply)

        # make sure s is in our accepted range
        assert 0.0 <= s <= 1.0

        if weight < 0.0:
            s = 1.0 - s

        score += abs(weight) * s

    return score / self.total_weight

class BalancedScorer(Scorer):
    def score(self, reply):
        text = reply.to_text()
        quotes = sum([1 for x in text if x == '"'])
        return 0.5 if quotes % 2 else 1.0

def load_brain(ctx):
    ctx.storage.brains[ctx.config.brain_file] = Brain(ctx.config.brain_file)

    scorer = ctx.storage.brains[ctx.config.brain_file].scorer
    scorer.score = scorergroup_score.__get__(scorer, ScorerGroup)
    scorer.add_scorer(1.0, LengthScorer())
    scorer.add_scorer(1.0, BalancedScorer())

@service.setup
def load_default_brain(ctx):
    ctx.storage.brains = {}
    load_brain(ctx)
    ctx.storage.brain = ctx.storage.brains[ctx.config.brain_file]

@service.shutdown
def unload_brain(ctx):
    for brain in ctx.storage.brains.values():
        brain.graph.close()

def get_brain(ctx):
    if ctx.config.brain_file not in ctx.storage.brains:
        load_brain(ctx)
    return ctx.storage.brains[ctx.config.brain_file]

@service.hook("channel_message", priority=-9999)
@background
def reply_and_learn(ctx, target, origin, message):
    front, _, rest = message.partition(" ")

    mention = False
    reply = False

    if front.strip(",:").lower() == ctx.client.nickname.lower():
        mention = True
        reply = True
        message = rest

    message = message.strip()
    brain = get_brain(ctx)

    if re.search(r"\b{}\b".format(re.escape(ctx.client.nickname)), message, re.I) is not None:
        reply = True

    if reply:
        reply_message = brain.reply(message)

        if mention:
            ctx.respond(reply_message)
        else:
            ctx.message(reply_message)

    if message:
        brain.learn(message)

@service.provides("brain")
def reply(ctx, message, *args, **kwargs):
    """
    Reply to a message with the default brain.

    Passes any additional arguments to the brain's .reply function.
    """
    return service.binding_for(ctx.bot).storage.brain.reply(message, *args, **kwargs)

