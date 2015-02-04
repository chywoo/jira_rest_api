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

factory = jira.JIRAFactory()

source_issue = factory.createIssue(SRC_SERVER_BASE_URL, 'chywoo.park', 'score123')
source_issue.set_proxy(PROXYS)

dest_issue = factory.createIssue(DST_SERVER_BASE_URL, 'chywoo.park', 'chywoo.park')
startAt = 0
total_count = 0

print ("Key\t\t\tIssueType\tSummary")

DATA_MAP_TO_DEST = {
    "project":"TEST"

}

loop = True

jql='project in ("Tizen 2.3 Release", "Tizen 2.3 Source Release", "Tizen SDK TF") AND issuetype in (Bug, DEFECT) AND filter = "S-Core(PSLab) Config_User"'

while loop:
    print("="*30)

    status = source_issue.retrieve_search(jql=jql, maxResults=100, startAt=startAt)

    if status != 200:
        print("Fail to retrieve issues")
        sys.exit(-1)

    data = util.VersatileDict(source_issue.value())

    total_count = int(data.value("total"))
    data.data = data.value("issues")

    for i in range(100):
        if i + startAt >= total_count:
            loop = False
            break

        v_key = data.value(str(i)+"/key")
        v_issuetype = data.value(str(i) + "/fields/issuetype/name")
        v_summary = data.value(str(i) + "/fields/summary")
        v_description = data.value(str(i) + "/fields/description")

        print("%d:%d  %s\t%-8s\t%s" % (i + startAt, i, v_key, v_issuetype, v_summary))

        result = dest_issue.create_issue(project_id=DATA_MAP_TO_DEST['project'], summary=v_summary, issuetype=v_issuetype, description=v_description)
        if result != 201:
            print("##### FAIL TO INSERT #####")
            print( dest_issue.value() )
            sys.exit(-1)

    startAt += 100

print("END" * 10)