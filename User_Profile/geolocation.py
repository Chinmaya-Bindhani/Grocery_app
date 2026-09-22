import json
from ipaddress import ip_address
from typing import Dict, Optional
from urllib.error import URLError, HTTPError
from urllib.request import urlopen


class IPGeolocation:
    services = (
        ("ip-api.com", "https://ip-api.com/json/{ip}"),
        ("ipinfo.io", "https://ipinfo.io/{ip}/json"),
        ("ipapi.co", "https://ipapi.co/{ip}/json/"),
    )

    def get_public_ip(self) -> Optional[str]:
        try:
            with urlopen("https://api.ipify.org?format=json", timeout=3) as response:
                return json.loads(response.read()).get("ip")
        except (HTTPError, URLError, ValueError):
            return None

    def locate(self, ip: Optional[str] = None) -> Optional[Dict]:
        if ip:
            try:
                if ip_address(ip).is_private or ip_address(ip).is_loopback:
                    ip = None
            except ValueError:
                ip = None
        ip = ip or self.get_public_ip()
        if not ip:
            return None

        for service, url_template in self.services:
            try:
                with urlopen(url_template.format(ip=ip), timeout=3) as response:
                    location = self._normalize(json.loads(response.read()))
                if location:
                    location["source"] = service
                    return location
            except (HTTPError, URLError, ValueError):
                continue
        return None

    @staticmethod
    def _normalize(data: Dict) -> Optional[Dict]:
        latitude = data.get("lat", data.get("latitude"))
        longitude = data.get("lon", data.get("longitude"))
        if not latitude or not longitude:
            loc = data.get("loc", "")
            if "," in loc:
                latitude, longitude = loc.split(",", 1)

        if not latitude or not longitude:
            return None

        return {
            "city": data.get("city"),
            "region": data.get("regionName", data.get("region")),
            "country": data.get("country", data.get("country_name")),
            "country_code": data.get("countryCode", data.get("country_code")),
            "postal_code": data.get("zip", data.get("postal")),
            "latitude": latitude,
            "longitude": longitude,
            "timezone": data.get("timezone"),
        }
