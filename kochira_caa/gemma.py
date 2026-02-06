"""
Ask Gemma Nye anything.

Allows the bot to query the Gemini API to generate text.
"""

import textwrap
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

@service.setup
def initialize_gemini_api(ctx):
    ctx.storage.gemini = genai.Client(
        api_key=ctx.config.api_key,
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(
                attempts=3,
                http_status_codes=[503],
            )
        )
    )
    ctx.storage.quota = QuotaState.zero()


def reset_daily_quota(ctx):
    if ctx.storage.quota.for_date != date.today():
        ctx.storage.quota = QuotaState.zero()

def record_quota_usage(ctx, tokens):
    ctx.storage.quota = ctx.storage.quota._replace(tokens_used=ctx.storage.quota.tokens_used + tokens)

def config_with_instructions(system_instruction, thinking_level):
    return types.GenerateContentConfig(
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        thinking_config=types.ThinkingConfig(thinking_level=thinking_level),
        system_instruction=system_instruction,
    )

def respond(ctx, text, config, print_tokens=None):
    reset_daily_quota(ctx)

    if ctx.config.token_quota > 0 and ctx.storage.quota.tokens_used > ctx.config.token_quota:
        ctx.respond("Daily token quota exceeded, try again tomorrow.")
        return

    try:
        response = ctx.storage.gemini.models.generate_content(
            model="gemini-3-flash-preview",
            config=config,
            contents=f"<{ctx.origin}> {text}",
        )
        record_quota_usage(ctx, response.usage_metadata.total_token_count)

        # I'm too cheap to spend extra tokens making sure this doesn't happen
        if response.text.startswith(ctx.origin):
            ctx.message(response.text)
        else:
            ctx.respond(response.text)

        if print_tokens:
            ctx.message(
                "prompt: {m.prompt_token_count}, thoughts: {m.thoughts_token_count}, "
                "total: {m.total_token_count}".format(m=response.usage_metadata)
            )
    except errors.APIError as e:
        ctx.respond(f"Gemini returned error: {e.code}: {e.message}")
    except Exception as e:
        ctx.respond(f"Unexpected error: {e}")

@service.command("big(?P<thinking>ger|gest)?(?P<verbose> verbose)? dog(?P<text>.+)")
def big_dog(ctx, text, thinking=None, verbose=None):
    """
    Big Dog

    Big Dog what is the meaning of the universe?
    """
    thinking_level = {'ger': 'medium', 'gest': 'high'}.get(thinking, 'minimal')
    instructions = textwrap.dedent(f"""
        You are an IRC bot user called Big Dog. You are chatting in {ctx.target}.
        A user has mentioned you in a message, asking for a response.
        The message is provided to you in the format <username> message.
        Generate only a response message, in no more than 3 lines, preferably 1.
    """)

    respond(ctx, text, config=config_with_instructions(instructions, thinking_level), print_tokens=verbose)

@service.command("haro(?P<chan>-chan)?(?P<kun>-kun)?(?P<verbose>!)? (?P<text>.+)")
def haro(ctx, text, chan='', kun='', verbose=None):
    """
    Haro

    Haro are Gundams bad?
    """
    thinking = 0 + (1 if chan else 0) + (1 if kun else 0)
    thinking_level = ['minimal', 'low', 'medium'][thinking]
    instructions = textwrap.dedent(f"""
        You are a helpful IRC bot user called Haro{chan}{kun}. You are chatting in {ctx.target}.
        A user has mentioned you in a message, asking for a response.
        The message is provided to you in the format <username> message.
        Generate only a response message, in no more than 3 lines, preferably 1.
    """)

    respond(ctx, text, config=config_with_instructions(instructions, thinking_level), print_tokens=verbose)

@service.command("!tokenusage")
def token_usage(ctx):
    ctx.respond(ctx.storage.quota)

