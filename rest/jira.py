__author__ = 'chywoo.park'

if __name__ == "__main__":
    pass

import json
import base64

from restful_lib import Connection


REST_API_URL_POSTFIX = "/rest/api/latest"


class JIRACommon:
    """
    Common class for JIRA REST API Classes. Don't this class directly. This is a abstract class.
    """
    base_url = ""
    rest_url = ""
    httpHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}


    def __init__(self, base_url, id, password):
        assert (base_url and id and password and base_url != "" and id != "" and password != "")
        assert (isinstance(id, str) and isinstance(password, str))
        global conn

        # Make HTTP authorization key. Connection class has ID and password params but doesn't work.
        self.httpHeaders["Authorization"] = "Basic " + base64.b64encode(id.strip() + ":" + password.strip())
        #self.httpHeaders["Authorization"] = "Basic Y2h5d29vLnBhcms6dGl6ZW5zZGsqMTA="

        # Make connection to REST server. This is a JUST connection.
        base_url.strip()
        self.base_url = base_url + REST_API_URL_POSTFIX
        conn = Connection(self.base_url, id, password)
        print(conn)

    def setRESTURL(self, resource_url):
        """
         Make full REST URL. This is overwrite previous REST URL.
        :param resource_url: resource URL for REST API
        """
        self.rest_url = self.base_url + resource_url


    @property
    def connect(self):
        assert(self.rest_url and self.rest_url != "")

        global res, body

        res = conn.request(self.rest_url, headers=self.httpHeaders, args={})

        if res[u'headers']['status'] != "200":
            raise False

        body = json.loads(res[u'body'])
        return body



class JIRAIssue(JIRACommon):
    RESOURCE_BASE_URL="/issue/"


    def retrieve(self, issue_key):
        global issue_data

        self.setRESTURL(self.RESOURCE_BASE_URL + issue_key)
        issue_data = self.connect()

    @property
    def key(self):
        return self.issue_data[u'key']


class JIRAFactory:
    def createIssue(self, url, id, password):
        return JIRAIssue(url, id, password)


