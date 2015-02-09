#-*- coding: utf-8 -*-
__author__ = 'chywoo.park'

import sys
import jira
import util
import time

SRC_SERVER_BASE_URL = "http://168.219.209.56/jira"
# SRC_SERVER_BASE_URL = "http://172.21.17.95:8080"
DST_SERVER_BASE_URL = "http://172.21.17.95:8080"
PROXYS = {
    'http':'http://172.21.17.105:3128',
    'https': 'http://172.21.17.105:3128'
}

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
    "created": "/fields/created",
    "spin_id": "/fields/customfield_10100",
    "spin_url": "/fields/customfield_10101"
}

# For issue creation and update
SCORE_JIRA_CUSTOM_FIELDS = {
    "spind_id": "customfield_10100",
    "spind_url": "customfield_10101"
}

CUSTOM_SPIN_ID = "customfield_10100"
CUSTOM_SPIN_URL = "customfield_10101"

factory = jira.JIRAFactoryBuilder()

source_factory = factory.get_factory(SRC_SERVER_BASE_URL, 'chywoo.park', 'score123')
source_factory.set_proxy(PROXYS)

target_factory = factory.get_factory(DST_SERVER_BASE_URL, 'chywoo.park', 'chywoo.park')

startAt = 0
total_count = 0

print ("Key\t\t\tIssueType\tSummary")

DATA_MAP_TO_DEST = {
    "project":"TEST"

}

loop = True

jql='project in ("Tizen 2.3 Release", "Tizen 2.3 Source Release", "Tizen SDK TF") AND issuetype in (Bug, DEFECT) AND filter = "S-Core(PSLab) Config_User"'


source_issue = jira.Issue()

while loop:
    print("="*30)

    source_factory.retrieve_search(jql=jql, max_results=100, start_at=startAt)

    if source_factory.http_status != 200:
        print("Fail to retrieve issues")
        sys.exit(-1)

    data = util.VersatileDict(source_factory.value())

    total_count = 10 # int(data.value("total"))
    data.data = data.value("issues")

    for i in range(100):
        if i + startAt >= total_count:
            loop = False
            break

        source_issue.set_data(data.value(str(i)), SPIN_JIRA_ISSUE_MAP)

        print("%d:%d  %s\t%-8s\t%s" % (i + startAt, i, source_issue.key, source_issue.issuetype, source_issue.summary))
        args={
            SCORE_JIRA_ISSUE_MAP["spin_id"]: source_issue.key,
            SCORE_JIRA_ISSUE_MAP["spin_url"]: SRC_SERVER_BASE_URL + "/browse/" + source_issue.key,
            SCORE_JIRA_ISSUE_MAP["environment"]: source_issue.environment,
            SCORE_JIRA_ISSUE_MAP["created"]: source_issue.created
        }

        result = target_factory.create_issue(project_id="TEST", summary=source_issue.summary, issuetype=source_issue.issuetype, description=source_issue.description, args=args)
        if result != 201:
            print("##### FAIL TO INSERT #####")
            print( target_factory.value() )
            sys.exit(-1)

    startAt += 100

print("END" * 10)