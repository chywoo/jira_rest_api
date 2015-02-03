__author__ = 'chywoo.park'

import sys

if __name__ == "__main__":
    sys.exit()

reload(sys)
sys.setdefaultencoding('utf-8')


import json
import base64

from restful_lib import Connection
import httplib2


REST_API_URL_POSTFIX = "/rest/api/latest"


class JIRACommon:
    """
    Common class for JIRA REST API Classes. Don't this class directly. This is a abstract class.
    """

    # Variables about HTTP Connection
    conn = None
    id = None
    password = None

    # HTTP Request variables
    base_url = ""
    rest_url = None
    httpHeaders = None
    post_body = None
    http_args = {}

    # HTTP Response variables.
    body = {}
    res = None

    jira_debug_level = 0


    def log(self, *args):
        """
        Debug log if jira_debug_level > 0
        :param args:
        :return:
        """
        if self.jira_debug_level > 0:
            print "[REST DEBUG]",

            for message in args:
                print message,

            print

    def set_post_body(self, body):
        """
        Set body data of HTTP POST
        """
        self.post_body = body


    def __init__(self, base_url, id, password, debug_level):
        """

        :param base_url:
        :param id:
        :param password:
        :param debug_level: 1 - JIRA log, 2 - JIRA log + HTTP log
        :return:
        """
        assert (base_url and id and password and base_url != "" and id != "" and password != "")
        assert (isinstance(id, str) and isinstance(password, str))

        self.jira_debug_level = debug_level

        if debug_level > 1:
            # Set HTTPLIB2's debug level
            httplib2.debuglevel = debug_level

        # Initialize HTTP Request variables
        self.rest_url = None
        self.post_body = None
        self.http_args = {}

        self.id = id.strip()
        self.password = password.strip()

        # Make HTTP authorization key. Connection class has ID and password params but doesn't work.
        self.httpHeaders = {'Content-type': 'application/json', 'Accept': 'application/json',
                            'Authorization': 'Basic ' + base64.b64encode(self.id + ':' + self.password)}

        # Make connection to REST server. This is a JUST connection.
        base_url.strip()
        self.base_url = base_url + REST_API_URL_POSTFIX
        self.conn = Connection(self.base_url, self.id, self.password)

        # Initialize HTTP Response variables.
        self.body = {}
        self.res = None

    def setRESTURL(self, resource_url):
        """
         Make full REST URL. This is overwrite previous REST URL.
        :param resource_url: resource URL for REST API
        """
        self.rest_url = resource_url

    def request(self, method="get"):
        """
        Request REST API Call
        :return: HTTP status code
        """
        assert (self.rest_url and self.rest_url != "")

        self.log("HTTP Request URL : " + self.base_url + self.rest_url)
        self.log("HTTP Request headers :", self.httpHeaders)

        self.res = self.conn.request(self.rest_url, method=method, headers=self.httpHeaders, args=self.http_args, body=self.post_body)

        self.log("HTTP Response status : " + self.res[u'headers']['status'])

        if self.res[u'headers']['status'] != "200":
            self.log("HTTP response data : ", self.res[u'body'])
            return self.res[u'headers']['status']

        # Clear value of rest_url for reuse.
        self.rest_url = None

        self.body = json.loads(self.res[u'body'])
        return self.res[u'headers']['status']


    def request_get(self):
        return self.request("get")

    def request_post(self):
        return self.request("post")


    def value(self, keystring=None):
        """
        Get value from JSON format data. Input key path(key1/key2/key3) and get the value.
        :param keystring: Key path
        :return: Value
        """

        if keystring is None:
            return self.body

        result = self.body

        keys = keystring.split("/")

        for key in keys:
            if isinstance(result, dict):
                result = result[key]
            elif isinstance(result, list):
                try:
                    result = result[int(key)]
                except ValueError as e:
                    raise KeyError(
                        "'%s' is not index value of List. Type of the value is List. Index must be integer." % key)

        return result


class JIRAIssue(JIRACommon):
    RESOURCE_BASE_URL = "/issue/"

    def retrieve(self, resource_url):
        self.setRESTURL(resource_url)
        status = self.request()

        self.log(resource_url + " : ", self.body)

        return status

    def retrieve_issue(self, issue_key):
        resource_url = self.RESOURCE_BASE_URL + issue_key

        return self.retrieve(resource_url)

    def retrieve_issue_types(self):
        resource_url = "/issuetype"

        return self.retrieve(resource_url)

    def retrieve_search(self, jql):
        resource_url = "/search?jql=" + jql  # TODO special character(=, space, ...) must be processed.

        return self.retrieve(resource_url)

    def create_issue(self, project_id, summary, issuetype, assignee=None, priority=None, description=None):
        req_body = u"""
        {
            "fields": {
                "project":
                {
                    "key": "%s"
                },
                "summary": "%s",
                "description": "DESCRIPTION",
                "issuetype": {
                    "name": "%s"
                }
            }
        }
        """ % (project_id, summary, issuetype)

        self.set_post_body(req_body)
        self.log("Issue creation json data:\n", self.post_body)
        resource_url = "/issue/"
        self.httpHeaders["Content-Type"]="application/json" # FIXME Why does this line inserted?

        self.setRESTURL(resource_url)
        status = self.request_post()

        self.log(resource_url + " : ", self.body)

        return status


    @property
    def key(self):
        return self.value('key')


class JIRAFactory:
    debug_level = 0

    def __init__(self, debug_level=0):
        """
        :param debug_level: debug_level: 1 - JIRA log, 2 - JIRA log + HTTP log
        :return:
        """
        self.debug_level = debug_level

    def createIssue(self, url, id, password):
        return JIRAIssue(url, id, password, self.debug_level)
