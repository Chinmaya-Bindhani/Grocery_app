# import requests
# import json
# from typing import Dict, Optional
#
#
# class IPGeolocation:
#     def __init__(self):
#         self.services = {
#             "ip-api.com": "http://ip-api.com/json/{}",
#             "ipinfo.io": "https://ipinfo.io/{}/json",
#             "ipapi.co": "https://ipapi.co/{}/json/"
#         }
#
#     def get_own_ip(self) -> str:
#         try:
#             response = requests.get('https://api.ipify.org?format=json', timeout=10)
#             return response.json()['ip']
#         except Exception as e:
#             print(f"Error getting own IP: {e}")
#             return "8.8.8.8"  # Fallback to Google's DNS as example
#
#     def fetch_from_service(self, service_name: str, ip: str) -> Optional[Dict]:
#         """Fetch geolocation data from a specific service"""
#         try:
#             url = self.services[service_name].format(ip)
#             response = requests.get(url, timeout=10)
#
#             if response.status_code == 200:
#                 return response.json()
#             else:
#                 print(f"  {service_name}: HTTP {response.status_code}")
#                 return None
#         except Exception as e:
#             print(f"  {service_name}: Error - {e}")
#             return None
#
#     def display_results(self, service_name: str, data: Dict):
#         """Pretty print the results from a service"""
#         print(f"\n{'=' * 50}")
#         print(f"Service: {service_name}")
#         print(f"{'=' * 50}")
#
#         # Different services return different field names
#         # We'll map common fields
#         field_mapping = {
#             'IP': ['ip', 'query'],
#             'City': ['city'],
#             'Region': ['region', 'regionName', 'loc'],
#             'Country': ['country', 'country_name'],
#             'Country Code': ['countryCode', 'country_code'],
#             'Latitude': ['lat', 'latitude'],
#             'Longitude': ['lon', 'longitude'],
#             'Timezone': ['timezone'],
#             'ISP': ['isp', 'org', 'org_name'],
#             'ZIP/Postal': ['zip', 'postal']
#         }
#
#         for label, possible_keys in field_mapping.items():
#             for key in possible_keys:
#                 if key in data and data[key]:
#                     value = data[key]
#                     # Handle ipinfo.io's loc format (lat,lon combined)
#                     if key == 'loc' and ',' in str(value):
#                         lat, lon = value.split(',')
#                         print(f"  {'Latitude':<15}: {lat}")
#                         print(f"  {'Longitude':<15}: {lon}")
#                         break
#                     print(f"  {label:<15}: {value}")
#                     break
#
#     def test_single_ip(self, ip: str = None):
#         """Test geolocation for a specific IP (or your own if None)"""
#         if ip is None:
#             ip = self.get_own_ip()
#             print(f"Your public IP address: {ip}")
#
#         print(f"\nFetching geolocation data for: {ip}")
#         print("-" * 50)
#
#         # Try each service
#         for service_name in self.services.keys():
#             data = self.fetch_from_service(service_name, ip)
#             if data:
#                 self.display_results(service_name, data)
#
#     def compare_services(self, ip: str = None):
#         """Compare results from multiple services side-by-side"""
#         if ip is None:
#             ip = self.get_own_ip()
#
#         print(f"\nComparing services for IP: {ip}")
#         print("=" * 70)
#
#         results = {}
#         for service_name in self.services.keys():
#             data = self.fetch_from_service(service_name, ip)
#             if data:
#                 results[service_name] = data
#
#         # Simple comparison table
#         print(f"{'Field':<15} | " + " | ".join(f"{name[:15]:<15}" for name in results.keys()))
#         print("-" * 70)
#
#         # Compare common fields
#         comparisons = [
#             ('City', ['city']),
#             ('Country', ['country', 'country_name']),
#             ('Latitude', ['lat', 'latitude']),
#             ('Longitude', ['lon', 'longitude']),
#             ('ISP', ['isp', 'org'])
#         ]
#
#         for label, keys in comparisons:
#             row = f"{label:<15} | "
#             values = []
#             for service_name, data in results.items():
#                 val = None
#                 for key in keys:
#                     if key in data:
#                         val = data[key]
#                         break
#                 values.append(f"{str(val)[:15]:<15}" if val else f"{'N/A':<15}")
#             print(row + " | ".join(values))
#
#
# def main():
#     """Main function to run the tests"""
#     geo = IPGeolocation()
#
#     print("IP-BASED GEOLOCATION TESTER")
#     print("=" * 50)
#     print("1. Test your own IP")
#     print("2. Test a specific IP")
#     print("3. Compare multiple services")
#     print("4. Test multiple famous IPs")
#
#     choice = input("\nEnter choice (1-4): ").strip()
#
#     if choice == '1':
#         geo.test_single_ip()
#
#     elif choice == '2':
#         ip = input("Enter IP address (e.g., 8.8.8.8): ").strip()
#         geo.test_single_ip(ip)
#
#     elif choice == '3':
#         ip = input("Enter IP address (or press Enter for your own): ").strip()
#         geo.compare_services(ip if ip else None)
#
#     elif choice == '4':
#         # Test with well-known IPs
#         test_ips = [
#             ("8.8.8.8", "Google DNS"),
#             ("1.1.1.1", "Cloudflare DNS"),
#             ("208.67.222.222", "OpenDNS"),
#         ]
#
#         for ip, desc in test_ips:
#             print(f"\n{'#' * 60}")
#             print(f"Testing: {desc} ({ip})")
#             print(f"{'#' * 60}")
#             geo.test_single_ip(ip)
#             input("\nPress Enter to continue...")
#
#     else:
#         print("Invalid choice")
#
#
# if __name__ == "__main__":
#     main()