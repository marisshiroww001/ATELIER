import logging

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

logger = logging.getLogger(__name__)


class DebugSocialAccountAdapter(DefaultSocialAccountAdapter):

    def on_authentication_error(
        self,
        request,
        provider,
        error=None,
        exception=None,
        extra_context=None
    ):
        logger.error(
            "SOCIAL LOGIN ERROR | Provider: %s | Error: %r | Exception: %r",
            getattr(provider, "id", "unknown"),
            error,
            exception,
            exc_info=(
                type(exception),
                exception,
                exception.__traceback__
            ) if exception else False
        )

        super().on_authentication_error(
            request,
            provider,
            error=error,
            exception=exception,
            extra_context=extra_context
        )