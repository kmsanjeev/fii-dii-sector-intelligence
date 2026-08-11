from .contracts import *  # noqa: F401,F403


def __getattr__(name: str):
    if name == "ResearchPlatformService":
        from .service import ResearchPlatformService

        return ResearchPlatformService
    if name == "get_research_platform_service":
        from .service import get_research_platform_service

        return get_research_platform_service
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "ResearchPlatformService",
    "get_research_platform_service",
]
