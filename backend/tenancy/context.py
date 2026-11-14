"""The ClientAccess of the request being handled, for code without a request
(core.audit.log_action). Set by tenancy.middleware."""

from contextvars import ContextVar

current_access = ContextVar("current_access", default=None)
