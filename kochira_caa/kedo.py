"""
kedo module.

Allows mortals to learn from the tome of kedo.
"""

import os
import re

from collections import defaultdict
from random import choice, randint, random

from peewee import CharField, fn
from tornado.web import RequestHandler, Application

from kochira.auth import requires_permission
from kochira.db import Model
from kochira.service import Service

service = Service(__name__, __doc__)

class KedoBit(Model):
    topic = CharField(255)
    knowledge = CharField(450)

    class Meta:
        indexes = (
            (("topic",), False),
        )

@service.setup
def initialize_model(bot):
    KedoBit.create_table(True)

@service.command(r"kedo on (?P<topic>[^:]+)$", mention=True)
@service.command(r"!kedo (?P<topic>.+)$")
def kedo(ctx, topic):
    """
    kedo

    Query the tome of kedo and return the results.
    """
    if not KedoBit.select().where(KedoBit.topic == topic).exists():
        ctx.respond("kedo hasn't said anything about {topic} yet. poop.".format(
            topic=topic
        ))
        return

    ctx.message("\x02kedo on {topic}:\x02 {bit.knowledge}".format(
        topic=topic,
        bit=KedoBit.select().where(KedoBit.topic == topic).order_by(fn.Random()).limit(1)[0]))

@service.command(r"kedo on (?P<topic>.*\w)\s*: (?P<knowledge>.+)$", mention=True)
@service.command(r"!kedolearn (?P<topic>.+) : (?P<knowledge>.+)$")
@requires_permission("kedo")
def kedo_learn(ctx, topic, knowledge):
    """
    kedolearn

    Instill new knowledge into the tome of kedo. Multiple entries on the
    same topic are allowed.
    """
    KedoBit.create(topic=topic, knowledge=knowledge).save()

    ctx.respond("kedo now knows about \x02{topic}\x02!".format(topic=topic))

@service.command(r"kedo no longer speaks of (?P<topic>.+)$", mention=True)
@service.command(r"!kedoforget (?P<topic>.+)$")
@requires_permission("kedo")
def kedo_forget(ctx, topic):
    """
    kedoforget

    Erase gospel from the tome of kedo. If multiple entries had been stored under
    the same topic, they are all removed.
    """
    KedoBit.delete().where(KedoBit.topic == topic).execute()

    ctx.respond("kedo no longer knows about \x02{topic}\x02.".format(topic=topic))

@service.command(r"what does kedo know about\??$", mention=True)
@service.command(r"!kedo$")
def kedolist(ctx):
    """
    kedolist

    List all scripture in the book of kedo.
    """
    ctx.message("\x02kedo knows about:\x02 {things}".format(
        things=", ".join([x.topic for x in KedoBit.select().group_by(KedoBit.topic)])
    ))


class IndexHandler(RequestHandler):
    def get(self):
        kedos = defaultdict(list)
        for bit in KedoBit.select():
            kedos[bit.topic].append(bit.knowledge)

        self.render("../../../../../../kochira_caa/kochira_caa/templates/kedo.html",
                    kedos=kedos)


def make_application(settings):
    return Application([
        (r"/", IndexHandler)
    ], **settings)


@service.hook("services.net.webserver")
def webserver_config(ctx):
    return {
        "name": "kedo.txt",
        "title": "kedo.txt",
        "application_factory": make_application
    }


@service.command(r".*\[in\].*")
def lnkd_simulator_2016(ctx):
    """
    LNKD simulator 2016

    Accurate simulation of LNKD.
    """
    ctx.respond("\x02LNKD\x02 down {percent}%!".format(
        percent=randint(15, 45)
    ))

@service.command(r"!nichi(?: (?P<text>.+))?")
def nichi(ctx, text=None):
    """
    ,,,n,ic,,,hi
    """
    if text is None:
        if len(ctx.client.backlogs[ctx.target]) == 1:
            return

        _, text = ctx.client.backlogs[ctx.target][1]

    new_text = ''
    for c in text:
        if random() < 0.4:
            if random() < 0.3:
                new_text += ',' * randint(3,6)
            else:
                new_text += ',' * randint(1,2)
        new_text += c
    ctx.message(new_text)

@service.command(r"!spongebob(?: (?P<text>.+))?")
def spongebob(ctx, text=None):
    """
    ReCrEatIonaL dRugS And heAVY aLcoHOl CONsUMpTIoN HAVe bEEn nORmal aMOng YOUNg pEOPle THE laST haLf cenTUry
    """
    if text is None:
        if len(ctx.client.backlogs[ctx.target]) == 1:
            return

        _, text = ctx.client.backlogs[ctx.target][1]

    new_text = ''
    run_length = 1
    current_transform = str.upper if random() < 0.5 else str.lower
    for c in text:
        new_text += current_transform(c)

        if random() > 0.75 ** (run_length * 1.5):
            current_transform = str.upper if current_transform is str.lower else str.lower
            run_length = 1
        else:
            run_length += 1

    ctx.message(new_text)

