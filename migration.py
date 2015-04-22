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


def create_in_target(factory, issue):

    # Set additional fields
    args = {
        DataMap.TARGET_JIRA_ISSUE_MAP["spin_id"]: issue.key,
        DataMap.TARGET_JIRA_ISSUE_MAP["spin_url"]: SRC_SERVER_BASE_URL + "/browse/" + issue.key,
        DataMap.TARGET_JIRA_ISSUE_MAP["spin_created"]: issue.created,
        DataMap.TARGET_JIRA_ISSUE_MAP["environment"]: issue.environment
    }

    target_issuetype="Bug"

    if issue.issuetype == "Task":
        target_issuetype = "Task"

    return factory.create_issue(project_id=DST_PROJECT, summary=issue.summary, issuetype=target_issuetype, description=issue.description, args=args)


def issue_migration(source_factory, target_factory):
    """
    Issue migration part. In this function, all issue of source jira are copied to target jira,
    and issue status and assignee are changed.
    :param source_factory:
    :param target_factory:
    :return:
    """
    loop = True
    start_at = 0
    source_issue = jira.Issue()
    # No.  SPIN-Key Exist  Action   New Key, Summary
    print("%7s %-10s %-5s   %-8s %-10s %s" % ("No.", "SPIN-key", "Exist", "Action", "New-key", "Summary"))
    while loop:
        print("=" * 80)

        # Phase 1. Get issues from SPIN
        source_factory.retrieve_search(jql=DataMap.get_jql(), max_results=JQL_MAX_RESULTS, start_at=start_at)

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
                # Phase 1. Create issue
                print("%5s   " % "N", end="")

                result = create_in_target(target_factory, source_issue)

                if result == 201:
                    print("Created %-10s %s" % (target_factory.value("key"), source_issue.summary), end="")

                    # Update issue status because issue status is "Open" at creation.
                    existing_issue = find_issue_in_target(target_factory, source_issue)
                    if not existing_issue:
                        print("CR-Fail: ABNORMALLY ISSUE CREATED]", end="")
                        continue
                else:
                    errmsg = target_factory.value()
                    print("CR-Fail  %-10s " % ("ERROR"), errmsg['errorMessages'])
                    continue

            result_issue_status = 0
            result_assign = 0

            print("%5s   " % "Y", end="")

            # Phase 2. Update issue status

            target_status = DataMap.get_issue_status(source_issue.issuestatus)

            if existing_issue.issuestatus != target_status:
                target_transition_id = DataMap.get_transition_id(source_issue.issuestatus)
                result_issue_status = existing_issue.update_status(target_transition_id)

                if result_issue_status == 204:
                    print("STA: %s -> %s " % (existing_issue.issuestatus, target_status), end="")
                else:
                    errmsg = existing_issue.value()
                    print("STA: [%s] " % (errmsg['errors']), end="")

            # Phase 3. Change assignee

            assigned_user = DataMap.get_user(source_issue.assignee)

            if existing_issue.assignee != assigned_user:
                result_assign = existing_issue.assign(assigned_user)

                if result_assign == 204:
                    print("USR: %s -> %s " % (existing_issue.assignee, assigned_user), end="")
                else:
                    errmsg = existing_issue.value()
                    print("USR: [%s] " % (errmsg['errors']), end="")

                    result_assign = existing_issue.assign(UNASSIGNED_USER)

            if result_assign == 0 and result_issue_status == 0:
                print("No change", end="")

            print("")

        start_at += JQL_MAX_RESULTS


def migration_post_work(source_factory, target_factory):
    """
    :param source_factory:
    :param target_factory:
    :return:
    """
    loop = True
    start_at = 0
    changed_count = 0

    print (" #### POST WORKD ####")
    # No.    Inter-key     SPIN-key    Summary
    print("%7s %-10s %-10s %s" % ("No.", "Inter-key", "SPIN-key", "Action"))

    while loop:
        print("=" * 80)

        # Phase 1. Get issues from Target
        target_factory.retrieve_search(jql=DataMap.get_target_assigned_issue_jql(), max_results=JQL_MAX_RESULTS,
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

            found_issue = find_issue_in_source(source_factory, target_issue)

            if not found_issue:
                new_assignee = "robot"
            elif DataMap.get_user(found_issue.assignee) != target_issue.assignee:
                new_assignee = DataMap.get_user(found_issue.assignee)
            else:
                new_assignee = None

            if new_assignee is not None:
                changed_count += 1

                result = target_issue.assign(new_assignee)
                if result == 204:
                    print("USR: %s -> %s " % (target_issue.assignee, new_assignee), end="")
                else:
                    errmsg = target_issue.value()
                    print("Assign Fail. ", errmsg['errorMessages'], end="")

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

    # Migrate issues.
    issue_migration(source_factory, target_factory)

    print ("")
    # Migration post work
    migration_post_work(source_factory, target_factory)


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
