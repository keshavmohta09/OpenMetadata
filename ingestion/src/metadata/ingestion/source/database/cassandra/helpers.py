#  Copyright 2021 Collate
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
"""
Iceberg source helpers.
"""
from __future__ import annotations

from metadata.generated.schema.entity.data.table import Column, DataType


class CassandraColumnParser:
    """
    Responsible for containing the logic to parse a column from Cassandra to OpenMetadata
    """

    datatype_mapping = {
        "ascii": DataType.STRING,
        "bigint": DataType.BIGINT,
        "blob": DataType.BLOB,
        "boolean": DataType.BOOLEAN,
        "date": DataType.DATE,
        "decimal": DataType.DECIMAL,
        "double": DataType.DOUBLE,
        "duration": DataType.INTERVAL,
        "float": DataType.FLOAT,
        "uuid": DataType.UUID,
        "inet": DataType.INET,
        "int": DataType.INT,
        "list": DataType.ARRAY,
        "map": DataType.MAP,
        "set": DataType.SET,
        "smallint": DataType.SMALLINT,
        "text": DataType.TEXT,
        "time": DataType.TIME,
        "timestamp": DataType.TIMESTAMP,
        "timeuuid": DataType.UUID,
        "tinyint": DataType.TINYINT,
        "tuple": DataType.TUPLE,
        "varint": DataType.STRING,
        "struct": DataType.STRUCT,
    }

    @classmethod
    def parse(cls, field) -> Column:
        """
        Parses a Cassandra table column into an OpenMetadata column.
        """

        data_type = None
        array_data_type = None
        raw_data_type = ""
        for letter in field.type:
            if letter == "<":
                if not raw_data_type:
                    continue
                elif raw_data_type == "frozen":
                    raw_data_type = ""
                    continue
                else:
                    if not data_type:
                        data_type = cls.datatype_mapping.get(
                            raw_data_type.lower(), DataType.UNKNOWN
                        )
                    elif not array_data_type:
                        array_data_type = cls.datatype_mapping.get(
                            raw_data_type.lower(), DataType.UNKNOWN
                        )
                    raw_data_type = ""
                    if data_type != DataType.ARRAY:
                        break

            elif letter != ">":
                raw_data_type += letter

            elif letter == ">":
                if not array_data_type and data_type:
                    array_data_type = cls.datatype_mapping.get(
                        raw_data_type.lower(), DataType.UNKNOWN
                    )
                    break
        else:
            if not data_type:
                data_type = cls.datatype_mapping.get(
                    field.type.lower(), DataType.UNKNOWN
                )

        column_def = {
            "name": field.column_name,
            "dataTypeDisplay": str(data_type),
            "dataType": data_type,
        }
        if array_data_type:
            column_def["arrayDataType"] = array_data_type

        return Column(**column_def)