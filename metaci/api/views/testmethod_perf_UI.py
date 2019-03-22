from rest_framework import viewsets, response

from metaci.api.views.testmethod_perf import BuildFlowFilterSet, TestMethodPerfFilterSet


class TestMethodPerfUIApiView(viewsets.ViewSet):
    def list(self, request, format=None):
        buildflow_filters = self.collect_filter_defs(BuildFlowFilterSet)
        testmethod_filters = self.collect_filter_defs(TestMethodPerfFilterSet)

        json = {
            "buildflow_filters": buildflow_filters,
            "includable_fields": testmethod_filters["include_fields"]["choices"],
            "group_by_fields": testmethod_filters["group_by"]["choices"],
        }
        return response.Response(json)

    def collect_filter_defs(self, filterSet):
        rc = {}
        for name, filter in filterSet.get_filters().items():
            if filter.extra.get("choices"):
                choices = [name for (name, value) in filter.extra["choices"]]
            else:
                choices = None
            obj = {"name": name, "label": filter._label, "choices": choices}
            rc[name] = obj
        return rc
