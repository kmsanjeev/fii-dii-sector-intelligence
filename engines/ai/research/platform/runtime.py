from __future__ import annotations

import socket
from datetime import datetime, timedelta, timezone
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from engines.ai.research.platform.service import ResearchPlatformService, get_research_platform_service, utc_now
from engines.common import config as cfg


class ResearchPlatformRuntime:
    def __init__(
        self,
        *,
        service: ResearchPlatformService | None = None,
        instance_id: str | None = None,
        poll_seconds: int | None = None,
    ):
        self.service = service or get_research_platform_service()
        self.instance_id = instance_id or f"{socket.gethostname()}-research-worker"
        self.poll_seconds = int(poll_seconds or cfg.VEDA_RESEARCH_SCHEDULER_POLL_SECONDS)
        self._scheduler: BackgroundScheduler | None = None

    def start(self) -> bool:
        if self._scheduler is not None and self._scheduler.running:
            return True
        self._scheduler = BackgroundScheduler(timezone=cfg.VEDA_RESEARCH_SCHEDULER_TIMEZONE)
        self._scheduler.add_job(
            self._scheduled_tick,
            trigger=IntervalTrigger(seconds=self.poll_seconds, timezone=cfg.VEDA_RESEARCH_SCHEDULER_TIMEZONE),
            id="veda_research_runtime_tick",
            name="VEDA Research Runtime Tick",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=max(5, self.poll_seconds),
        )
        self._scheduler.start()
        self.service.store.set_runtime_state(
            "worker_status",
            {
                "instance_id": self.instance_id,
                "running": True,
                "last_started_at": utc_now(),
                "poll_seconds": self.poll_seconds,
            },
            updated_at=utc_now(),
        )
        return True

    def stop(self) -> None:
        if self._scheduler is not None and self._scheduler.running:
            self._scheduler.shutdown(wait=False)
        self._scheduler = None
        self.service.store.set_runtime_state(
            "worker_status",
            {
                "instance_id": self.instance_id,
                "running": False,
                "last_stopped_at": utc_now(),
                "poll_seconds": self.poll_seconds,
            },
            updated_at=utc_now(),
        )

    def pause(self, *, actor_id: str = "admin", reason: str | None = None) -> dict[str, Any]:
        return self.service.set_platform_runtime_state(paused=True, actor_id=actor_id, reason=reason)

    def resume(self, *, actor_id: str = "admin", reason: str | None = None) -> dict[str, Any]:
        return self.service.set_platform_runtime_state(paused=False, actor_id=actor_id, reason=reason)

    def set_kill_switch(self, enabled: bool, *, actor_id: str = "admin", reason: str | None = None) -> dict[str, Any]:
        return self.service.set_platform_runtime_state(kill_switch=enabled, actor_id=actor_id, reason=reason)

    def run_due_tasks(self, *, as_of: str | None = None, actor_id: str = "scheduler") -> dict[str, Any]:
        now = as_of or utc_now()
        lease_expires = self._shift_iso(now, cfg.VEDA_RESEARCH_WORKER_LEASE_SECONDS)
        acquired = self.service.store.try_acquire_lease(
            "research_worker_lease",
            owner_id=self.instance_id,
            now=now,
            expires_at=lease_expires,
        )
        if not acquired:
            return {"status": "LEASE_HELD", "instance_id": self.instance_id, "as_of": now, "runs_started": 0}
        try:
            result = self.service.run_due_schedules(as_of=now, actor_id=actor_id)
            self.service.store.set_runtime_state(
                "worker_status",
                {
                    "instance_id": self.instance_id,
                    "running": True,
                    "last_tick_at": now,
                    "last_result": result,
                    "poll_seconds": self.poll_seconds,
                },
                updated_at=now,
            )
            return result
        finally:
            self.service.store.release_lease("research_worker_lease", owner_id=self.instance_id, released_at=utc_now())

    def health(self) -> dict[str, Any]:
        worker_status = self.service.store.get_runtime_state("worker_status") or {}
        lease = self.service.store.get_runtime_state("research_worker_lease") or {}
        controls = self.service.platform_runtime_state()
        due_count = len(self.service.store.list_due_schedules(utc_now()))
        return {
            "scheduler_alive": bool(self._scheduler and self._scheduler.running),
            "worker_alive": bool(worker_status.get("running")),
            "instance_id": self.instance_id,
            "lease": lease,
            "controls": controls,
            "runs_due": due_count,
            "backlog_state": self.service.backlog_state(),
            "providers": self.service._provider_health_rows(),
        }

    def _scheduled_tick(self) -> None:
        self.run_due_tasks(actor_id="scheduler")

    def _shift_iso(self, iso_value: str, seconds: int) -> str:
        base = datetime.fromisoformat(iso_value.replace("Z", "+00:00"))
        return (base + timedelta(seconds=seconds)).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


_RUNTIME: ResearchPlatformRuntime | None = None


def get_research_platform_runtime() -> ResearchPlatformRuntime:
    global _RUNTIME
    if _RUNTIME is None:
        _RUNTIME = ResearchPlatformRuntime()
    return _RUNTIME
