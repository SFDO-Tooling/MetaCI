from rest_framework import viewsets, response, permissions

from metaci.api.views.testmethod_perf_fast import BuildFlowFilterSet, DEFAULTS

from metaci.api.views.testmethod_perf_fast import TestMethodPerfFilterSet
from metaci.api.views.testresults import TestMethodResultFilterSet


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
        # Future feature
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
                "defaults": {**dict(self.defaults)},
            },
            "testmethod_results": {
                "includable_fields": testmethodresult_filters["include_fields"][
                    "choices"
                ],
                "filters": testmethodresult_filters.values(),
                "defaults": {**dict(self.defaults)},
            },
        }

        return response.Response(json)

    def collect_filter_defs(self, filterSet, exclusion_names):
        json_filter_defs = {}
        defaults = dict(self.defaults)
        for name, filter in filterSet.get_filters().items():
            if name in exclusion_names:
                continue
            obj = {
                "name": name,
                "label": filter._label,
                "field_type": filter.field_class.__name__,
                "field_module": filter.field_class.__module__,
                "lookup_expr": filter.lookup_expr,
            }
            choices = filter.extra.get("choices")
            if choices:
                obj["choices"] = choices

            initial = filter.extra.get("initial")
            if initial:
                obj["initial"] = initial
            elif name in defaults:
                obj["initial"] = defaults[name]

            if "ui" in filter.extra:
                for key, value in filter.extra["ui"].items():
                    obj[key] = value

            json_filter_defs[name] = obj

        return json_filter_defs
