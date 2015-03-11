__author__ = 'chywoo.park'

import sys

if __name__ == "__main__":
    sys.exit()

import requests
import util


REST_API_URL_POSTFIX = "/rest/api/latest"

DEFAULT_JIRA_ISSUE_MAP = {
    "issuetype": "/fields/issuetype/name",
    "issuestatus": "/fields/status/name",
    "key": "/key",
    "assignee": "/fields/assignee/name",
    "displayname": "/fields/assignee/displayName",
    "summary": "/fields/summary",
    "description": "/fields/description",
#    "components": "/fields/components/{#}/name",
    "environment": "/fields/environment",
#    "fixversions": "/fields/fixVersions/{#}/name",
    "created": "/fields/created"
}


class RESTNetwork:
    """
    Common class for JIRA REST API Classes. Don't this class directly. This is a abstract class.
    """

    _is_network_initialized = False     # Check if network facility is initialized.

    # Variables about HTTP Connection
    conn = None
    username = None
    password = None
    proxies = None

    # HTTP Request variables
    server_url = ""
    base_url = ""
    rest_url = None
    http_headers = {}
    post_body = None
    http_args = {}

    # HTTP Response variables.
    res = None
    res_body = None

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

    def set_proxy(self, proxy):
        self.proxies = None
        self.proxies = proxy

    def __init__(self, server_url, username, password, debug_level):
        """

        :param server_url:
        :param username:
        :param password:
        :param debug_level: 1 - JIRA log, 2 - JIRA log + HTTP log
        :return:
        """
        assert (server_url and username and password and server_url != "" and username != "" and password != "")
        assert (isinstance(username, str) and isinstance(password, str))

        self.jira_debug_level = debug_level

        self.username = username
        self.password = password
        # Initialize HTTP Request variables
        self.rest_url = None
        self.post_body = None
        self.http_args = {}
        self.http_headers = {}

        # Make connection to REST server. This is a JUST connection.
        self.server_url = server_url.strip()
        self.base_url = self.server_url + REST_API_URL_POSTFIX

        # Initialize HTTP Response variables.
        self.res_body = None
        self.res = None

        self._is_network_initialized = True

    def set_resturl(self, resource_url):
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

        if self._is_network_initialized is False:
            raise ConnectionError("Not initialized yet.")

        self.log("HTTP Request URL : " + self.base_url + self.rest_url)
        self.log("HTTP Request headers :", self.http_headers)

        self.res_body = None
        self.res = requests.request(method=method,
                                    url=self.base_url + self.rest_url,
                                    headers=self.http_headers,
                                    auth=(self.username, self.password), params=self.http_args,
                                    data=self.post_body,
                                    proxies = self.proxies)

        try:
            self.res_body = util.VersatileDict(self.res.json())
        except ValueError:  # Not json format
            self.res_body = None

        self.log("HTTP Request URL: %s" % self.res.url)
        self.log("HTTP Response status : %d" % self.res.status_code)

        if self.res.status_code == requests.codes.unauthorized:
            self.log("Status Code: %d, Message: Unauthorized, URL: %s" % (self.res.status_code, self.res.url))

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
        if self.res_body is None:
            return None
        else:
            return self.res_body.value(keystring)


