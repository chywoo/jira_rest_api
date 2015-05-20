#!/usr/bin/env python3
__author__ = 'Sungho Park'

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


DST_SPIN_JQL = "project = SPIN"

from data_mapping import DataMap


JQL_MAX_RESULTS = 100
UNASSIGNED_USER = "robot"   # This 'robot' ID is used as 'Unassigned user'

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


def find_issue_in_source(factory, issue):
    """
    Find a issue with issue key in Key field.
    :param factory: Instance of JIRAFactory class for target JIRA
    :param issue: Issue information. Instance of Issue class
    :return: None - Nothing, instance of Issue class - Issue data
    """
    check_jql = 'key = %s' % (issue.spin_id)

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


def issue_sync(source_factory, target_factory):
    """
    :param source_factory:
    :param target_factory:
    :return:
    """
    loop = True
    start_at = 0
    changed_count = 0

    print (" ####################")
    print (" #### POST WORKS ####")
    print (" ####################")
    print()
    print (" #### Processing issues not assigned to S-Core ####\n")
    # No.    Inter-key     SPIN-key    Summary
    print("%7s %-10s %-10s %s" % ("No.", "Inter-key", "SPIN-key", "Action"))

    while loop:
        print("=" * 80)

        # Phase 1. Get issues from Target
        target_factory.retrieve_search(jql="project = SPIN and status = Closed", max_results=JQL_MAX_RESULTS,
                                       start_at=start_at)

        if target_factory.http_status != 200:
            print("Fail to get issues from Target")
            sys.exit(-1)

        data = util.VersatileDict(target_factory.value())

        total_count = int(data.value("total"))
        data._data = data.value("issues")

        # Phase 2. Find existing issue
        for i in range(JQL_MAX_RESULTS):

            # Exit loop condition
            if i + start_at >= total_count:
                loop = False
                break

            # Make issue instance for convenience
            target_issue = target_factory._new_issue_object(data.value(str(i)), DataMap.TARGET_JIRA_ISSUE_MAP)
            print("%4d:%2d %-10s  %-10s " % (i + start_at, i, target_issue.key, target_issue.spin_id), end="")

            if target_issue.spin_id is None:
                print("Invalid Issue. SPIN ID is none. Skip")
                continue

            try:
                found_issue = find_issue_in_source(source_factory, target_issue)
            except ConnectionError as err:
                print(err, end="")
                found_issue = None

            # Phase 3. Change assignee
            if found_issue is None:
                continue

            # Phase 4. Change issue status. In fact, this phase  is not necessary work, but convenient work for viewing
            result = target_issue.update_spin_resolved(found_issue.resolutiondate)

            if result == 204:
                print("RSV: updated with %s " % found_issue.resolutiondate, end="")
            else:
                errmsg = target_issue.value()
                print("RSV: [%s] " % (errmsg['errors']), end="")

            print("")

        start_at += JQL_MAX_RESULTS

    print("")
    print("Total changed: %d" % (changed_count))


def main():
    # Initialize
    factory = jira.JIRAFactoryBuilder()

    source_factory = factory.get_factory(SRC_SERVER_BASE_URL, DataMap.SRC_JIRA_USER_ID, DataMap.SRC_JIRA_USER_PWD)
    source_factory.set_permission(jira.PERMISSION_READ)
    source_factory.set_proxy(PROXYS)

    target_factory = factory.get_factory(DST_SERVER_BASE_URL, DataMap.DST_JIRA_USER_ID, DataMap.DST_JIRA_USER_PWD)
    target_factory.set_permission(jira.PERMISSION_WRITE)

    target_issue_status_table = get_issues_status(target_factory)
    if target_issue_status_table is None:
        print("Fail to get issue status information. Can not be continued.")
        sys.exit(-1)

    # start issue sync
    issue_sync(source_factory, target_factory)

    print("END" * 10)


def print_usage():
    print("Usage: python3 fieldsynchtool.py <source jira HTTP URL> <target jira HTTP URL>")
    print("       ex) migration.py http://100.100.100.1/jira http://100.100.100.2:8080\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
    else:
        SRC_SERVER_BASE_URL = sys.argv[1]
        DST_SERVER_BASE_URL = sys.argv[2]

        main()
