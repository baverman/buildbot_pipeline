import re
import fnmatch
import operator

from .utils import ensure_list


def filter_op_and(filters):
    if len(filters) == 1:
        return filters[0]
    return lambda value: all(it(value) for it in filters)


def filter_op_or(filters):
    if len(filters) == 1:
        return filters[0]
    return lambda value: any(it(value) for it in filters)


def filter_op_not(flt):
    if not flt:
        return
    return lambda value: not flt(value)


def filter_regex(regex, getter):
    r = re.compile(regex)
    return lambda value: bool(r.match(getter(value) or ''))


def filter_fnmatch(pattern, getter):
    return lambda value: bool(fnmatch.filter(getter(value), pattern))


def make_filter(values, flt_fn, getter):
    if not values:
        return
    return filter_op_or([flt_fn(v, getter) for v in ensure_list(values)])


def make_filter_pair(desc, name, flt_fn, getter):
    return (make_filter(desc.get(name), flt_fn, getter),
            filter_op_not(make_filter(desc.get('not_' + name), flt_fn, getter)))


def make_filters(filters, is_or=False):
    if hasattr(filters, 'keys'):
        filters = [filters]

    result = []
    for desc in filters:
        result.extend(make_filter_pair(desc, 'branch', filter_regex, operator.attrgetter('branch')))
        result.extend(make_filter_pair(desc, 'comment', filter_regex, operator.attrgetter('comments')))
        result.extend(make_filter_pair(desc, 'file', filter_fnmatch, operator.attrgetter('files')))
        if 'or' in desc:
            result.append(make_filters(desc['or'], True))

    if is_or:
        return filter_op_or(list(filter(None, result)))
    else:
        return filter_op_and(list(filter(None, result)))
