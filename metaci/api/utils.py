import re
from rest_framework.generics import get_object_or_404


class PkOrSlugMixin(object):
    """
    ViewSet Mixin that supports looking up an object by primary key
    or slug field in the same url scheme/default router. if the kwarg
    matches lookup_pk_regexp (defaults to \d+), search by lookup_field,
    otherwise, search by lookup_slug_field.
    """

    # Override lookup_slug_field with the name of your string/uri slug field
    lookup_slug_field = "slug"
    # default assumes django orm convention of pk.
    lookup_field = "pk"
    # default assumes integer PKs
    lookup_pk_regexp = r"^\d+$"
    # default from the router made explicit
    lookup_value_regexp = r"[^/.]+"

    def get_object(self):
        """return the object based on pk or slug"""
        queryset = self.filter_queryset(self.get_queryset())

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]

        filter_kwargs = {}
        if re.match(self.lookup_pk_regexp, lookup_value):
            filter_kwargs[self.lookup_field] = lookup_value
        else:
            filter_kwargs[self.lookup_slug_field] = lookup_value

        # May raise a permission denied
        obj = get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)

        return obj
