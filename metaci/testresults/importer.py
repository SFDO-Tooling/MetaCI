import urllib
import json
from metaci.testresults.models import TestClass
from metaci.testresults.models import TestMethod
from metaci.testresults.models import TestResult

STATS_MAP = {
    'email_invocations': 'Number of Email Invocations',
    'soql_queries': 'Number of SOQL queries',
    'future_calls': 'Number of future calls',
    'dml_rows': 'Number of DML rows',
    'cpu_time': 'Maximum CPU time',
    'query_rows': 'Number of query rows',
    'dml_statements': 'Number of DML statements',
    'mobile_apex_push': 'Number of Mobile Apex push calls',
    'heap_size': 'Maximum heap size',
    'sosl_queries': 'Number of SOSL queries',
    'queueable_jobs': 'Number of queueable jobs added to the queue',
    'callouts': 'Number of callouts',
    'test_email_invocations': 'TESTING_LIMITS: Number of Email Invocations',
    'test_soql_queries': 'TESTING_LIMITS: Number of SOQL queries',
    'test_future_calls': 'TESTING_LIMITS: Number of future calls',
    'test_dml_rows': 'TESTING_LIMITS: Number of DML rows',
    'test_cpu_time': 'TESTING_LIMITS: Maximum CPU time',
    'test_query_rows': 'TESTING_LIMITS: Number of query rows',
    'test_dml_statements': 'TESTING_LIMITS: Number of DML statements',
    'test_mobile_apex_push': 'TESTING_LIMITS: Number of Mobile Apex push calls',
    'test_heap_size': 'TESTING_LIMITS: Maximum heap size',
    'test_sosl_queries': 'TESTING_LIMITS: Number of SOSL queries',
    'test_queueable_jobs': 'TESTING_LIMITS: Number of queueable jobs added to the queue',
    'test_callouts': 'TESTING_LIMITS: Number of callouts',
}

LIMIT_TYPES = (
            'email_invocations',
            'soql_queries',
            'future_calls',
            'dml_rows',
            'cpu_time',
            'query_rows',
            'dml_statements',
            'mobile_apex_push',
            'heap_size',
            'sosl_queries',
            'queueable_jobs',
            'callouts',
        )


def import_test_results(build_flow, results):
    classes = {}
    methods = {}

    for result in results:
        class_and_method = '%s.%s' % (result['ClassName'], result['Method'])

        testclass = classes.get(result['ClassName'], None)
        if not testclass:
            try:
                testclass = TestClass.objects.get(name = result['ClassName'], repo=build_flow.build.repo)
            except TestClass.DoesNotExist:
                testclass = TestClass(name = result['ClassName'], repo=build_flow.build.repo)
                testclass.save()
            classes[result['ClassName']] = testclass

        method = methods.get(class_and_method, None)
        if not method:
            try:
                method = TestMethod.objects.get(testclass = testclass.id, name = result['Method'])
            except TestMethod.DoesNotExist:
                method = TestMethod(testclass = testclass, name = result['Method'])
                method.save()
            methods[result['Method']] = method

        duration = None
        if 'Stats' in result and result['Stats'] and 'duration' in result['Stats'] and result['Stats']['duration']:
            duration = result['Stats']['duration']
       
        testresult = TestResult(
            build_flow = build_flow,
            method = method,
            duration = duration,
            outcome = result['Outcome'],
            stacktrace = result['StackTrace'],
            message = result['Message'],
            source_file = result['SourceFile']
        )
        populate_limit_fields(testresult, result['Stats'])
        testresult.save()

    return build_flow

def populate_limit_fields(testresult, code_unit):
        for limit_type in LIMIT_TYPES:
            try:
                test_used = code_unit[STATS_MAP['test_%s' % limit_type]]['used']
                test_allowed = code_unit[STATS_MAP['test_%s' % limit_type]]['allowed']

                test_percent = None

                if test_used is not None and test_allowed:
                    test_percent = (test_used * 100) / test_allowed
            
                setattr(testresult, 'test_%s_used' % limit_type,  test_used)
                setattr(testresult, 'test_%s_allowed' % limit_type, test_allowed)
                setattr(testresult, 'test_%s_percent' % limit_type, test_percent)
            except KeyError:
                continue

        worst_limit_test = None
        worst_limit_test_percent = None

        for limit_type in LIMIT_TYPES:
            percent_test = getattr(testresult, 'test_%s_percent' % limit_type)

            if percent_test > worst_limit_test_percent:
                worst_limit_test = 'test_%s_percent' % limit_type
                worst_limit_test_percent = percent_test

        testresult.worst_limit = worst_limit_test
        testresult.worst_limit_percent = worst_limit_test_percent
        testresult.worst_limit_test = worst_limit_test
        testresult.worst_limit_test_percent = worst_limit_test_percent
