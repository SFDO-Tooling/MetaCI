"""
https://simpleisbetterthancomplex.com/snippet/2016/08/22/dealing-with-querystring-parameters.html
"""
from django import template

register = template.Library()


@register.simple_tag
def relative_url(value, field_name, urlencode=None):
    url = f"?{field_name}={value}"
    if urlencode:
        querystring = urlencode.split("&")
        filtered_querystring = [p for p in querystring if p.split("=")[0] != field_name]
        encoded_querystring = "&".join(filtered_querystring)
        url = f"{url}&{encoded_querystring}"
    return url
