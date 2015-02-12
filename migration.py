__author__ = 'chywoo.park'

import sys
import jira
import util

SRC_SERVER_BASE_URL = "http://168.219.209.56/jira"
PROXYS = {
    'http':'http://172.21.17.105:3128',
    'https': 'http://172.21.17.105:3128'
}
DST_SERVER_BASE_URL = "http://172.21.17.95:8080"
DST_PROJECT = "SPIN"

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

# For issue view
SCORE_JIRA_ISSUE_MAP = {
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
    "spin_id": "/fields/customfield_10100",
    "spin_url": "/fields/customfield_10101",
    "spin_created":"/fields/customfield_10105"
}

# For issue creation and update
SCORE_JIRA_CUSTOM_FIELDS = {
    "spind_id": "customfield_10100",
    "spind_url": "customfield_10101"
}


CUSTOM_SPIN_ID = "customfield_10100"
CUSTOM_SPIN_URL = "customfield_10101"


SPIN_JQL = 'project in ("Tizen 2.3 Release", "Tizen 2.3 Source Release", "Tizen SDK TF") AND issuetype in (Bug, DEFECT) AND filter = "S-Core(PSLab) Config_User"'

JQL_MAX_RESULTS = 100


def get_issues_status(factory):
    """
    Get issue status name and ID mapping table.
    ex)
    +---------------+----------------+
    | Status name   | Issue ID       |
    +---------------+----------------+
    | Open          |      1         |
    | In Progress   |      3         |
    | Reopened      |      4         |
    |   ...         |      ...       |
    +---------------+----------------+
    :param factory:
    :return: dictionary formated like {<Issue status name>:<Issue status id>}
    """
    issue_status = {}

    factory.set_resturl("/status")
    if factory.request() == 200:
        data = factory.value()

        for i in range(len(data)):
            issue_status[data[i]["name"]] = data[i]["id"]

        return issue_status
    else:
        return None


def init_issue_status(status_table):
    mapping = {
        "Open"       : status_table["Open"],
        "In Progress": status_table["In Progress"],
        "Reopened"   : status_table["Reopened"],
        "Resolved"   : status_table["Resolved"],
        "Closed"     : status_table["Closed"],
        "OPENED"     : status_table["Open"],
        "SUBMITTED"  : status_table["Open"],
        "Done"       : status_table["Closed"],
        "Confirmed"  : status_table["Open"],
        "Rejected"   : status_table["Open"],
        "Accepted"   : status_table["Open"]
    }

    return mapping


def find_issue_in_target(factory, issue):
    """
    Find a issue with issue key in SPIN Issue ID field.
    :param factory: Instance of JIRAFactory class for target JIRA
    :param issue: Issue information. Instance of Issue class
    :return: None - Nothing, instance of Issue class - Issue data
    """
    check_jql = 'project = %s and "SPIN Issue ID" ~ %s' % (DST_PROJECT, issue.key)

    r = factory.retrieve_search(check_jql, 0, 1)

    if r is None:
        raise ConnectionError("Fail to check if issue exist. Http status %d, %s" % (factory.http_status, factory.value("errorMessages/0")))

    cnt = int(factory.value("total"))

    if cnt == 0:
        return None
    elif cnt == 1:
        return factory.get_issue(0)
    else:
        raise LookupError("There is many issues about SPIN key %s." % issue.key)


def create_in_target(factory, issue):

    # Set additional fields
    args = {
        SCORE_JIRA_ISSUE_MAP["spin_id"]: issue.key,
        SCORE_JIRA_ISSUE_MAP["spin_url"]: SRC_SERVER_BASE_URL + "/browse/" + issue.key,
        SCORE_JIRA_ISSUE_MAP["spin_created"]: issue.created,
        SCORE_JIRA_ISSUE_MAP["environment"]: issue.environment
    }

    return factory.create_issue(project_id=DST_PROJECT, summary=issue.summary, issuetype="Bug", description=issue.description, args=args)


def main():
    # Initialize
    factory = jira.JIRAFactoryBuilder()

    source_factory = factory.get_factory(SRC_SERVER_BASE_URL, 'chywoo.park', 'score123')
    source_factory.set_proxy(PROXYS)
    target_factory = factory.get_factory(DST_SERVER_BASE_URL, 'robot', 'robot')

    target_issue_status_table = get_issues_status(target_factory)
    if target_issue_status_table is None:
        print("Fail to get issue status information. Can not be continued.")
        sys.exit(-1)
    else:
        issue_status_map = init_issue_status(target_issue_status_table)

    loop = True
    start_at = 0

    source_issue = jira.Issue()

    #     No.  SPIN-Key Exist  Action   New Key, Summary
    print("%7s %-10s %-5s   %-8s %-10s %s" % ("No.", "SPIN-key", "Exist", "Action", "New-key", "Summary"))

    while loop:
        print("="*80)

        # Phase 1. Get issues from SPIN
        source_factory.retrieve_search(jql=SPIN_JQL, max_results=JQL_MAX_RESULTS, start_at=start_at)

        if source_factory.http_status != 200:
            print("Fail to get issues from SPIN")
            sys.exit(-1)

        data = util.VersatileDict(source_factory.value())

        total_count = int(data.value("total"))
        data._data = data.value("issues")

        # Phase 2. Insert issues to target JIRA
        for i in range(JQL_MAX_RESULTS):

            # Exit loop condition
            if i + start_at >= total_count:
                loop = False
                break

            # Make issue instance for convenience
            source_issue.set_data(data.value(str(i)), SPIN_JIRA_ISSUE_MAP)
            print("%4d:%2d %-10s " % (i + start_at, i, source_issue.key), end="")

            exist_issue = find_issue_in_target(target_factory, source_issue)

            if exist_issue:
                print("%5s   " % "Y", end="")
                result = exist_issue.update_status(issue_status_map[source_issue.issuestatus])
                if result == 204:
                    print("Updated %-10s %s" % (target_factory.value("key"), source_issue.issuestatus))
                else:
                    print("Failed  %-10s $s" % ("ERROR", exist_issue.value("errorMessages/0")))
            else:
                print("%5s   " % "N", end="")
                result = create_in_target(target_factory, source_issue)

                if result == 201:
                    print("Created %-10s %s" % (target_factory.value("key"), source_issue.summary))
                else:
                    print("Failed  %-10s $s" % ("ERROR", target_factory.value("errorMessages/0")))

        start_at += JQL_MAX_RESULTS

    print("END" * 10)


if __name__ == "__main__":
    main()