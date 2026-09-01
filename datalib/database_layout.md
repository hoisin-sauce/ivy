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
Querying this requires one of the following syntaxes,

```python
from datalib.database_manager import DatabaseManager
from datalib.database_types import SQLiteString
from typing import Generator

class A:
    field: int | str

# Setup database
...

dbi: DatabaseManager[SQLiteString, dict]

data = dbi.select(A["field"] == 1).get_values() # Implicit typing
# OR
data = dbi.select(A["field", int] == 1).get_values() # Specifying field typing
# OR
data = dbi.select(A["field"][int] == 1).get_values() # Specifying the type as an attribute
```

## Iterable fields
Classes may contain fields that refer to a collection of other values,
e.g. a list of values of another type or a mapping between two other types.
These are fundamentally roughly the same type in a database.

A basic example of these classes might look like
```python
class ListContainer:
    field: list[int]

class MappingContainer:
    field: dict[int, str]
```
These are fundamentally abstracted by the same mechanism, by treating a mapping as
a list of pairs which it is equivalent to. The data about a member of the collection -
be it the individual item or pair is stored in one table, the surrounding class in
another and the connection between them is stored as a separate class.

```sqlite
-- The list container

CREATE TABLE ListContainer__field__iter_inner__ (
	id INTEGER NOT NULL PRIMARY KEY,
	option_0 INTEGER NOT NULL
);
CREATE TABLE ListContainer (
	id INTEGER NOT NULL PRIMARY KEY
);
CREATE TABLE ListContainer_field__iter_link__builtins_list (
	parent_field INTEGER NOT NULL,
	field_to_data INTEGER NOT NULL,
	FOREIGN KEY (parent_field) REFERENCES test_datalib_test_iter_from_markdown__ListContainer(id),
	FOREIGN KEY (field_to_data) REFERENCES test_datalib_test_iter_from_markdown__ListContainer__field__iter_inner__(id)
);

-- The mapping container
CREATE TABLE MappingContainer__field__iter_inner__ (
	id INTEGER NOT NULL PRIMARY KEY,
	option_0 INTEGER NOT NULL,
	option_1 STRING NOT NULL
);
CREATE TABLE MappingContainer (
	id INTEGER NOT NULL PRIMARY KEY
);
CREATE TABLE MappingContainer_field__iter_link__builtins_dict (
	parent_field INTEGER NOT NULL,
	field_to_data INTEGER NOT NULL,
	FOREIGN KEY (parent_field) REFERENCES test_datalib_test_iter_from_markdown__MappingContainer(id),
	FOREIGN KEY (field_to_data) REFERENCES test_datalib_test_iter_from_markdown__MappingContainer__field__iter_inner__(id)
);
```
In the above output schema we can see that the two datatypes are nearly identically
represented, differing by only the number of fields. This process should automatically
extend itself to objects which require a collection of sequences of arbitrary length
to be properly represented.

Data stored in these fields can be accessed by constructing a query such as
```python
from datalib.database_manager import DatabaseManager
from datalib.database_types import SQLiteString
from typing import Generator

# Same classes as earlier

class Dummy:
    field: int
    
class DummyToo:
    field: str

# Setup database manager
...

dbi: DatabaseManager[SQLiteString, dict]

# Lists and other basic iterables
data = dbi.select(ListContainer).where(1 in ListContainer["field"]).get_values()

# Or when constructing a query for another field
data = dbi.select(Dummy).where(Dummy["field"] in ListContainer["field"] &
                                            1 in ListContainer["field"]
).get_values()
```

For mappings such as dictionaries
in behaves as it does with a standard python mapping and refers to the key field
```python
data = dbi.select(MappingContainer).where(1 in MappingContainer["field"]).get_values()
```
we use `.value` to refer to the value that is mapped to, e.g.
```python
data = dbi.select(
    MappingContainer
).where(
    "foo" in MappingContainer["field"].value
).get_values()
```
We can build up queries using `.maps` with mappings like this
```python
data = dbi.select(DummyToo).where(
    MappingContainer["field"].maps(Dummy["field"], DummyToo["field"])
)
```
The same syntax can be used for ordered datatypes (in progress)
```python
data = dbi.select(Dummy).where(ListContainer.maps(0, Dummy["field"]))
```
which would return all the Dummy objects where their value is the first
value in a list



When an iterable has multiple different types, or holds values at different points
we can use `.option` to switch between the possible options e.g.
```python
data = dbi.select(MappingContainer).where(MappingContainer["field"].option(0) == 1)
```
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

data: Generator[B, None, None] = dbi.select(B).where(B["A"]["field"] == 1).get_values()
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