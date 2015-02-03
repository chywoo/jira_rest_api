#-*- coding: utf-8 -*-
__author__ = 'chywoo.park'

import jira
import util
import time

SRC_SERVER_BASE_URL = "http://172.21.17.95:8080"
DST_SERVER_BASE_URL = "http://172.21.17.95:2990/jira"

factory = jira.JIRAFactory()

source_issue = factory.createIssue(SRC_SERVER_BASE_URL, 'chywoo.park', 'chywoo.park')
dest_issue = factory.createIssue(DST_SERVER_BASE_URL, 'admin', 'admin')
startAt = 0
total_count = 0

print ("Key\t\t\tIssueType\tSummary")

DATA_MAP_TO_DEST = {
    "project":"TEST"

}

loop = True
while loop:
    print("="*30)
    source_issue.retrieve_search("project=TS&maxResults=100&startAt=" + str(startAt))

    data = util.VersatileDict(source_issue.value())

    total_count = 10 #int(data.value("total"))
    data.data = data.value("issues")

    for i in range(100):
        if i + startAt >= total_count:
            loop = False
            break

        v_key = data.value(str(i)+"/key")
        v_issuetype = data.value(str(i) + "/fields/issuetype/name")
        v_summary = data.value(str(i) + "/fields/summary")

        print("%d:%d  %s\t%-8s\t%s" % (i + startAt, i, v_key, v_issuetype, v_summary))

        dest_issue.create_issue(DATA_MAP_TO_DEST['project'], v_summary, v_issuetype)

    startAt += 100

print "END" * 10