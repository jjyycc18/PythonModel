def fetch_data_all(cursor) :
    result = []
    if cursor.description:
        column_names = list(map(lambda x: x.upper(), [
            d[0] for d in cursor.description]))
        rows = list(cursor.fetchall())
        if rows and len(rows) > 0 :
            result = [FetchData(column_names, row) for row in rows]
    return result
def fetch_data_one(cursor) :
    result = None
    if cursor.description :
        column_names = list(map(lambda x: x.upper(), [
            d[0] for d in cursor.description]))
        row = cursor.fetchone()
        if row is None :
            result = FetchData(column_names, [None] * len(column_names))
        else :
            result = FetchData(column_names, row)
    return result
class FetchData(object):
    def __init__(self, columns, values):
        for column, value in zip(columns, values):
            if "<class 'decimal.Decimal'>" == str(type(value)) :
                value = float(str(value))
            setattr(self, column, value)
    def __eq__(self, other):
        if not isinstance(other, FetchData):
            return NotImplemented
        return self.__dict__ == other.__dict__
    def __repr__(self):
        return str(self.__dict__)
    def __hash__(self):
        return hash(repr(self))