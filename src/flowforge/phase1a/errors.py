class Phase1AError(Exception):
    pass


class AuthenticationError(Phase1AError):
    pass


class AuthorizationError(Phase1AError):
    pass


class TenantIsolationError(Phase1AError):
    pass


class TokenReplayError(AuthenticationError):
    pass


class WorkflowError(Phase1AError):
    pass
