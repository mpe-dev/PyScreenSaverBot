from __future__ import annotations

import logging
import threading

_local = threading.local()


class DatabaseLogHandler(logging.Handler):
    """Logging handler that persists records to the AppLog database model.

    Thread-safe reentrance guard prevents recursion when the ORM itself emits
    log records during a write. Failures are silently swallowed so that a DB
    hiccup never crashes the application.
    """

    def emit(self, record: logging.LogRecord) -> None:
        if getattr(_local, "emitting", False):
            return
        _local.emitting = True
        try:
            from django.apps import apps  # lazy import — avoids AppRegistryNotReady

            AppLog = apps.get_model("screensaver_app", "AppLog")
            AppLog.objects.create(
                level=record.levelname,
                logger_name=record.name,
                message=self.format(record),
            )
        except Exception:
            pass  # never let logging failures crash the app
        finally:
            _local.emitting = False
