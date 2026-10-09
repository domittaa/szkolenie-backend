"""Event publisher wiring. Pub/Sub topic is created in the gcp repo (messaging.tf)."""

from functools import lru_cache

from pizza_core.events import EventPublisher, InMemoryPublisher, PubSubPublisher

from app.settings import get_settings


@lru_cache
def get_publisher() -> EventPublisher:
    settings = get_settings()
    if settings.use_inmemory_events or settings.app_env == "local":
        return InMemoryPublisher()
    return PubSubPublisher(project_id=settings.gcp_project_id, topic_id=settings.orders_topic)
