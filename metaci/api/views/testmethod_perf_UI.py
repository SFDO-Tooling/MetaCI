from rest_framework import viewsets, response, permissions

from metaci.api.views.testmethod_perf import (
    BuildFlowFilterSet,
    TestMethodPerfFilterSet,
    TestMethodResultFilterSet,
    DEFAULTS,
)


class TestMethodPerfUIApiView(viewsets.ViewSet):
    permission_classes = (permissions.AllowAny,)

    defaults = [
        (item, value)
        for (item, value) in DEFAULTS.__dict__.items()
        if not item.startswith("_")
    ]

    def list(self, request, format=None):
        buildflow_filters = self.collect_filter_defs(BuildFlowFilterSet, [])
        testmethodperf_filters = self.collect_filter_defs(
            TestMethodPerfFilterSet, buildflow_filters.keys()
        )
        testmethodresult_filters = self.collect_filter_defs(
            TestMethodResultFilterSet, buildflow_filters.keys()
        )

        json = {
            "buildflow_filters": buildflow_filters.values(),
            "testmethod_perf": {
                "includable_fields": testmethodperf_filters["include_fields"][
                    "choices"
                ],
                "filters": testmethodperf_filters.values(),
            },
            "testmethod_results": {
                "includable_fields": testmethodresult_filters["include_fields"][
                    "choices"
                ],
                "filters": testmethodresult_filters.values(),
            },
            "defaults": dict(self.defaults),
        }

        return response.Response(json)

    def collect_filter_defs(self, filterSet, exclusion_names):
        json_filter_defs = {}
        for name, filter in filterSet.get_filters().items():
            if name in exclusion_names:
                continue
            if filter.extra.get("choices"):
                choices = filter.extra["choices"]
            else:
                choices = None

            default_value = dict(self.defaults).get(name)
            obj = {
                "name": name,
                "label": filter._label,
                "choices": choices,
                "field_type": filter.field_class.__name__,
                "field_module": filter.field_class.__module__,
                "lookup_expr": filter.lookup_expr,
            }
            if choices:
                obj["choices"] = choices
            if default_value:
                obj["default"] = default_value
            json_filter_defs[name] = obj

        return json_filter_defs
