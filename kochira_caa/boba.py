"""
Imma let you finish
"""

from kochira.service import Service
import random
import time

FAGETRY = "I'd just like to interject for a moment. What you're referring to as boba, is in fact, pearl milk tea, or as I've recently taken to calling it, PMT plus boba."
REVERSE_FAGETRY = "Did you mean boba?"

service = Service(__name__, __doc__)

@service.hook("channel_message", priority=-9999)
def boba(ctx, target, origin, message):
    if "boba" in message and random.random() <= 0.4:
        time.sleep(random.randint(1, 4))
        ctx.message(FAGETRY)
    elif "pmt" in message and random.random() <= 0.8:
        time.sleep(random.randint(1, 2))
        ctx.message(REVERSE_FAGETRY)
