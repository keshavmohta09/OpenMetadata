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
Source connection handler
"""
from functools import partial
from typing import Optional

from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from cassandra.cluster import Session as CassandraSession
from pydantic import BaseModel

from metadata.generated.schema.entity.automations.workflow import (
    Workflow as AutomationWorkflow,
)
from metadata.generated.schema.entity.services.connections.database.cassandraConnection import (
    CassandraConnection,
)
from metadata.generated.schema.entity.services.connections.testConnectionResult import (
    TestConnectionResult,
)
from metadata.ingestion.connections.test_connections import test_connection_steps
from metadata.ingestion.ometa.ometa_api import OpenMetadata
from metadata.ingestion.source.database.cassandra.queries import (
    CASSANDRA_GET_KEYSPACE_TABLES,
    CASSANDRA_GET_KEYSPACES,
    CASSANDRA_GET_RELEASE_VERSION,
)
from metadata.utils.constants import THREE_MIN

# from cassandra.auth


def get_connection(connection: CassandraConnection):
    """
    Create connection
    """
    auth_provider = (
        connection.username
        and connection.password
        and PlainTextAuthProvider(
            username=connection.username, password=connection.password
        )
    )
    host, port = connection.hostPort.split(":")
    cluster = Cluster(contact_points=[host], port=port, auth_provider=auth_provider)
    session = cluster.connect()

    return session


def test_connection(
    metadata: OpenMetadata,
    session: CassandraSession,
    service_connection: CassandraConnection,
    automation_workflow: Optional[AutomationWorkflow] = None,
    timeout_seconds: Optional[int] = THREE_MIN,
) -> TestConnectionResult:
    """
    Test connection. This can be executed either as part
    of a metadata workflow or during an Automation Workflow
    """

    class SchemaHolder(BaseModel):
        database: Optional[str] = None

    holder = SchemaHolder()

    def test_get_release_version(session: CassandraConnection):
        session.execute(CASSANDRA_GET_RELEASE_VERSION)

    def test_get_databases(session: CassandraSession, holder_: SchemaHolder):
        for database in session.execute(CASSANDRA_GET_KEYSPACES):
            holder_.database = database.keyspace_name
            break

    def test_get_tables(session: CassandraSession, holder_: SchemaHolder):
        session.execute(CASSANDRA_GET_KEYSPACE_TABLES, [holder_.database])

    test_fn = {
        "CheckAccess": partial(test_get_release_version, session),
        "GetDatabases": partial(test_get_databases, session, holder),
        "GetTables": partial(test_get_tables, session, holder),
    }

    return test_connection_steps(
        metadata=metadata,
        test_fn=test_fn,
        service_type=service_connection.type.value,
        automation_workflow=automation_workflow,
        timeout_seconds=timeout_seconds,
    )