class JIRAFactory(RESTNetwork):
    _fields_mapping = None

    def __init__(self, server_url, username, password, mapping, debug_level):
        self._fields_mapping = mapping

        super().__init__(server_url, username, password, debug_level)

    def get_mapping(self):
        return self._fields_mapping

    def set_mapping(self, mapping):
        self._fields_mapping = mapping

    def _new_issue_object(self):
        _issue = Issue(self.server_url, self.username, self.password)
        return _issue

    def _new_issue_object(self, obj, mapping):
        _issue = Issue(obj, mapping, self.server_url, self.username, self.password)
        return _issue

    @property
    def http_status(self):
        """
        return HTTP status code
        :return: HTTP status code
        """
        return self.res.status_code

    def retrieve(self):
        status = self.request()

        if status != requests.codes.ok:
            self.log("Fail to get %s, Status Code: %d" % (self.res.url, self.res.status_code))
            return status
        else:
            self.log("HTTP response data : %s" % self.res.text)

        return status

    def retrieve_issue(self, issue_key):
        self.set_resturl("/issue/%s" % issue_key)

        if self.retrieve() == requests.codes.ok:
            return self._new_issue_object(self.value(), self._fields_mapping)
        else:
            return None

    def retrieve_issue_types(self):
        self.set_resturl("/issuetype")

        return self.retrieve()

    def retrieve_search(self, jql, start_at=0, max_results=50):
        """
        Execute JQL.

        :param jql:
        :param start_at:
        :param max_results:
        :return:
        """
        self.set_resturl("/search")

        self.add_url_param("jql", jql)
        self.add_url_param("startAt", str(start_at))
        self.add_url_param("maxResults", str(max_results))

        if self.retrieve() == requests.codes.ok:
            return self.value()
        else:
            return None

    def get_issue(self, idx):
        """
        Get issue object from searched issues by retrieve_search() method.
        :param idx: index of searched issues
        :return: instance of Issue class
        """
        return self._new_issue_object(self.value("issues/%d" % idx), self.get_mapping())

    def create_issue(self, project_id, summary, issuetype, assignee=None, priority=None, description="", args={}):
        """
        Create JIRA Issue.

        :param project_id:
        :param summary:
        :param issuetype:
        :param assignee:
        :param priority:
        :param description:
        :return:
        """

        req_body = util.VersatileDict()
        req_body.add("fields/project/key", project_id)
        req_body.add("fields/summary", summary)
        req_body.add("fields/description", description)
        req_body.add("fields/issuetype/name", issuetype)

        if len(args) > 0:
            arg_list = list(args.keys())

            for arg in arg_list:
                if args[arg] is None:
                    continue

                self.log("Create issue arg => %s : %s" % (arg, args[arg]))
                req_body.add(arg, args[arg])

        self.log("Issue creation json data:\n", req_body)
        self.set_post_body(req_body.json())

        self.http_headers["Content-Type"] = "application/json"

        self.set_resturl("/issue")
        status = self.request_post()

        if status != requests.codes.created:
            self.log("Fail to create issue. Status Code: %d, URL: %s" % (status, self.res.url))
            self.log(self.res.text)
            return status

        return status


class JIRAFactoryBuilder:
    debug_level = 0

    def __init__(self, debug_level=0):
        """
        :param debug_level: debug_level: 1 - JIRA log, 2 - JIRA log + HTTP log
        :return:
        """
        self.debug_level = debug_level

    def get_factory(self, url, username, password, mapping=DEFAULT_JIRA_ISSUE_MAP):
        return JIRAFactory(url, username, password, mapping, self.debug_level)


class JIRAFieldsMap:
    """
    Map field name and REST api path.
    See DEFAULT_JIRA-ISSUE_MAP. It is a sample.
    """
    def __init__(self, map):
        if isinstance(map, dict):
            self.map = map
        else:
            raise ValueError("Type of the parameter is not Dictionary.")

    def keys(self):
        return self.map.keys()

    def value(self, key):
        return self.map.get(key)


class Issue(RESTNetwork):
    """
    Contains issue data. This does not provide REST API.
    Main function is to use JIRA field path as  property. eg) issue.key => issue.vale("fields/key")
    """

    def __init__(self, obj=None, mapping=DEFAULT_JIRA_ISSUE_MAP, server_url=None, username=None, password=None, debug_level=0):
        """

        :param obj: JIRA Issue data. VersatilaDict type or Dictionary
        :param mapping: JIRA Field and JSON Path mapping dictionary or JIRAFieldsMap
        :param server_url:
        :param username:
        :param password:
        :param debug_level:
        :return:
        """

        if obj:                                                             # if data is empty
            if isinstance(obj, util.VersatileDict):
                self._data = obj
            else:
                self._data = util.VersatileDict(obj)

            if isinstance(mapping, JIRAFieldsMap):
                self.map = mapping
            else:
                self.map = JIRAFieldsMap(mapping)

            for field in mapping.keys():
                v = self.map.value(field)
                d = self._data.value(v)
                setattr(self, field, d)

        if server_url is not None:                                            # if don't want to initialize network
            super().__init__(server_url, username, password, debug_level)     # Constructor of RESTNetwork

    def set_data(self, obj, mapping=DEFAULT_JIRA_ISSUE_MAP):
        self.__init__(obj, mapping)

    def update_status(self, value):
        """
        Update issue status
        :param value: new issue status
        :return: HTTP code
        """
        self.set_resturl("/issue/%s/transitions" % self.key)
        self.http_headers["Content-Type"] = "application/json"
        req_body = util.VersatileDict()
        req_body.add("update", {})
        req_body.add("transition/id", value)

        self.set_post_body(req_body.json())
        return self.request_post()

    def assign(self, user, user_map=None):
        """
        Assign issue to specific user.
        :param user:
        :param user_map: map table between source jira and target jira. This is only used when 'user' is in this map table.
        :return:
        """

        self.set_resturl("/issue/%s/assignee" % self.key)
        self.http_headers["Content-Type"] = "application/json"

        if user_map is not None:
            try:
                tmp = user_map[user]
                user = tmp
            except KeyError:
                pass

        req_body = util.VersatileDict()
        req_body.add("name", user)

        self.set_post_body(req_body.json())
        return self.request("put")
