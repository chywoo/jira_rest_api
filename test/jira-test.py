__author__ = 'chywoo.park'
import jira

TEST_BASE_URL = "http://jira.score"
factory = jira.JIRAFactory()

def test_JIRAIssue():
    issue = factory.createIssue(TEST_BASE_URL, 'chywoo.park', 'tizensdk*10')
    issue.retrieve("TS-17952")


    print("Key: " + issue.key)


test_JIRAIssue()
