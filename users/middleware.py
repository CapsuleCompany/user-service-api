from users.utils.location.client import get_client_ip


class AttachIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.ip_address = get_client_ip(request)
        response = self.get_response(request)
        return response