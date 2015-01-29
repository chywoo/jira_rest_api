__author__ = 'chywoo.park'

if __name__ == "__main__":
    pass

import json
import base64

from restful_lib import Connection


REST_API_URL_POSTFIX = "/rest/api/latest"

jira_debug_level=0


class JIRACommon:
    """
    Common class for JIRA REST API Classes. Don't this class directly. This is a abstract class.
    """
    base_url = ""
    rest_url = ""
    body = {}
    httpHeaders = {'Content-type': 'application/json', 'Accept': 'application/json'}


    def __init__(self, base_url, id, password):
        assert (base_url and id and password and base_url != "" and id != "" and password != "")
        assert (isinstance(id, str) and isinstance(password, str))
        global conn

        # Make HTTP authorization key. Connection class has ID and password params but doesn't work.
        self.httpHeaders["Authorization"] = "Basic " + base64.b64encode(id.strip() + ":" + password.strip())

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
        self.rest_url = resource_url

    def request(self):
        assert(self.rest_url and self.rest_url != "")

        global res

        res = conn.request(self.rest_url, headers=self.httpHeaders, args={})

        if res[u'headers']['status'] != "200":
            print("STATUS == " + res[u'headers']['status'])

        self.body = json.loads(res[u'body'])
        return self.body

    def value(self, keystring):
        """
        Get value from JSON format data. Input key path(key1/key2/key3) and get the value.
        :param keystring: Key path
        :return: Value
        """
        keys = keystring.split("/")

        result = self.body

        for key in keys:
            if isinstance( result, dict):
                result = result[key]
            elif isinstance( result, list):
                try:
                    result = result[int(key)]
                except ValueError as e:
                    raise KeyError("'%s' is not index value of List. Type of the value is List. Index must be integer." % key)

        return result

class JIRAIssue(JIRACommon):
    RESOURCE_BASE_URL="/issue/"


    def retrieve(self, issue_key):
        self.setRESTURL(self.RESOURCE_BASE_URL + issue_key)
        self.request()

        if jira_debug_level > 0:
            print "[REST DEBUG] Retrived issue data: ",  self.body

    @property
    def key(self):
        return self.value('key')

    def create(self, project_id, summary, issuetype, assignee = None, priority = None, description = None ):
        pass


class JIRAFactory:
    def createIssue(self, url, id, password):
        return JIRAIssue(url, id, password)


