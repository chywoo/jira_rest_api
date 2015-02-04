__author__ = 'Sungho Park'

import json
import requests
from requests.auth import HTTPBasicAuth

# params={'jql':'project=TS', 'maxResults':'100', 'startAt':'0'}
# r = requests.get("http://172.21.17.95:8080/rest/api/2/search", auth=HTTPBasicAuth('chywoo.park', 'chywoo.park'), params=params)
#
# print(r.status_code)
# print(r.headers)
# print(type(r.json()))

data_p='TEST'
data_summary='써머리 테스트'
data_issuetype='Task'
data_description='디스크립션descritpion'

req_body = """
{
    "fields": {
        "project": {
            "key": "%s"
        },
        "summary": "%s",
        "description": "%s",
        "issuetype": {
            "name": "%s"
        }
    }
}
""" % (data_p, data_summary, data_description, data_issuetype)

data=json.loads(req_body)
headers={'Content-type': 'application/json'}

r = requests.post("http://172.21.17.95:8080/rest/api/2/issue", data=req_body.encode('utf-8'), auth=('chywoo.park','chywoo.park'), headers=headers)
print(r.status_code)

print(r.text)
print("URL: ", r.url)
print("", r.request.body)