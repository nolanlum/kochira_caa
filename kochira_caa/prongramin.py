"""
Resources for the prongramin.

Helps you get to work more on time, probably.
"""

import codecs
import json
from datetime import datetime, timezone

import humanize
import requests

from kochira import config
from kochira.service import Service, Config

service = Service(__name__, __doc__)

@service.config
class Config(Config):
    api_key = config.Field(doc="511.org API key.")

def next_n_times(ctx):
    resp = json.loads(codecs.decode(requests.get(
        "https://api.511.org/transit/StopMonitoring",
        params={
            'api_key': ctx.config.api_key,
            'format': 'json',
            'agency': 'SF',
            'stopCode': 16992,
        },
    ).content, 'utf-8-sig'))

    planned_n_stop_times = sorted([
        datetime.strptime(mvj['MonitoredCall']['AimedArrivalTime'], '%Y-%m-%dT%H:%M:%SZ')
        for mvj in [
            msv['MonitoredVehicleJourney']
            for msv in resp['ServiceDelivery']['StopMonitoringDelivery']['MonitoredStopVisit']
        ]
        if mvj['LineRef'] == 'N'
    ])
    planned_n_stop_minutes = [
        str(int((stop_time - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds() // 60))
        for stop_time in planned_n_stop_times
    ]

    return planned_n_stop_minutes

def gobike_infostring():
    resp = requests.get("https://gbfs.fordgobike.com/gbfs/en/station_status.json").json()
    gobike_stations = {
        int(station['station_id']): station for station in resp['data']['stations']
    }

    return (
        "Spear@Folsom: {stations[24][num_bikes_available]}/{stations[24][num_ebikes_available]}e"
        " || "
        "Embarcadero@Steuart: {stations[23][num_bikes_available]}/{stations[23][num_ebikes_available]}e"
        " -> "
        "Berry@4th: {stations[81][num_docks_available]} docks"
    ).format(
        stations=gobike_stations
    )

@service.command(r"I'?m late (?:for|to) work", mention=True, priority=1)
def transit_times(ctx):
    """
    Get Transit Times

    Gets bikeshare information so you can make it to standup.
    """
    ctx.respond("Next inbound N in {next_n} minutes. Bikes: {bike_info}".format(
        next_n=", ".join(next_n_times(ctx)),
        bike_info=gobike_infostring(),
    ))
