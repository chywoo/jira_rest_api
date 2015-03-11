__author__ = 'chywoo.park'

import sys
sys.path.append('./rest')
sys.path.append('.')
import jira
import util

SRC_SERVER_BASE_URL = ""
PROXYS = {
    'http':'http://172.21.17.105:3128',
    'https': 'http://172.21.17.105:3128'
}
DST_SERVER_BASE_URL = ""
DST_PROJECT = "SPIN"

from data_mapping import DataMap


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
        DataMap.SCORE_JIRA_ISSUE_MAP["spin_id"]: issue.key,
        DataMap.SCORE_JIRA_ISSUE_MAP["spin_url"]: SRC_SERVER_BASE_URL + "/browse/" + issue.key,
        DataMap.SCORE_JIRA_ISSUE_MAP["spin_created"]: issue.created,
        DataMap.SCORE_JIRA_ISSUE_MAP["environment"]: issue.environment
    }

    return factory.create_issue(project_id=DST_PROJECT, summary=issue.summary, issuetype="Bug", description=issue.description, args=args)


def main():
    # Initialize
    factory = jira.JIRAFactoryBuilder()

    source_factory = factory.get_factory(SRC_SERVER_BASE_URL, DataMap.SRC_JIRA_USER_ID, DataMap.SRC_JIRA_USER_PWD)
    source_factory.set_proxy(PROXYS)
    target_factory = factory.get_factory(DST_SERVER_BASE_URL, DataMap.DST_JIRA_USER_ID, DataMap.DST_JIRA_USER_PWD)

    target_issue_status_table = get_issues_status(target_factory)
    if target_issue_status_table is None:
        print("Fail to get issue status information. Can not be continued.")
        sys.exit(-1)

    loop = True
    start_at = 0

    source_issue = jira.Issue()

    #     No.  SPIN-Key Exist  Action   New Key, Summary
    print("%7s %-10s %-5s   %-8s %-10s %s" % ("No.", "SPIN-key", "Exist", "Action", "New-key", "Summary"))

    while loop:
        print("="*80)

        # Phase 1. Get issues from SPIN
        source_factory.retrieve_search(jql=DataMap.SPIN_JQL, max_results=JQL_MAX_RESULTS, start_at=start_at)

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
            source_issue.set_data(data.value(str(i)), DataMap.SPIN_JIRA_ISSUE_MAP)
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
                        result = existing_issue.update_status(DataMap.ISSUE_TRANSITION_ID[source_issue.issuestatus])
                        if result == 204:
                            print("[FAIL TO UPDATE ISSUE STATUS]", end="")

                    print()
                else:
                    errormessage = target_factory.value()
                    print("CR-Fail  %-10s " % ("ERROR"), errormessage['errorMessages'])
            else:
                # Phase 2-2. Update existing issue
                print("%5s   " % "Y", end="")
                result = existing_issue.update_status(DataMap.ISSUE_TRANSITION_ID[source_issue.issuestatus])
                result_assign = existing_issue.assign(source_issue.assignee)
                if result == 204 and result_assign == 204:
                    print("Updated %-10s %s" % (existing_issue.key, source_issue.issuestatus))
                elif result == 204 and result_assign == 400:
                    print("Updated %-10s %s. Fail to assign to %s" % (existing_issue.key, source_issue.issuestatus, source_issue.assignee))
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
