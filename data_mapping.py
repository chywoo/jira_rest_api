__author__ = 'chywoo.park'


class DataMap:
    SRC_JIRA_USER_ID="chywoo.park"
    SRC_JIRA_USER_PWD="score123"

    DST_JIRA_USER_ID="robot"
    DST_JIRA_USER_PWD="robot"

    SPIN_JIRA_ISSUE_MAP = {
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

    CUSTOM_SPIN_ID = "customfield_10100"
    CUSTOM_SPIN_URL = "customfield_10101"
    CUSTOM_SPIN_CREATED = "customfield_10105"

    # For issue view
    TARGET_JIRA_ISSUE_MAP = {
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
        "spin_id": "/fields/" + CUSTOM_SPIN_ID,
        "spin_url": "/fields/" + CUSTOM_SPIN_URL,
        "spin_created": "/fields/" + CUSTOM_SPIN_CREATED
    }

    # For assignee mapping. This is for case that user name is different from single ID.
    USER_MAP = {
    }

    def get_user(src_user):
        if DataMap.USER_MAP.__len__() == 0:
            return src_user
        else:
            try:
                return DataMap.USER_MAP[src_user]
            except KeyError:
                return src_user

    # Issue status mapping table from source jira to target jira
    ISSUE_STATUS_MAP = {
        "Open"       : "Open",
        "OPENED"     : "Open",
        "SUBMITTED"  : "Open",
        "Accepted"   : "Open",
        "Confirmed"  : "Open",
        "To Do"      : "Open",
        "Resolved"   : "Resolved",
        "Closed"     : "Closed",
        "Done"       : "Closed",
        "In Progress": "In Progress",
        "Reopened"   : "Reopened"
    }

    def get_issue_status(src_status):
        return DataMap.ISSUE_STATUS_MAP[src_status]

    ISSUE_TRANSITION_ID = {
        "Open"       : "721",
        "In Progress": "751",
        "Reopened"   : "711",
        "Resolved"   : "731",
        "Closed"     : "741",
        "OPENED"     : "721",
        "SUBMITTED"  : "721",
        "To Do"      : "721",
        "Done"       : "741",
        "Confirmed"  : "721",
        "Rejected"   : "711",
        "Accepted"   : "721"
    }

    def get_transition_id(to_status):
        return DataMap.ISSUE_TRANSITION_ID[to_status]

    SPIN_JQL = '( ( project in ("Tizen 2.3 Release", "Tizen 2.3 Source Release", "Tizen SDK TF", "Tizen 2.4 Release" ) AND issuetype in (Bug, DEFECT) ) OR (project = SDKRM and issuetype in (Task, Defect)) ) AND filter = "S-Core(PSLab) Config_User"'

    def get_jql():
        return DataMap.SPIN_JQL