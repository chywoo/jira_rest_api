__author__ = 'chywoo.park'
import sys
sys.path.append("../python_rest_client")

import json


from restful_lib import Connection

base_url = "http://jira.score/rest/api/latest"
conn = Connection(base_url, username="chywoo.park", password="10")
res = conn.request("/issue/TS-17952", headers={'Authorization':'Basic Y2h5d29vLnBhcms6dGl6ZW5zZGsqMTA=', 'Content-type':'application/json', 'Accept':'application/json'}, args={})


if res[u'headers']['status'] != "200":
    print("Fail to get issue data")
    exit(1)

body = json.loads(res[u'body'])
print(body.keys() )
print("Key: " + body[u'key'])
# print("Status: %s\n" % res[u'headers']['status'])

