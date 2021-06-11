#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Copyright (c) 2002-2020 "Neo4j,"
# Neo4j Sweden AB [http://neo4j.com]
#
# This file is part of Neo4j.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# tag::transaction-function-import[]
from neo4j import unit_of_work
# end::transaction-function-import[]


# python -m pytest tests/integration/examples/test_session_configuration_with_database.py -s -v


@unit_of_work(timeout=5)
def create_person(tx, name):
    return tx.run("CREATE (a:Person {name: $name}) RETURN id(a)", name=name).single().value()


def add_person(driver, name):
    # tag::session-config-database[]
    session = driver.session(database="foo")
    # end::session-config-database[]
    with session:
        return session.write_transaction(create_person, name)


class SessionConfigurationExample:

    def __init__(self, driver):
        self.driver = driver

    def add_person(self, name):
        return add_person(self.driver, name)


def test_example(bolt_driver):
    eg = SessionConfigurationExample(bolt_driver)
    with eg.driver.session() as session:
        session.run("MATCH (_) DETACH DELETE _")
        eg.add_person("Alice")
        n = session.run("MATCH (a:Person) RETURN count(a)").single().value()
        assert n == 1
