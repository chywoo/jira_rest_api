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
DST_PROJECT = "TEST"

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


SPIN_JQL='project in ("Tizen 2.3 Release", "Tizen 2.3 Source Release", "Tizen SDK TF") AND issuetype in (Bug, DEFECT) AND filter = "S-Core(PSLab) Config_User"'

JQL_MAX_RESULTS = 100


def check_exist(factory, issue):
    """
    Check the same issue is already inserted.
    :param factory: Instance of JIRAFactory class for target JIRA
    :param issue: Issue information. Instance of Issue class
    :return: True - exist, False - nothing
    """
    check_jql = 'project = %s and "SPIN Issue ID" ~ %s' % (DST_PROJECT, issue.key)

    r = factory.retrieve_search(check_jql, 0, 1)

    if r is None:
        raise ConnectionError("Fail to check if issue exist. Http status %d, %s" % (factory.http_status, factory.value("errorMessages/0")))

    cnt = int(factory.value("total"))

    if cnt == 0:
        return False
    else:
        return True


def create_in_target(factory, issue):
    args = {
        SCORE_JIRA_ISSUE_MAP["spin_id"]: issue.key,
        SCORE_JIRA_ISSUE_MAP["spin_url"]: SRC_SERVER_BASE_URL + "/browse/" + issue.key,
        SCORE_JIRA_ISSUE_MAP["spin_created"]: issue.created,
        SCORE_JIRA_ISSUE_MAP["environment"]: issue.environment
    }
    return factory.create_issue(project_id=DST_PROJECT, summary=issue.summary, issuetype="Bug", description=issue.description, args=args)


def main():
    factory = jira.JIRAFactoryBuilder()

    source_factory = factory.get_factory(SRC_SERVER_BASE_URL, 'chywoo.park', 'score123')
    source_factory.set_proxy(PROXYS)

    target_factory = factory.get_factory(DST_SERVER_BASE_URL, 'robot', 'robot')

    loop = True
    start_at = 0

    source_issue = jira.Issue()

    #     No.  SPIN-Key Exist  Action   New Key, Summary
    print("%7s %-10s %-5s   %-8s %-10s %s" % ("No.", "SPIN-key", "Exist", "Action", "New-key", "Summary"))

    while loop:
        print("="*80)

        # Get issues from SPIN
        source_factory.retrieve_search(jql=SPIN_JQL, max_results=JQL_MAX_RESULTS, start_at=start_at)

        if source_factory.http_status != 200:
            print("Fail to get issues from SPIN")
            sys.exit(-1)

        data = util.VersatileDict(source_factory.value())

        total_count = int(data.value("total"))
        data._data = data.value("issues")

        # Insert issues to target JIRA
        for i in range(JQL_MAX_RESULTS):
            if i + start_at >= total_count:
                loop = False
                break

            source_issue.set_data(data.value(str(i)), SPIN_JIRA_ISSUE_MAP)
            print("%4d:%2d %-10s " % (i + start_at, i, source_issue.key), end="")

            if check_exist(target_factory, source_issue):
                print("%5s   " % "Y", end="")
                print()
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