__author__ = 'chywoo.park'

import sys
sys.path.append('./rest')
sys.path.append('.')
import jira
import util

SRC_SERVER_BASE_URL = "http://168.219.209.56/jira"
PROXYS = {
    'http':'http://172.21.17.105:3128',
    'https': 'http://172.21.17.105:3128'
}
DST_SERVER_BASE_URL = "http://jira.score"
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

CUSTOM_SPIN_ID = "customfield_10608"
CUSTOM_SPIN_URL = "customfield_10610"
CUSTOM_SPIN_CREATED = "customfield_10607"

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
    "spin_id": "/fields/" + CUSTOM_SPIN_ID,
    "spin_url": "/fields/" + CUSTOM_SPIN_URL,
    "spin_created": "/fields/" + CUSTOM_SPIN_CREATED
}


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


def init_issue_transition():
    """
    Mapping transition ID for table issue status.

    The keys are from source Jira and values are transition IDs from target Jira.
    When source issue status is changed, we should use transition ID for appropriate target issue status.
    :param status_table:
    :return:
    """

    # For test Jira
    # mapping = {
    #     "Open"       : "721",
    #     "In Progress": "751",
    #     "Reopened"   : "711",
    #     "Resolved"   : "731",
    #     "Closed"     : "741",
    #     "OPENED"     : "721",
    #     "SUBMITTED"  : "721",
    #     "Done"       : "741",
    #     "Confirmed"  : "721",
    #     "Rejected"   : "711",
    #     "Accepted"   : "721"
    # }

    # For S-Core Jira
    mapping = {
        "Open"       : "711",
        "In Progress": "751",
        "Reopened"   : "741",
        "Resolved"   : "721",
        "Closed"     : "731",
        "OPENED"     : "711",
        "SUBMITTED"  : "711",
        "Done"       : "731",
        "Confirmed"  : "711",
        "Rejected"   : "721",
        "Accepted"   : "711"
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
    target_factory = factory.get_factory(DST_SERVER_BASE_URL, 'chywoo.park', 'tizensdk*10')

    target_issue_status_table = get_issues_status(target_factory)
    if target_issue_status_table is None:
        print("Fail to get issue status information. Can not be continued.")
        sys.exit(-1)
    else:
        issue_status_map = init_issue_transition()  # Currently target_issue_status_table is not used.

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

            existing_issue = find_issue_in_target(target_factory, source_issue)

            if not existing_issue:
                # Phase 2-1. Create issue
                print("%5s   " % "N", end="")

                result = create_in_target(target_factory, source_issue)

                if result == 201:
                    print("Created %-10s %s" % (target_factory.value("key"), source_issue.summary), end="")

                    # Update issue status because issue status is "Open" at creation.
                    existing_issue = find_issue_in_target(target_factory, source_issue)
                    if existing_issue:
                        result = existing_issue.update_status(issue_status_map[source_issue.issuestatus])
                        if result == 204:
                            print("[FAIL TO UPDATE ISSUE STATUS]", end="")

                    print()
                else:
                    errormessage = target_factory.value()
                    print("Failed  %-10s " % ("ERROR"), errormessage['errors'])
            else:
                # Phase 2-2. Update existing issue
                print("%5s   " % "Y", end="")
                result = existing_issue.update_status(issue_status_map[source_issue.issuestatus])
                if result == 204:
                    print("Updated %-10s %s" % (existing_issue.key, source_issue.issuestatus))
                else:
                    errormessage = target_factory.value()
                    print("Failed  %-10s " % ("ERROR"), errormessage['errors'])

        start_at += JQL_MAX_RESULTS

    print("END" * 10)


def print_usage():
    print("Usage: python3 migration.py <source jira HTTP URL> <target jira HTTP URL>")
    print("       ex) migration.py http://100.100.100.1/jira http://100.100.100.2:8080\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
    else:
        SRC_SERVER_BASE_URL = sys.argv[1]
        DST_SERVER_BASE_URL = sys.argv[2]

        main()

