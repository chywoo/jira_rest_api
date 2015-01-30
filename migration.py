__author__ = 'chywoo.park'

import jira
import util

SPIN_SERVER_BASE_URL = "http://172.21.17.95:8080"
# SPIN_SERVER_BASE_URL = "http://168.219.209.56/jira"
SCORE_SERVER_BASE_URL = "http://localhost:2990/jira"

factory = jira.JIRAFactory()

spin_issue = factory.createIssue(SPIN_SERVER_BASE_URL, 'chywoo.park', 'chywoo.park')
startAt = 0
total_count = 0

print ("Key\t\t\tIssueType\tSummary")

loop = True
while loop:
    print("="*30)
    spin_issue.retrieve_search("project=TS&maxResults=100&startAt=" + str(startAt))

    data = util.VersatileDict(spin_issue.value())

    total_count = int(data.value("total"))
    data.data = data.value("issues")

    for i in range(100):
        if i + startAt >= total_count:
            loop = False
            break

        print( "%d:%d  %s\t%-8s\t%s" % ( i + startAt, i, data.value(str(i)+ "/key"), data.value(str(i) + "/fields/issuetype/name"), data.value(str(i) + "/fields/summary")))

    startAt += 100

print "END" * 10