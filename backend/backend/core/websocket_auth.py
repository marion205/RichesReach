class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app
    async def __call__(self, scope, receive, send):
        return await self.app(scope, receive, send)

def JWTAuthMiddlewareStack(app):
    # insert your auth wrapper here when ready; for now passthrough
    return app