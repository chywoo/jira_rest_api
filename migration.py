__author__ = 'chywoo.park'

import jira
import util

SPIN_SERVER_BASE_URL = "http://172.21.17.95:8080"
# SPIN_SERVER_BASE_URL = "http://168.219.209.56/jira"
SCORE_SERVER_BASE_URL = "http://localhost:2990/jira"

factory = jira.JIRAFactory()

spin_issue = factory.createIssue(SPIN_SERVER_BASE_URL, 'chywoo.park', 'chywoo.park')
spin_issue.retrieve_search("project=TS")

data = util.VersatileDict(spin_issue.value())
print spin_issue.value()

issue_count =  int(data.value("total"))
data.data = data.value("issues")

print ("Key\t\t\tIssueType\tSummary")

for i in range(issue_count):
    print( "%s\t%-8s\t%s" % ( data.value(str(i)+ "/key"), data.value(str(i) + "/fields/issuetype/name"), data.value(str(i) + "/fields/summary")))
