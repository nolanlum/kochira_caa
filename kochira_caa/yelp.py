"""
Yelp generator plugin.

Fake service that extends the generator service to provide
typical Yelp imports.
"""
from functools import partial

from kochira.service import Service
from kochira.services.textproc.generators import PickFrom, WrapWith, RandomInt, run_generator, bind_generator

service = Service(__name__, __doc__)


@service.shutdown
def reload_generators(ctx):
    if 'kochira.services.textproc.generators' in ctx.bot.services:
        ctx.bot.load_service(".textproc.generators", reload=True)


yelp = partial(run_generator,
               WrapWith(1,
                        "from {}",
                        PickFrom(1, [
                            "core",
                            "cmds",
                            "util",
                        ])
               ),
               PickFrom(RandomInt(2, 5), [
                   WrapWith(1,
                            PickFrom(1, [
                                ".{}",
                                PickFrom(1, [
                                    ".ad_{}",
                                    ".business_{}",
                                    ".biz_{}",
                                    ".photo_{}",
                                    ".user_{}",
                                ]),
                            ]),
                            PickFrom(1, [
                                "common",
                                "component",
                                "lib",
                                "models",
                                "presentation",
                                "util",
                            ])
                   ),
               ]),
               WrapWith(1,
                        " import {}",
                        PickFrom(1, [
                            [
                                PickFrom(1, [
                                    "",
                                    "_",
                                ]),
                                PickFrom(1, [
                                    "maybe_",
                                    "cached_",
                                ]),
                                PickFrom(1, [
                                    "get_",
                                    "set_",
                                    "check_",
                                    "create_",
                                    "load_",
                                    "log_",
                                    "is_",
                                    "format_",
                                    "render_",
                                ]),
                                PickFrom(1, [
                                    "",
                                    "active_",
                                    "next_",
                                ]),
                                PickFrom(1, [
                                    "user",
                                    "business",
                                    "review",
                                    "advertiser",
                                ]),
                                PickFrom(RandomInt(0, 2), [
                                    "_config",
                                    "_presenter",
                                    "_params",
                                    "_event",
                                ]),
                                PickFrom(1, [
                                    "",
                                    PickFrom(1, [
                                        "_if_enabled",
                                        "_if_active",
                                    ]),
                                ]),
                            ],
                            [
                                PickFrom(1, [
                                    "Serializable",
                                    "",
                                ]),
                                PickFrom(RandomInt(1, 2), [
                                    "Ad",
                                    "Review",
                                    "Biz",
                                    "Business",
                                    "Signup",
                                    "User",
                                ]),
                                PickFrom(1, [
                                    "Repository",
                                    "Stub",
                                    "Checkout",
                                ]),
                                PickFrom(1, [
                                    "Params",
                                    "Type",
                                    "Presenter",
                                    "Wizard",
                                    "Accessor",
                                    "",
                                ]),
                            ],
                    ])
               )
               )

bind_generator("yelp", yelp,
"""
Yelp programmer simulator.

Generates a typical Yelp import.
""")
