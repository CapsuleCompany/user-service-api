import requests
from django.conf import settings

def get_client_ip(request):
    """
    Retrieves the IP address from a request object.
    Handles cases where the user is behind a proxy.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip

API_KEY = settings.IPGEOLOCATION_API_KEY

def get_location_from_ip(request):
    """
    Retrieves the location of a user based on their IP address using the ipgeolocation.io API.
    """
    ip_address = get_client_ip(request)

    # TODO: Local Dev
    if ip_address[:3] == "192":
        response = requests.get('https://api.ipify.org?format=json')
        response.raise_for_status()
        ip_data= response.json()
        ip_address = ip_data['ip']

    if not ip_address or ip_address == "127.0.0.1":
        return {"error": "Localhost IP detected, unable to get location. --cc--"}

    url = f"https://api.ipgeolocation.io/ipgeo?apiKey={API_KEY}&ip={ip_address}"

    #TODO: On Paid Subscription
    """url = f"https://api.ipgeolocation.io/ipgeo?apiKey={API_KEY}&ip={ip_address}&include=security"""

    headers = {
        'User-Agent': request.META.get('HTTP_USER_AGENT', 'Django-IP-Client/1.0')
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.json(), "status_code": response.status_code}