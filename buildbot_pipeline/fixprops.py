import sys
import sqlite3
import itertools
import operator
import json

PROP_ALL_NAME = '__bbp_props__'
FILE_ALL_NAME = '__bbp_files__'


def get_props(conn, table, id):
    is_source = table == 'build_properties'
    if is_source:
        q = f'select {id}, name, value, source from {table} order by {id}'
    else:
        q = f'select {id}, property_name, property_value from {table} order by {id}'

    data = conn.execute(q)
    result = {}
    for k, g in itertools.groupby(data, operator.itemgetter(0)):
        props = {}
        if is_source:
            for _, name, value, source in g:
                props[name] = json.loads(value), source
        else:
            for _, name, value in g:
                props[name] = json.loads(value)

        if PROP_ALL_NAME in props:
            p = props.pop(PROP_ALL_NAME)[0]
            if not props:
                continue
            p.update(props)
            props = p

        result[k] = props

    return result


def update_props(conn, table, id, data, source):
    print('UPDATING', table, len(data))
    for k, v in data.items():
        with conn:
            conn.execute(f'DELETE FROM {table} WHERE {id}=?', (k,))
            if table == 'build_properties':
                row = (k, PROP_ALL_NAME, json.dumps(v), source)
                conn.execute(f'INSERT INTO {table} ({id}, name, value, source) VALUES (?, ?, ?, ?)', row)
            else:
                row = (k, PROP_ALL_NAME, json.dumps([v, source]))
                conn.execute(f'INSERT INTO {table} ({id}, property_name, property_value) VALUES (?, ?, ?)', row)


def process_properties(conn, table, id, source='buildbot_pipeline'):
    data = get_props(conn, table, id)
    update_props(conn, table, id, data, source)


def process_change_files(conn):
    q = 'SELECT changeid, filename FROM change_files ORDER by changeid'
    data = {}
    for k, g in itertools.groupby(conn.execute(q), operator.itemgetter(0)):
        files = [it[1] for it in g]
        if files and files[0].startswith(FILE_ALL_NAME):
            continue
        data[k] = files

    print('UPDATING', 'change_files', len(data))
    for k, v in data.items():
        with conn:
            conn.execute('DELETE FROM change_files WHERE changeid=?', (k,))
            row = (k, FILE_ALL_NAME + json.dumps(v))
            conn.execute(f'INSERT INTO change_files (changeid, filename) VALUES (?, ?)', row)


def main():
    conn = sqlite3.connect(sys.argv[1])
    process_properties(conn, 'change_properties', 'changeid', 'Change')
    process_properties(conn, 'buildset_properties', 'buildsetid')
    process_properties(conn, 'build_properties', 'buildid')
    process_change_files(conn)
    conn.execute('VACUUM')


if __name__ == '__main__':
    main()
