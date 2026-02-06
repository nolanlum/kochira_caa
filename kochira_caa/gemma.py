"""
Ask Gemma Nye anything.

Allows the bot to query the Gemini API to generate text.
"""

from datetime import date
from typing import NamedTuple

from google import genai
from google.genai import errors, types

from kochira import config
from kochira.service import Service, Config


class QuotaState(NamedTuple):
    for_date: date
    tokens_used: int

    @staticmethod
    def zero():
        return QuotaState(date.today(), 0)


service = Service(__name__, __doc__)

@service.config
class Config(Config):
    api_key = config.Field(doc="Gemini API key.")
    token_quota = config.Field(doc="Allowable token usage per day.", default=-1)


def reset_daily_quota(ctx):
    if ctx.storage.quota.for_date != date.today():
        ctx.storage.quota = QuotaState.zero()


def record_quota_usage(ctx, tokens):
    ctx.storage.quota = ctx.storage.quota._replace(tokens_used=ctx.storage.quota.tokens_used + tokens)


@service.setup
def initialize_gemini_api(ctx):
    ctx.storage.gemini = genai.Client(api_key=ctx.config.api_key)
    ctx.storage.quota = QuotaState.zero()


@service.command("big(?P<thinking>ger|gest)?(?P<verbose> verbose)? dog(?P<text>.+)")
def big_dog(ctx, text, thinking=None, verbose=None):
    """
    Big Dog

    Big Dog what is the meaning of the universe?
    """
    reset_daily_quota(ctx)

    if ctx.config.token_quota > 0 and ctx.storage.quota.tokens_used > ctx.config.token_quota:
        ctx.respond("Daily token quota exceeded, try again tomorrow.")
        return

    thinking_level = {'ger': 'medium', 'gest': 'high'}.get(thinking, 'minimal')

    try:
        response = ctx.storage.gemini.models.generate_content(
            model="gemini-3-flash-preview",
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_level=thinking_level),
                system_instruction="You are an IRC bot user called Big Dog. "
                        f"You are chatting in {ctx.target}. "
                        "A user has mentioned you in a message, asking for a response. "
                        "The message is provided to you in the format <username> message. "
                        "Generate only a response message, in no more than 3 lines, preferably 1."
            ),
            contents=f"<{ctx.origin}> {text}",
        )
        record_quota_usage(ctx, response.usage_metadata.total_token_count)

        # I'm too cheap to spend extra tokens making sure this doesn't happen
        if response.text.startswith(ctx.origin):
            ctx.message(response.text)
        else:
            ctx.respond(response.text)

        if verbose:
            ctx.message(
                "prompt: {m.prompt_token_count}, thoughts: {m.thoughts_token_count}, "
                "total: {m.total_token_count}".format(m=response.usage_metadata)
            )
    except errors.APIError as e:
        ctx.respond(f"Gemini returned error: {e.code}: {e.message}")
    except Exception as e:
        ctx.respond(f"Unexpected error: {e}")

