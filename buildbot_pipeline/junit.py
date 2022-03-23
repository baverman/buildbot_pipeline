import functools
from xml.etree import ElementTree as ET

from covador import make_schema, item, opt
from jinja2 import Template


class XmlGetter:
    def __init__(self, ns=None):
        self.ns = ns

    def get(self, elem, item):
        if item.multi:
            return elem.findall(item.src, self.ns)
        else:
            return elem.find(item.src, self.ns)


def xml_text(elem):
    return elem.text


def xml_attr(name):
    def get_attr(elem):
        return elem.attrib.get(name)
    return get_attr


xml_schema = make_schema(XmlGetter())

property_t = xml_schema(
    name=item(xml_attr('name'), src='.'),
    value=item(xml_attr('value'), src='.'),
)

error_t = xml_schema(
    message=item(xml_attr('message'), src='.'),
    type=opt(xml_attr('type'), src='.'),
    content=item(xml_text, src='.'),
)

test_t = xml_schema(
    error=opt(error_t, src='error'),
    failure=opt(error_t, src='failure'),
    name=item(xml_attr('name'), src='.'),
    classname=item(xml_attr('classname'), src='.'),
    time=item(xml_attr('time'), src='.') | float,
    stdout=opt(xml_text, src='system-out'),
    stderr=opt(xml_text, src='system-err'),
    properties=item(property_t, src='properties/property', multi=True),
)

testsuite_t = xml_schema(
    name=item(xml_attr('name'), src='.'),
    package=item(xml_attr('package'), src='.'),
    testcases=item(test_t, src=('testcase'), multi=True),
    tests=item(xml_attr('tests'), src='.') | int,
    errors=item(xml_attr('errors'), src='.') | int,
    failures=item(xml_attr('failures'), src='.') | int,
    skipped=opt(xml_attr('skipped'), src='.', default=0) | int,
    time=item(xml_attr('time'), src='.') | float,
)


junit_single_t = xml_schema(suites=item(testsuite_t, multi=True, src='.'))
junit_many_t = xml_schema(suites=item(testsuite_t, multi=True, src='testsuite'))


def parse(fname):
    root = ET.parse(fname)
    root_tag = root.getroot().tag
    if root_tag == 'testsuite':
        s = junit_single_t
    elif root_tag == 'testsuites':
        s = junit_many_t
    else:
        return []
    return s(root)['suites']


EMBED_TEMPLATE = '''\
<div class="bb-pipe-junit-report">
  <style>
    .bb-pipe-junit-case span.status.ok {
        color: #00b255;
    }
    .bb-pipe-junit-case span.status.error {
        color: #cc008e;
    }
    .bb-pipe-junit-case span.status.fail {
        color: #ff2920;
    }
    .bb-pipe-junit-case summary {
        font-weight: bold;
    }
  </style>
  {% for suite in suites %}
  <div class="bb-pipe-junit-suite">
    <h2>{{ suite.name }}</h2>
    <p>Total: {{ suite.tests }}, errors: {{ suite.errors }}, failures: {{ suite.failures }}, skipped: {{ suite.skipped }}. Time: {{ suite.time }}</p>
    {% for case in suite.testcases %}
    <div class="bb-pipe-junit-case" style="margin-bottom: 0.5em;">
      <details {%if case.fail %}open{% endif %}>
        <summary>
          <span class="status {{ case.status }}">{{ case.status.upper() }}</span>
          {{ case.classname }}.{{ case.name }} ({{ case.time }})
        </summary>
        <p>{{ case.fail.message }}</p>
        <pre>{{ case.fail.content }}</pre>
        {% if case.stderr %}
        <pre>{{ case.stderr }}</pre>
        {% endif %}
        {% if case.stdout %}
        <pre>{{ case.stdout }}</pre>
        {% endif %}
      </details>
    </div>
    {% endfor %}
  </div>
  {% endfor %}
</div>
'''


HTML_TEMPLATE = f'''\
<!doctype html>
<html class="no-js" lang="">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
{EMBED_TEMPLATE}
</body>
'''


@functools.lru_cache(None)
def get_template(embed):
    if embed:
        return Template(EMBED_TEMPLATE)
    return Template(HTML_TEMPLATE)


def gen_html(suites, embed=False):
    for s in suites:
        for c in s['testcases']:
            c['fail'] = c['error'] or c['failure']

            if c['error']:
                c['status'] = 'error'
            elif c['failure']:
                c['status'] = 'fail'
            else:
                c['status'] = 'ok'

            if c['stderr'] and not c['stderr'].strip():
                c['stderr'] = None
            if c['stdout'] and not c['stdout'].strip():
                c['stdout'] = None

        s['testcases'].sort(key=lambda it: not it['fail'])

    return get_template(embed).render(suites=suites)


def main():
    import sys
    suites = parse(sys.argv[1])
    print(gen_html(suites))


if __name__ == '__main__':
    main()
