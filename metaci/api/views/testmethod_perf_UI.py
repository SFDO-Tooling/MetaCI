from rest_framework import viewsets, response

from metaci.api.views.testmethod_perf import (
    BuildFlowFilterSet,
    TestMethodPerfFilterSet,
    DEFAULTS,
)


class TestMethodPerfUIApiView(viewsets.ViewSet):
    defaults = [
        (item, value)
        for (item, value) in DEFAULTS.__dict__.items()
        if not item.startswith("_")
    ]

    def list(self, request, format=None):
        choice_filters, other_buildflow_filters = self.collect_filter_defs(
            BuildFlowFilterSet
        )
        testmethod_choice_filters, other_testmethod_filters = self.collect_filter_defs(
            TestMethodPerfFilterSet
        )

        json = {
            "buildflow_filters": {
                "choice_filters": choice_filters,
                "other_buildflow_filters": other_buildflow_filters,
            },
            "includable_fields": testmethod_choice_filters["include_fields"]["choices"],
            "group_by_fields": testmethod_choice_filters["group_by"]["choices"],
            "defaults": dict(self.defaults),
        }

        return response.Response(json)

    def collect_filter_defs(self, filterSet):
        choice_filters = {}
        other_filters = {}
        for name, filter in filterSet.get_filters().items():
            if filter.extra.get("choices"):
                choices = filter.extra["choices"]
            else:
                choices = None
            obj = {"name": name, "label": filter._label, "choices": choices}
            if choices:
                choice_filters[name] = obj
            else:
                other_filters[name] = obj
        return choice_filters, other_filters
