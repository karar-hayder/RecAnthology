from rest_framework.throttling import BaseThrottle

class AdminThrottle(BaseThrottle):
    def allow_request(self, request, view):
        return True if request.user.is_superuser else False