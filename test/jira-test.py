__author__ = 'chywoo.park'
import jira

TEST_BASE_URL = "http://jira.score"
factory = jira.JIRAFactory(2)

def test_JIRAIssue():
    issue = factory.createIssue(TEST_BASE_URL, 'chywoo.park', 'tizensdk*10')
    issue.retrieve("TS-17952")


    print("Key: " + issue.key)
    print "Key2: ", issue.value("fields/comment/comments/0/updateAuthor/displayName")

def test_JIRAIssueType():
    issue = factory.createIssue(TEST_BASE_URL, 'chywoo.park', 'tizensdk*10')
    issue.retrieve_issue_types()
    print "Issue type: ", issue.value()

def test_MultiUse():
    SPIN_SERVER_BASE_URL = "http://localhost:2990/jira"
    SCORE_SERVER_BASE_URL = "http://172.21.17.95:8080"

    score_issue = factory.createIssue(SCORE_SERVER_BASE_URL, 'chywoo.park', 'chywoo.park')
    spin_issue = factory.createIssue(SPIN_SERVER_BASE_URL, 'admin', 'admin')

    status = score_issue.retrieve_issue_types()
    print "SCORE STATUS : ", status

    status = spin_issue.retrieve_issue_types()
    print "SPIN  STATUS : ", status


# test_JIRAIssue()
# test_JIRAIssueType()
test_MultiUse()