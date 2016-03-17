"""
Twitter timeline follower.

Broadcasts a Twitter user's timeline into IRC. Provides tweeting capabilities as well as
Markov-chain text generation with a compatible Brain.
"""

import time
import twitter

from threading import Thread
from twitter import Twitter, TwitterStream, TwitterHTTPError
from kochira import config
from kochira.service import Service, Config
from kochira.auth import requires_permission

TRUNCATED_MAX = 134  # 140 - '...' - '...'

service = Service(__name__, __doc__)

@service.config
class Config(Config):
    class OAuth(config.Config):
        consumer_key = config.Field(doc="Twitter API consumer key.")
        consumer_secret = config.Field(doc="Twitter API consumer secret.")
        token = config.Field(doc="Twitter API OAuth token.")
        token_secret = config.Field(doc="Twitter API OAuth token secret.")
    class Channel(config.Config):
        client = config.Field(doc="The client to announce on.")
        channel = config.Field(doc="The channel to announce on.")

    oauth = config.Field(doc="OAuth parameters.",
                         type=OAuth)
    announce = config.Field(doc="Places to announce tweets.",
                         type=config.Many(Channel))

@service.setup
def make_twitter(ctx):
    ctx.storage.api = Twitter(auth=twitter.OAuth(**ctx.config.oauth._fields))
    ctx.storage.active = True
    ctx.storage.ids = {}
    ctx.storage.last = None
    ctx.storage.stream = Thread(target=_follow_userstream, args=(ctx,), daemon=True)
    ctx.storage.stream.start()

@service.shutdown
def kill_twitter(ctx):
    ctx.storage.active = False
    ctx.storage.stream.join()

@service.command(r"!asadayo$")
@service.command(r"!twitter$")
@requires_permission("tweet")
def restart_twitter(ctx):
    """
    Restart the twitter stream because Twitter sucks.
    """
    ctx.storage.active = False
    ctx.storage.stream.join()
    ctx.storage.active = True
    ctx.storage.stream = Thread(target=_follow_userstream, args=(ctx,), daemon=True)
    ctx.storage.stream.start()

@service.command(r"tweet (?P<message>.+)$", mention=True)
@service.command(r"!tweet (?P<message>.+)$")
@requires_permission("tweet")
def tweet(ctx, message):
    """
    Tweet

    Tweet the given text.
    """
    
    if len(message) > TRUNCATED_MAX:
        messages = [message[:TRUNCATED_MAX] + '...']
        for i in xrange(len(message) / TRUNCATED_MAX):
            messages.append('...' + message[TRUNCATED_MAX * i : TRUNCATED_MAX * (i + 1)] + '...')
        messages.append('...' + message[TRUNCATED_MAX * (i + 1):])
    else:
        messages = [message]
    try:
        for message in messages:
            ctx.storage.api.statuses.update(status=message)
    except TwitterHTTPError as e:
        for error in e.response_data['errors']:
            ctx.respond("Twitter returned error: {}".format(error['message']))

@service.command(r"retweet (?P<id>[0-9]+|last)$", mention=True)
@service.command(r"!(?:rt|retweet) (?P<id>[0-9]+|last)$")
@requires_permission("tweet")
def retweet(ctx, id):
    """
    Retweet

    Retweets the specified tweet.
    """
    id = parse_tweet_id(ctx, id)
    if id is None:
        return

    try:
        ctx.storage.api.statuses.retweet(id=id)
    except TwitterHTTPError as e:
        for error in e.response_data['errors']:
            ctx.respond("Twitter returned error: {}".format(error['message']))

@service.command(r"reply to (?P<id>[0-9]+|last)(?: with (?P<message>.+))?$", mention=True)
@service.command(r"!reply (?P<id>[0-9]+|last)(?: (?P<message>.+))?$")
@requires_permission("tweet")
def reply(ctx, id, message=None):
    """
    Reply

    Reply to the given tweet. Automatically prepends the appropriate @mention. If no message is given,
    attemps to search for a usable Brain service and uses it to generate a suitable reply.
    """
    api = ctx.storage.api

    id = parse_tweet_id(ctx, id)
    if id is None:
        return

    try:
        tweet = api.statuses.show(id=id)
    except TwitterHTTPError:
        ctx.respond("Tweet {} does not exist!".format(id))
        return

    if message is None:
        try:
            brain = ctx.provider_for("brain")
        except KeyError:
            ctx.respond("No tweet provided and no Brain could be found!")
            return

        text = tweet["text"]
        user = "@{} ".format(tweet["user"]["screen_name"])
        message = user + brain(text, max_len=140-len(user))
    else:
        message = "@{} {}".format(tweet["user"]["screen_name"], message)
        
    if len(message) > TRUNCATED_MAX:
        messages = [message[:TRUNCATED_MAX] + '...']
        for i in xrange(len(message) / TRUNCATED_MAX):
            messages.append('...' + message[TRUNCATED_MAX * i : TRUNCATED_MAX * (i + 1)] + '...')
        messages.append('...' + message[TRUNCATED_MAX * (i + 1):])
    else:
        messages = [message]
    try:
        for message in messages:
            api.statuses.update(status=message, in_reply_to_status_id=id)
    except TwitterHTTPError as e:
        for error in e.response_data['errors']:
            ctx.respond("Twitter returned error: {}".format(error['message']))

