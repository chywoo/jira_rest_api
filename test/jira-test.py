__author__ = 'chywoo.park'
import jira

TEST_BASE_URL = "http://172.21.17.95:8080"
SPIN_BASE_URL = "http://172.21.17.95:8080"
SCORE_BASE_URL = "http://172.21.17.95:2990/jira"

factory = jira.JIRAFactoryBuilder(2)


def test_JIRAIssue():
    print
    print("="*80)
    issue = factory.get_factory(TEST_BASE_URL, 'chywoo.park', 'chywoo.park')
    issue.retrieve_issue("TS-17674")

    print("Key: " + issue.key)
    print("Key2: ", issue.value("fields/comment"))


def test_JIRAIssueType():
    print
    print("="*80)
    issue = factory.get_factory(TEST_BASE_URL, 'chywoo.park', 'chywoo.park')
    issue.retrieve_issue_types()
    print("Issue type: ", issue.value())


def test_MultiUse():
    print
    print("="*80)
    score_issue = factory.get_factory(SCORE_BASE_URL, 'admin', 'admin')
    spin_issue = factory.get_factory(SPIN_BASE_URL, 'chywoo.park', 'chywoo.park')

    status = score_issue.retrieve_issue_types()
    print("SCORE STATUS : ", status)

    status = spin_issue.retrieve_issue_types()
    print("SPIN  STATUS : ", status)

def test_search():
    print
    print("="*80)
    issue = factory.get_factory(SCORE_BASE_URL, 'admin', 'admin')
    issue.retrieve_search('project=TEST')

    print("Issue list: ", issue.value())

def test_create():
    print
    print("="*80)
    issue = factory.get_factory(SCORE_BASE_URL, 'admin', 'admin')
    issue.create_issue("TEST", "테스트Summary", "Task" )
    print("Issue Info: ", issue.value())


test_JIRAIssue()
test_JIRAIssueType()
test_MultiUse()
test_search()
test_create()