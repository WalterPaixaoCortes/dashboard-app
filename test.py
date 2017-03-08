import requests
import base64
import json

b_auth_token = base64.b64encode(b'riverlite+SiUG2WOz82u0KJhs:cHISQrSHqvRqz50U')

auth_token = b_auth_token.decode('utf-8')

header = {
    'Authorization': 'Basic ' + auth_token,
    'Content-Type': 'application/json',
    'Accept': 'application/vnd.connectwise.com+json; version=3.0.0'
}


proxy = {'https': 'http://walter_ritzel:Wrpc.0218@anonproxy.us.dell.com:80'}

url = "https://api-eu.myconnectwise.net/v4_6_release/apis/3.0/service/tickets?pageSize=10&page=1"
# url = "https://api-eu.myconnectwise.net/v4_6_release/apis/3.0/service/tickets/count"

response = requests.get(url, headers=header, proxies=proxy)

print(response.text)
print(round(json.loads(response.text)['count'] / 1000))