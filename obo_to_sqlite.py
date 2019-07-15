# A script to convert obo to python
import sqlite3
import argparse


def main(args):
    # create database
    conn = sqlite3.connect(args.db)
    cursor = conn.cursor()
    columns = [
        {'name': 'id', 'index': True},
        {'name': 'name', 'index': True},
        {'name': 'def', 'index': False},
        {'name': 'alt_id', 'index': False},
        {'name': 'is_a', 'index': False},
    ]
    cursor.execute('DROP TABLE IF EXISTS hpo')
    cursor.execute(f'''CREATE TABLE hpo({','.join([i['name'] + ' text' for i in columns])},
    PRIMARY KEY({','.join([i['name'] for i in columns if i['index']])}))''')

    # read obo
    this_term = {}
    with open(args.obo, 'rt') as inf:
        for line in inf:
            line = line.rstrip()
            if not line:
                continue
            if line == '[Term]':
                if this_term:
                    # write to database
                    write_to_db(this_term, columns, cursor)
                    this_term = {}
                continue
            key, value = line.split(': ', 1)
            if key in ('id', 'name'):
                this_term[key] = value
            elif key == 'def':
                value = value.split('"')[1]
                this_term[key] = value
            elif key == 'alt_id':
                if key in this_term:
                    this_term[key].append(value)
                else:
                    this_term[key] = [value]
            elif key == 'is_a':
                value = value.split('!')[0].strip()
                if key in this_term:
                    this_term[key].append(value)
                else:
                    this_term[key] = [value]

        write_to_db(this_term, columns, cursor)
        conn.commit()
        conn.close()


def write_to_db(rec, columns, c):
    # join is_a and alt_id as strings
    for key in ('is_a', 'alt_id'):
        if key in rec:
            rec[key] = ';'.join(rec[key])
        else:
            rec[key] = None
    # insert sql
    sql = f"INSERT INTO hpo VALUES ({','.join(['?']*len(columns))})"
    c.execute(sql, [rec.get(i['name'], None) for i in columns])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--obo", help="the obo file to be converted", default="data/hp.obo")
    parser.add_argument("--db", help="sqlite database name",
                        default="data/hpo.db")
    args = parser.parse_args()
    main(args)
    print('===done===')
