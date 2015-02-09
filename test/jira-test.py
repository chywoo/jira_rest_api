__author__ = 'chywoo.park'
import jira

TEST_BASE_URL = "http://172.21.17.95:8080"
SPIN_BASE_URL = "http://172.21.17.95:8080"
SCORE_BASE_URL = "http://172.21.17.95:2990/jira"

builder = jira.JIRAFactoryBuilder(2)


def test_JIRAIssue():
    print
    print("="*80)
    issue_factory = builder.get_factory(TEST_BASE_URL, 'resttest', 'resttest')
    result = issue_factory.retrieve_issue("REST-1")

    if result is None:
        print("Fail to get issue. HTTP code is ", issue_factory.http_status)
        return

    print("Key1: ", issue_factory.value('key'))
    print("Key2: ", result.key)
    print("Status: ", issue_factory.http_status)


def test_JIRAIssueType():
    print
    print("="*80)
    issue_factory = builder.get_factory(TEST_BASE_URL, 'resttest', 'resttest')
    issue_factory.retrieve_issue_types()
    print("Issue type: ", issue_factory.value())


def test_MultiUse():
    print
    print("="*80)
    score_issue_factory = builder.get_factory(SCORE_BASE_URL, 'admin', 'admin')
    spin_issue_factory = builder.get_factory(SPIN_BASE_URL, 'resttest', 'resttest')

    status = score_issue_factory.retrieve_issue_types()
    print("SCORE STATUS : ", status)

    status = spin_issue_factory.retrieve_issue_types()
    print("SPIN  STATUS : ", status)

def test_search():
    print
    print("="*80)
    issue_factory = builder.get_factory(TEST_BASE_URL, 'resttest', 'resttest')
    issue_factory.retrieve_search('project=REST')

    print("Issue list: ", issue_factory.value())

def test_create():
    print
    print("="*80)
    issue_factory = builder.get_factory(TEST_BASE_URL, 'resttest', 'resttest')
    issue_factory.create_issue("REST", "테스트Summary", "Task" )
    print("Issue Info: ", issue_factory.value())

def test_issueobject():
    print()
    print("="*80)

    issue_factory = builder.get_factory(TEST_BASE_URL, 'resttest', 'resttest')
    issue_factory.retrieve_search('project=REST')

    print("Key\t\tIssueType\tSummary")
    print("="*80)
    total = issue_factory.value('total')

    for i in range(total):
        issue = jira.Issue(issue_factory.value("issues/" + str(i)))
        print("%s\t%-8s\t%s\t%s\t%s" % (issue.key, issue.issuetype, issue.summary, issue.assignee, issue.environment))


test_JIRAIssue()
test_JIRAIssueType()
test_MultiUse()
test_search()
test_create()
test_issueobject()