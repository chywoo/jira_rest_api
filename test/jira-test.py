__author__ = 'chywoo.park'
import jira

TEST_BASE_URL = "http://jira.score"
factory = jira.JIRAFactory()

def test_JIRAIssue():
    issue = factory.createIssue(TEST_BASE_URL, 'chywoo.park', 'tizensdk*10')
    issue.retrieve("TS-17952")


    print("Key: " + issue.key)
    print "Key2: ", issue.value("fields/comment/comments/0/updateAuthor/displayName")

def test_JIRAIssueType():
    issue = factory.createIssue(TEST_BASE_URL, 'chywoo.park', 'tizensdk*10')
    issue.retrieve_issue_types()
    print "Issue type: ", issue.value()


test_JIRAIssue()
test_JIRAIssueType()