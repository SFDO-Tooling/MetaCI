# I started here: https://www.django-rest-framework.org/api-guide/renderers/#example

import csv
import io
import logging

from rest_framework import renderers

logger = logging.getLogger(__name__)


class SimpleCSVRenderer(renderers.BaseRenderer):
    """Renders simple 1-level-deep data as csv"""

    # Setting media_type to text/csv results in the file being
    # downloaded rather than being displayed in the browser.
    # I _think_ that's what I want, but is there a smarter
    # way to do this (eg: by passing in an accept header)?
    media_type = "text/csv"
    format = "csv"

    def render(self, data, media_type=None, renderer_context={}):

        if "results" not in data:
            logger.warning(f"no results in data: {str(data)}")
            # Is this the right thing to do?
            detail = data.get("detail", "unexpected error")
            return detail

        table_data = self.to_table(data["results"])
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        for row in table_data:
            writer.writerow(row)

        return csv_buffer.getvalue().encode("utf-8")

    def to_table(self, data, fields=None):
        """Generator to stream the data as a series of rows"""
        if data:
            if fields is None:
                fields = data[0].keys()
            yield fields

            for item in data:
                row = [item.get(key, None) for key in fields]
                yield row
