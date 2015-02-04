__author__ = 'chywoo.park'

import sys

if __name__ == "__main__":
    sys.exit()

import json
import requests


REST_API_URL_POSTFIX = "/rest/api/latest"


class JIRACommon:
    """
    Common class for JIRA REST API Classes. Don't this class directly. This is a abstract class.
    """

    # Variables about HTTP Connection
    conn = None
    username = None
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
            print("[REST DEBUG]", end=' ')

            for message in args:
                print(message, end=' ')

            print()

    def set_post_body(self, body):
        """
        Set body data of HTTP POST
        """
        if body is not None:
            self.post_body = body.encode(sys.getdefaultencoding())

    def __init__(self):
        pass

    def __init__(self, base_url, username, password, debug_level):
        """

        :param base_url:
        :param username:
        :param password:
        :param debug_level: 1 - JIRA log, 2 - JIRA log + HTTP log
        :return:
        """
        assert (base_url and username and password and base_url != "" and username != "" and password != "")
        assert (isinstance(username, str) and isinstance(password, str))

        self.jira_debug_level = debug_level

        self.username = username
        self.password = password
        # Initialize HTTP Request variables
        self.rest_url = None
        self.post_body = None
        self.http_args = {}

        # Make connection to REST server. This is a JUST connection.
        base_url.strip()
        self.base_url = base_url + REST_API_URL_POSTFIX

        # Initialize HTTP Response variables.
        self.body = {}
        self.res = None

    def setRESTURL(self, resource_url):
        """
         Make full REST URL. This is overwrite previous REST URL.
        :param resource_url: resource URL for REST API
        """
        self.rest_url = None
        self.rest_url = resource_url

    def add_url_param(self, key, value):
        """
        Add URL parameter. ex)search?jql=project=test => 'jql' is key and 'project=test' is value
        """
        self.http_args[key] = value

    def request(self, method="get"):
        """
        Request REST API Call
        :return: HTTP status code
        """
        assert (self.rest_url and self.rest_url != "")

        self.log("HTTP Request URL : " + self.base_url + self.rest_url)
        self.log("HTTP Request headers :", self.httpHeaders)

        self.res = requests.request(method=method,
                                    url=self.base_url + self.rest_url,
                                    headers=self.httpHeaders,
                                    auth=(self.username, self.password), params=self.http_args,
                                    data=self.post_body)

        self.log("HTTP Response status : %d" % self.res.status_code)

        if self.res.status_code != requests.codes.ok and self.res.status_code != requests.codes.created:
            print("!!FAIL!! Status Code: %d" % self.res.status_code)
            print("Message: %s" % self.res.text)
            return self.res.status_code
        else:
            self.log("HTTP response data : %s" % self.res.text)

        self.body = self.res.json()
        return self.res.status_code


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
    def retrieve(self):
        status = self.request()

        self.log(self.rest_url + " : ", self.body)

        return status

    def retrieve_issue(self, issue_key):
        self.setRESTURL("/issue/%s" % issue_key)

        return self.retrieve()

    def retrieve_issue_types(self):
        self.setRESTURL("/issuetype")

        return self.retrieve()

    def retrieve_search(self, params):
        self.setRESTURL("/search")

        for i in params.keys():
            self.add_url_param(i, params[i])

        return self.retrieve()

    def create_issue(self, project_id, summary, issuetype, assignee=None, priority=None, description=None):
        req_body = """
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

        if self.httpHeaders is None:
            self.httpHeaders = {}

        self.httpHeaders["Content-Type"]="application/json" # FIXME Why does this line inserted?

        self.setRESTURL("/issue")
        status = self.request_post()

        self.log("%s : %s" % (self.rest_url, self.body))

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

    def createIssue(self, url, username, password):
        return JIRAIssue(url, username, password, self.debug_level)
