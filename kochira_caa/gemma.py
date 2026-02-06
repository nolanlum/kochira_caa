"""
Ask Gemma Nye anything.

Allows the bot to query the Gemini API to generate text.
"""

from google import genai
from google.genai import errors, types

from kochira import config
from kochira.service import Service, Config

service = Service(__name__, __doc__)

@service.config
class Config(Config):
    api_key = config.Field(doc="Gemini API key.")


@service.setup
def initialize_gemini_api(ctx):
    ctx.storage.gemini = genai.Client(api_key=ctx.config.api_key)


@service.command("big dog (?P<text>.+)")
def big_dog(ctx, text):
    """
    Big Dog

    Big Dog what is the meaning of the universe?
    """
    try:
        response = ctx.storage.gemini.models.generate_content(
            model="gemini-3-flash-preview",
            config=types.GenerateContentConfig(
                system_instruction="You are an IRC bot user called Big Dog. "
                        f"You are chatting in {ctx.target}. "
                        "A user has mentioned you in a message, asking for a response. "
                        "The message is provided to you in the format <username> message. "
                        "Generate only a response message, in no more than 3 lines, preferably 1."
            ),
            contents=f"<{ctx.origin}> {text}",
        )
        ctx.respond(response.text)
    except errors.APIError as e:
        ctx.respond(f"Gemini returned error: {e.code}: {e.message}")
    except Exception as e:
        ctx.respond(f"Unexpected error: {e}")

