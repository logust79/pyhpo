'''
The main HPO class that deals with HPOs
'''
import os
import sqlite3


class Hpo:
    def __init__(self, db):
        # conn is a sqlite connection
        assert os.path.isfile(db), 'hpo db file does not exist!'
        self.conn = sqlite3.connect(db)

    def get_ancestors(self, hpo_id, result=None):
        if result is None:
            result = []
        cursor = self.conn.cursor()

        # find record
        sql = 'SELECT * FROM hpo WHERE id = ?'
        cursor.execute(sql, (hpo_id,))
        record = dict(zip(self.table_header, cursor.fetchone()))
        if record['is_a']:
            ancestors = record['is_a'].split(';')
            result.extend(ancestors)
            for anc in ancestors:
                return self.get_ancestors(anc, result)
        else:
            return result

    @property
    def table_header(self):
        '''
        get sqlite table header
        '''
        if hasattr(self, '_table_header', None) is None:
            cursor = self.conn.cursor()
            # get header
            sql = 'PRAGMA table_info(hpo)'
            cursor.execute(sql)
            self._table_header = [i[1] for i in cursor.fetchall()]
        return self._table_header

    def get_min_graph(self, hpo_list):
        '''
        get a miniminsed graph given a hpoList. For rendering a node graph.
          e.g.
          ```
          this.getMinGraph(['HP:0007754','HP:0000505','HP:0000510'])
          ```
          returns
          [
            {
              "id": "HP:0007754", 
              "is_a": "HP:0000556"
            }, 
            {
              "id": "HP:0000556", 
              "is_a": "HP:0000478"
            }, 
            {
              "id": "HP:0000478", 
              "is_a": null
            }, 
            {
              "id": "HP:0000505", 
              "is_a": "HP:0000478"
            }, 
            {
              "id": "HP:0000510", 
              "is_a": "HP:0000556"
            }
          ]
        '''
        cursor = self.conn.cursor()

        if (len(hpo_list) == 1):
            result = [{'id': hpo_list[0], 'is_a': None}]
            sql = 'SELECT * FROM hpo WHERE id = ?'
            cursor.execute(sql, (hpo_list[0],))
            record = dict(zip(self.table_header, cursor.fetchone()))
            if record['is_a']:
                result[0]['is_a'] = record['is_a'].split(';')
                for anc in result[0]['is_a']:
                    result.append({'id': anc, 'is_a': None})
            return result

        ancestor_list = []
        for h in hpo_list:
            ancestors = self.get_ancestors(h)
            ancestor_list.append([h] + ancestors)
        ancestor_count = counter(ancestor_list)
        # sort hpo list and ancestor list so that more specific terms come first
        sorted_index = get_sorted_index(hpo_list, ancestor_count)

        result, seen = [], set()
        for hpo_index in sorted_index:
            count = ancestor_count[hpo_list[hpo_index]]
            for anc_index, ancestor in enumerate(ancestor_list[hpo_index]):
                if anc_index == 0 and not ancestor in seen:
                    result.append({'id': ancestor, 'is_a': None})
                else:
                    if ancestor_count[ancestor] > count:
                        count = ancestor_count[ancestor]
                        if result[-1]['is_a'] is None:
                            result[-1]['is_a'] = ancestor
                        if ancestor not in seen:
                            result.append({'id': ancestor, 'is_a': None})
                            seen.add(ancestor)
        return result


def counter(data):
    # given a list (of lists), return elements as key, counts as value
    result = {}

    def inner_counter(e):
        if e in result:
            result[e] += 1
        else:
            result[e] = 1

    for ele in data:
        if isinstance(ele, (list, tuple)):
            for e in ele:
                inner_counter(e)
        else:
            inner_counter(ele)
    return result


def get_sorted_index(hpos, count):
    indexed_test = [{'ind': i, 'val': e} for i, e in enumerate(hpos)]
    # sort index/value couples, based on values
    indexed_test = sorted(indexed_test, key=lambda x: count[x['val']])
    # make list keeping only indices
    return [i['ind'] for i in indexed_test]
