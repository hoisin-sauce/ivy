from datalib.database_types import SQLiteString

## Database Layout
[TODO Alter database to match the specified formatting]: #
# Classes
Classes correspond to at least one table within the database,
for example
```python
class A:
    field: int
```
in a file called db.py
would add to a class defined by the creation statement of
```sqlite
CREATE TABLE db_a(
    db_a_primary_key INTEGER NOT NULL PRIMARY KEY,
    field INTEGER NOT NULL
)
```
This is how tables with standard fields are resolved. Other tables may be created to resolve the fields with special fields.

# Special Fields
## Union fields
When classes contain fields that might contain values of multiple different types, this cannot be represented in a traditional table. As such we create a table structure to represent which type of value is stored for that specific instance, where one table acts as a decider for which other table holds the value for the corresponding type.

This allows for fields to be resolved without repeated queries or gathering all necessary data. However it is complicated.

This takes seemingly simple tables such as, in an example db.py
```python
class A:
    field: int | str
```
And translates to the group of tables created by
```sqlite
CREATE TABLE db_a_field_union_selector (
    id INTEGER NOT NULL PRIMARY KEY,
    union_member_number INTEGER NOT NULL
);

CREATE TABLE db_a_field_union_member_int__ (
    id INTEGER NOT NULL PRIMARY KEY,
    field INTEGER NOT NULL,
    selector INTEGER NOT NULL,
    FOREIGN KEY (selector) REFERENCES db_a_field_union_selector (id)
);

CREATE TABLE db_a_field_union_member_str__ (
    id INTEGER NOT NULL PRIMARY KEY,
    field TEXT NOT NULL,
    selector INTEGER NOT NULL,
    FOREIGN KEY (selector) REFERENCES db_a_field_union_selector (id)
);

CREATE TABLE db_a (
    id INTEGER NOT NULL PRIMARY KEY,
    field INTEGER NOT NULL,
    FOREIGN KEY (field) REFERENCES db_a_field_union_selector(id)
);
```
Querying these fields requires specifying the datatype being referenced.
## Iterable fields
## References to other Classes
When a class contains another field that is another class, instead of storing the data representing that class, the field is replaced with a reference to that class's table. If the class is not specified to be part of the database it is automatically added.

For example, take the following simple example in a Python file called db.py
```python
class A:
    field: int

class B:
    reference: A
```
In SQL, the relevant table creation command would be
```sqlite
CREATE TABLE db_A(
    id INTEGER NOT NULL PRIMARY KEY,
    field INTEGER NOT NULL
);

CREATE TABLE db_B(
    db_b_primary_id INTEGER NOT NULL PRIMARY KEY,
    reference INTEGER NOT NULL,
    FOREIGN KEY (reference) REFERENCES db_a (id)
);
```
Once the database file has been loaded, the fields can be used to make queries like so
```python
from datalib.database_manager import DatabaseManager
from datalib.database_types import SQLiteString
from typing import Generator

class B:
    ...

# Setup database manager
...
dbi: DatabaseManager[SQLiteString, dict]

data: Generator[B] = dbi.select(B).where(B["A"]["field"] == 1).get_values()
```

Where the objects returned in data match the output from the query
```sqlite
SELECT
    *
FROM
    db_B
INNER JOIN db_A
ON db_A.id = db_B.reference
WHERE
    db_A.field = 1
```
## Enum Fields