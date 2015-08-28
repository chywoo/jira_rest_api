__author__ = 'chywoo.park'

import sys
import jira
import util
from jira import Issue

SRC_SERVER_BASE_URL = ""
PROXYS = {
    'http': 'http://172.21.17.105:3128',
    'https': 'http://172.21.17.105:3128'
}
DST_SERVER_BASE_URL = ""
DST_PROJECT = "SPIN"

from data_mapping import DataMap

JQL_MAX_RESULTS = 100
UNASSIGNED_USER = "robot"  # This 'robot' ID is used as 'Unassigned user'


def get_issues_status(connection):
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

    :param connection:
    :return: dictionary formated like {<Issue status name>:<Issue status id>}
    """
    issue_status = {}

    connection.set_resturl("/status")
    if connection.request() == 200:
        data = connection.value()

        for i in range(len(data)):
            issue_status[data[i]["name"]] = data[i]["id"]

        return issue_status
    else:
        return None


def find_one_issue(connection, jsql):
    """
    Find one issue from specified connection.

    :param connection: factory instance
    :param jsql: JQL to find a issue.
    :return: Issue if just one found, None if not found.
    :rtype: Issue
    :raise LookupError: If many issues are found, this error raises.
    """
    result = connection.retrieve_search(jsql, 0, 1)

    if result is None:
        raise ConnectionError("Fail to check if issue exist. Http status %d, %s" %
                              (connection.http_status, connection.value("errorMessages/0")))

    cnt = int(connection.value("total"))

    if cnt == 0:
        return None
    elif cnt == 1:
        return connection.get_issue(0)
    else:
        raise LookupError("Many issues are found with '%s'" % jsql)


def find_issue_in_target(connection, issue):
    """
    Find a issue with issue key in SPIN Issue ID field.

    :param connection: Instance of JIRAConnection class for target JIRA
    :param issue: Issue information. Instance of Issue class
    :return: None - Nothing, instance of Issue class - Issue data
    """
    check_jql = 'project = %s and "SPIN Issue ID" ~ %s' % (DST_PROJECT, issue.key)

    return find_one_issue(connection, check_jql)


def find_issue_in_source(connection, issue):
    """
    Find a issue with issue key in Key field.
    :param connection: Instance of JIRAConnection class for target JIRA
    :param issue: Issue information. Instance of Issue class
    :return: None - Nothing, instance of Issue class - Issue data
    """
    check_jql = 'key = %s' % issue.spin_id

    return find_one_issue(connection, check_jql)


def issue_create(connection, issue):
    """
    Create a issue.

    :param connection: 이슈를 생성한 factory
    :param issue:
    """
    return_code = 0
    return_msg = "OK"

    args = {
        DataMap.TARGET_JIRA_ISSUE_MAP["spin_id"]: issue.key,
        DataMap.TARGET_JIRA_ISSUE_MAP["spin_url"]: SRC_SERVER_BASE_URL + "/browse/" + issue.key,
        DataMap.TARGET_JIRA_ISSUE_MAP["spin_created"]: issue.created,
        DataMap.TARGET_JIRA_ISSUE_MAP["environment"]: getattr(issue, "environment", None)
    }

    target_issuetype = "Bug"

    if issue.issuetype == "Task":
        target_issuetype = "Task"

    result = connection.create_issue(project_id=DST_PROJECT, summary=issue.summary, issuetype=target_issuetype,
                                description=issue.description, args=args)

    if result == 201:
        pass
    else:
        errmsg = connection.value()
        return_code = result
        if "errorMessages" in errmsg:
            return_msg = "Creation failed. Message: %s" % errmsg["errorMessages"][0]

    return {"CODE": return_code, "MESSAGE": return_msg}


def issue_assign(issue, name, reassign=False, reassign_name="robot"):
    """
    Change assignee.

    :param issue: 네트웍에 연결된 Issue 클래스의 인스턴스
    :param name: 변경하고자하는 사용자.
    :param reassign: name으로 담당자 변경 실패시 reassign_name으로 재변경한다.
    :param reassign_name: 재변경할 담당자명
    :return: {CODE:xxx, MESSAGE:xxx} 형태
    :rtype: dict
    """
    return_code = 0
    return_msg = "OK"

    # assign user
    assert isinstance(issue, Issue)
    result = issue.assign(name)
    errmsg = issue.value()

    if result == 204:
        pass
    else:  # if fail to assign to member
        try:
            msg = errmsg["errors"]["assignee"]

            if issue.assignee != UNASSIGNED_USER:   # skip reassign if current assignee is UNASSIGNED_USER.
                assert isinstance(reassign, bool)
                if msg is not None and reassign:
                    assert isinstance(reassign_name, str)
                    result = issue.assign(reassign_name)

                if result == 204:
                    return_code = 0
                    return_msg = "Reassign to %s." % reassign_name
                else:
                    return_code = 400
            else:
                return_code = result
                return_msg = "Fail to assign."
        except KeyError:
            return_code = result
            if "errorMessages" in errmsg:
                return_msg = "Assign failed. Message: %s" % errmsg["errorMessages"][0]
            else:
                return_msg = "Assign failed."

    return {"CODE": return_code, "MESSAGE": return_msg}


def issue_change_status(issue, status):
    """
    Change issue status.

    :param issue: connected Issue object
    :param status:
    :return: {CODE:xxx, MESSAGE:xxx} data
    :rtype: dict
    """
    return_code = 0
    return_msg = "OK"

    assert isinstance(issue, Issue)
    result = issue.update_status(status)
    errmsg = issue.value()

    if result == 204:
        pass
    else:
        return_code = result

        if "errorMessages" in errmsg:
            return_msg = errmsg["errorMessages"][0]

    return {"CODE": return_code, "MESSAGE": return_msg}


def issue_importing(source_connection, target_connection):
    """
    Issue migration part. In this function, all issue of source jira are copied to target jira,
    and issue status and assignee are changed.

    :param source_connection:
    :param target_connection:
    :return:
    """
    loop = True
    start_at = 0
    source_issue = jira.Issue()
    created_count = 0

    # No.  SPIN-Key Exist  Action   New Key, Summary
    print("%7s %-10s %-5s   %-8s %-10s %s" % ("No.", "SPIN-key", "Exist", "Action", "New-key", "Summary"))

    while loop:
        print("=" * 80)

        # Phase 1. Get created issues from SPIN
        source_connection.retrieve_search(jql=DataMap.get_new_issues_jql(), max_results=JQL_MAX_RESULTS, start_at=start_at)

        if source_connection.http_status != 200:
            print("Fail to get issues from SPIN")
            sys.exit(-1)

        data = util.VersatileDict(source_connection.value())

        total_count = int(data.value("total"))
        data._data = data.value("issues")

        # Phase 2. Insert issues to target JIRA
        for i in range(JQL_MAX_RESULTS):

            # Exit loop condition
            if i + start_at >= total_count:
                loop = False
                break

            # Make issue instance for convenience. source_issue is not a connected object.
            source_issue.set_data(data.value(str(i)))
            print("%4d:%2d %-10s " % (i + start_at, i, source_issue.key), end="")

            try:
                existing_issue = find_issue_in_target(target_connection, source_issue)
            except LookupError as e:
                print(str(e))

            if not existing_issue:
                # Phase 1. Create issue
                print("%5s   " % "N", end="")

                created_count += 1

                r = issue_create(target_connection, source_issue)

                if r["CODE"] == 0:
                    print("Created %-10s %s" % (target_connection.value("key"), source_issue.summary), end="")
                else:
                    print("CR: %-10s" % r["MESSAGE"], end="")
            else:
                print("%5s   " % "Y", end="")

            print("")

        start_at += JQL_MAX_RESULTS

    print("")
    print("Total imported: %d" % created_count)

    return created_count


def update_existing_issues(source_connection, target_connection):
    """
    Update issues of target connection

    :param source_connection:
    :param target_connection:
    :return:
    """
    loop = True
    start_at = 0
    changed_count = 0


    # No.    Inter-key     SPIN-key    Summary
    print("%7s %-10s %-10s %s" % ("No.", "Target-key", "Source-key", "Action"))

    while loop:
        print("=" * 80)

        # STEP 1. Get issues from Target
        target_connection.retrieve_search(jql=DataMap.get_target_assigned_issue_jql(),
                                       max_results=JQL_MAX_RESULTS,
                                       start_at=start_at)

        if target_connection.http_status != 200:
            print("Fail to get issues from Target")
            sys.exit(-1)

        data = util.VersatileDict(target_connection.value())

        total_count = int(data.value("total"))
        data._data = data.value("issues")

        # STEP 2. Find existing issue
        for i in range(JQL_MAX_RESULTS):
            assign_flag = False
            status_flag = False

            new_assignee = ""
            new_status = ""

            # Exit loop condition
            if i + start_at >= total_count:
                loop = False
                break

            # Make issue instance for convenience
            target_issue = target_connection._new_issue_object(data.value(str(i)), DataMap.TARGET_JIRA_ISSUE_MAP)
            print("%4d:%2d %-10s %-10s " % (i + start_at, i, target_issue.key, target_issue.spin_id), end="")

            if target_issue.spin_id is None:  # if the issue is not imported from source.
                print("Invalid Issue. SPIN ID is none. Skip.")
                continue

            # STEP 3. Find source issue
            try:
                found_issue = find_issue_in_source(source_connection, target_issue)
            except ConnectionError as err:
                print(str(err), end="")
                found_issue = None
            except LookupError as err:
                print(str(err), end="")

            # STEP 4. Compare issues
            if found_issue and DataMap.get_user(found_issue.assignee) != DataMap.get_user(target_issue.assignee):
                assign_flag = True
                new_assignee = DataMap.get_user(found_issue.assignee)
            else:
                assign_flag = False

            if found_issue and DataMap.get_issue_status(found_issue.issuestatus) != target_issue.issuestatus:
                status_flag = True
                new_status = DataMap.get_issue_status(found_issue.issuestatus)
            else:
                status_flag = False

            if found_issue and found_issue.key != target_issue.spin_id:
                # TODO
                pass

            if not assign_flag and not status_flag:  # if not changed, go next.
                print("Skip")
                continue

            # STEP 4. Change assignee
            if assign_flag:
                reporter = target_issue.reporter

                if new_status in ("Resolved", "Closed") and reporter == new_assignee:
                    print("USR: automatic assign by issue resolve. Reporter: %s, Current assignee: %s"
                          % (reporter, target_issue.assignee))
                else:
                    r = issue_assign(target_issue, new_assignee, True, UNASSIGNED_USER)
                    print("USR: %s -> %s : %s " % (target_issue.assignee, new_assignee, r["MESSAGE"]), end="")

            # STEP 5. Change status
            if status_flag:
                # if closed issue, set resolved date before status changing, because closed issue can't be modified.
                if new_status == "Closed":
                    target_issue.update_spin_resolved(found_issue.resolutiondate)

                transition_id = DataMap.get_transition_id(new_status)
                r = issue_change_status(target_issue, transition_id)
                print("STAT: %s -> %s : %s " % (target_issue.issuestatus, new_status, r["MESSAGE"]), end="")

                if new_status == "Closed":
                    print("with Resolved date '%s'" % found_issue.resolutiondate, end="")

            print("")

            changed_count += 1

        start_at += JQL_MAX_RESULTS

    print("")
    print("Total changed: %d" % changed_count)


def main():
    # Initialize
    factory = jira.JIRAFactory()

    source_connection = factory.get_connection(SRC_SERVER_BASE_URL, DataMap.SRC_JIRA_USER_ID,
                                               DataMap.SRC_JIRA_USER_PWD, DataMap.SPIN_JIRA_ISSUE_MAP)
    source_connection.set_permission(jira.PERMISSION_READ)
    source_connection.set_proxy(PROXYS)

    target_connection = factory.get_connection(DST_SERVER_BASE_URL, DataMap.DST_JIRA_USER_ID, DataMap.DST_JIRA_USER_PWD,
                                         DataMap.TARGET_JIRA_ISSUE_MAP)
    target_connection.set_permission(jira.PERMISSION_WRITE)

    target_issue_status_table = get_issues_status(target_connection)
    if target_issue_status_table is None:
        print("Fail to get issue status information. Can not be continued.")
        sys.exit(-1)

    # STEP 1. Updating issues.
    print("########################")
    print("#### ISSUE UPDATING ####")
    print("########################")
    print("")
    update_existing_issues(source_connection, target_connection)

    print("")

    # STEP 2. Imporint new issues
    print("#########################")
    print("#### ISSUE IMPORTING ####")
    print("#########################")
    print("")
    created_count = issue_importing(source_connection, target_connection)

    # STEP 3. Updating issues for new imported issues.
    if created_count > 0:
        print("##########################")
        print("#### ISSUE UPDATING 2 ####")
        print("##########################")
        print("")
        update_existing_issues(source_connection, target_connection)

    print("")
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
