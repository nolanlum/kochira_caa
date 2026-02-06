"""
METAR/TAF fetcher.

For SZI and SZI accessories.
"""

import requests

from kochira import config
from kochira.service import Service, Config

service = Service(__name__, __doc__)


@service.config
class Config(Config):
    api_key = config.Field(doc="AVWX app token.")


@service.command(r"!metar (?P<location>[A-Z0-9]{4})$")
def metar(ctx, location):
    """
    METAR

    Get the METAR for a specific station by ICAO ident.
    """
    response = requests.get(
        "https://avwx.rest/api/metar/{location}".format(location=location),
        params={
            'token': ctx.config.api_key,
            'format': 'json',
            'onfail': 'cache',
        },
    ).json()

    if 'error' in response:
        ctx.respond(response['error'])
        return

    ctx.respond(response['sanitized'])