@service.command(r"follow @?(?P<user>[0-9a-z_]+)", mention=True)
@requires_permission("tweet")
def follow(ctx, user):
    """
    Follow

    Follows a user.
    """
    api = ctx.storage.api
    try:
        api.friendships.create(screen_name=user, follow=True)
        ctx.respond("Now following @{}.".format(user))
    except TwitterHTTPError as e:
        for error in e.response_data['errors']:
            ctx.respond("Twitter returned error: {}".format(error['message']))

@service.command(r"(unfollow|stop following) @?(?P<user>[0-9a-z_]+)", mention=True)
@requires_permission("tweet")
def unfollow(ctx, user):
    """
    Unfollow

    Unfollows a user.
    """
    api = ctx.storage.api
    try:
        api.friendships.destroy(screen_name=user)
        ctx.respond("No longer following @{}.".format(user))
    except TwitterHTTPError as e:
        for error in e.response_data['errors']:
            ctx.respond("Twitter returned error: {}".format(error['message']))

def memorize_id(ctx, id):
    ids = ctx.storage.ids
    suffix = id[-2:]
    if not suffix in ids:
        ids[suffix] = set()
    ids[suffix].add(id)

def parse_tweet_id(ctx, id):
    """
    Attempt to resolve a tweet ID.
    """
    last = ctx.storage.last
    ids = ctx.storage.ids

    if id == "last":
        if last is not None:
            return last["id_str"]

        ctx.respond("I haven't seen any tweets yet!")
        return None

    if len(id) < 2:
        ctx.respond("Enter at least 2 digits!")
        return None

    suffix = id[-2:]
    if suffix in ids:
        matching = [x for x in ids[suffix] if x.endswith(id)]
        # Return error if ambiguous, found ID if unambiguous, and the original
        # string if not found. Just in case.
        if len(matching) > 1:
            ctx.respond("ID could not unambiguously be resolved! Try a longer prefix.")
            return None
        elif len(matching) == 1:
            return matching[0]

    return id

def _follow_userstream(ctx):
    o = ctx.config.oauth._fields
    stream = TwitterStream(auth=twitter.OAuth(**o), domain="userstream.twitter.com", block=False)

    reconnect_seconds = [2, 10, 60, 300]
    reconnect_tries = 0

    while ctx.storage.active:
        try:
            for msg in stream.user():
                if msg is not None:
                    service.logger.debug(str(msg))

                    # Twitter signals start of stream with the "friends" message.
                    if 'friends' in msg:
                        _announce(ctx, "\x02twitter:\x02 This channel is now streaming Twitter in real-time.")
                        reconnect_tries = 0
                    elif 'text' in msg and 'user' in msg:
                        memorize_id(ctx, msg["id_str"])
                        ctx.storage.last = msg

                        url_format = "(https://twitter.com/{0[user][screen_name]}/status/{0[id_str]})"
                        if 'retweeted_status' in msg:
                            text = "\x02[@{0[user][screen_name]} RT @{0[retweeted_status][user][screen_name]}]\x02 {0[retweeted_status][text]} " + url_format
                        else:
                            text = "\x02[@{0[user][screen_name]}]\x02 {0[text]} " + url_format

                        _announce(ctx, text.format(msg))
                else:
                    time.sleep(.5)

                if not ctx.storage.active:
                    return

            _announce(ctx, "\x02twitter:\x02 Twitter userstream connection lost! Waiting {time} seconds to reconnect.".format(
                            time=reconnect_seconds[reconnect_tries]
                        ))
        except Exception as e:
            _announce(ctx, "\x02twitter:\x02 Exception thrown while following userstream! Waiting {time} seconds to reconnect.".format(
                            time=reconnect_seconds[reconnect_tries]
                        ))
            _announce(ctx, "↳ {name}: {info}".format(
                            name=e.__class__.__name__,
                            info=str(e)
                        ))

        time.sleep(reconnect_seconds[reconnect_tries])
        reconnect_tries += 1

def _announce(ctx, text):
    text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')

    for announce in ctx.config.announce:
        if announce.client in ctx.bot.clients:
            ctx.bot.clients[announce.client].message(announce.channel, text)

