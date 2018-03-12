#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Copyright (c) 2002-2018 "Neo Technology,"
# Network Engine for Objects in Lund AB [http://neotechnology.com]
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


from datetime import date, datetime, time
from unittest import SkipTest

from pytz import FixedOffset, timezone, utc

from neo4j.v1.types.graph import Node, Relationship, Path
from neo4j.v1.types.spatial import CartesianPoint, CartesianPoint3D, WGS84Point, WGS84Point3D
from neo4j.v1.types.temporal import duration

from test.integration.tools import DirectIntegrationTestCase


def run_and_rollback(tx, statement, **parameters):
    result = tx.run(statement, **parameters)
    value = result.single().value()
    tx.success = False
    return value


class CoreTypeOutputTestCase(DirectIntegrationTestCase):

    def test_null(self):
        with self.driver.session() as session:
            result = session.run("RETURN null")
            self.assertIs(result.single().value(), None)

    def test_boolean(self):
        with self.driver.session() as session:
            result = session.run("RETURN true")
            self.assertIs(result.single().value(), True)

    def test_integer(self):
        with self.driver.session() as session:
            result = session.run("RETURN 123456789")
            self.assertEqual(result.single().value(), 123456789)

    def test_float(self):
        with self.driver.session() as session:
            result = session.run("RETURN 3.1415926")
            self.assertEqual(result.single().value(), 3.1415926)

    def test_string(self):
        with self.driver.session() as session:
            result = session.run("RETURN 'hello, world'")
            self.assertEqual(result.single().value(), "hello, world")

    def test_bytes(self):
        with self.driver.session() as session:
            data = bytearray([0x00, 0x33, 0x66, 0x99, 0xCC, 0xFF])
            value = session.write_transaction(run_and_rollback, "CREATE (a {x:$x}) RETURN a.x", x=data)
            self.assertEqual(value, data)

    def test_list(self):
        with self.driver.session() as session:
            result = session.run("RETURN ['one', 'two', 'three']")
            self.assertEqual(result.single().value(), ["one", "two", "three"])

    def test_map(self):
        with self.driver.session() as session:
            result = session.run("RETURN {one: 'eins', two: 'zwei', three: 'drei'}")
            self.assertEqual(result.single().value(), {"one": "eins", "two": "zwei", "three": "drei"})


class GraphTypeOutputTestCase(DirectIntegrationTestCase):

    def test_node(self):
        with self.driver.session() as session:
            a = session.write_transaction(run_and_rollback, "CREATE (a:Person {name:'Alice'}) RETURN a")
            self.assertIsInstance(a, Node)
            self.assertEqual(a.labels, {"Person"})
            self.assertEqual(a.properties, {"name": "Alice"})

    def test_relationship(self):
        with self.driver.session() as session:
            a, b, r = session.write_transaction(
                run_and_rollback, "CREATE (a)-[r:KNOWS {since:1999}]->(b) RETURN [a, b, r]")
            self.assertIsInstance(r, Relationship)
            self.assertEqual(r.type, "KNOWS")
            self.assertEqual(r.properties, {"since": 1999})
            self.assertEqual(r.start, a.id)
            self.assertEqual(r.end, b.id)

    def test_path(self):
        with self.driver.session() as session:
            a, b, c, ab, bc, p = session.write_transaction(
                run_and_rollback, "CREATE p=(a)-[ab:X]->(b)-[bc:X]->(c) RETURN [a, b, c, ab, bc, p]")
            self.assertIsInstance(p, Path)
            self.assertEqual(len(p), 2)
            self.assertEqual(p.nodes, (a, b, c))
            self.assertEqual(p.relationships, (ab, bc))
            self.assertEqual(p.start, a)
            self.assertEqual(p.end, c)


class SpatialTypeOutputTestCase(DirectIntegrationTestCase):

    def test_cartesian_point(self):
        if not self.at_least_protocol_version(2):
            raise SkipTest("Point type requires Bolt protocol v2 or above")
        with self.driver.session() as session:
            result = session.run("RETURN point({x:3, y:4})")
            value = result.single().value()
            self.assertIsInstance(value, CartesianPoint)
            self.assertEqual(value.x, 3.0)
            self.assertEqual(value.y, 4.0)

    def test_cartesian_3d_point(self):
        if not self.at_least_protocol_version(2):
            raise SkipTest("Point type requires Bolt protocol v2 or above")
        with self.driver.session() as session:
            result = session.run("RETURN point({x:3, y:4, z:5})")
            value = result.single().value()
            self.assertIsInstance(value, CartesianPoint3D)
            self.assertEqual(value.x, 3.0)
            self.assertEqual(value.y, 4.0)
            self.assertEqual(value.z, 5.0)

    def test_wgs84_point(self):
        if not self.at_least_protocol_version(2):
            raise SkipTest("Point type requires Bolt protocol v2 or above")
        with self.driver.session() as session:
            result = session.run("RETURN point({latitude:3, longitude:4})")
            value = result.single().value()
            self.assertIsInstance(value, WGS84Point)
            self.assertEqual(value.latitude, 3.0)
            self.assertEqual(value.longitude, 4.0)

    def test_wgs84_3d_point(self):
        if not self.at_least_protocol_version(2):
            raise SkipTest("Point type requires Bolt protocol v2 or above")
        with self.driver.session() as session:
            result = session.run("RETURN point({latitude:3, longitude:4, height:5})")
            value = result.single().value()
            self.assertIsInstance(value, WGS84Point3D)
            self.assertEqual(value.latitude, 3.0)
            self.assertEqual(value.longitude, 4.0)
            self.assertEqual(value.height, 5.0)


class TemporalTypeOutputTestCase(DirectIntegrationTestCase):

    def test_date(self):
        if not self.at_least_protocol_version(2):
            raise SkipTest("Date type requires Bolt protocol v2 or above")
        with self.driver.session() as session:
            result = session.run("RETURN date('1976-06-13')")
            value = result.single().value()
            self.assertIsInstance(value, date)
            self.assertEqual(value, date(1976, 6, 13))

    def test_whole_second_time(self):
        if not self.at_least_protocol_version(2):
            raise SkipTest("Time type requires Bolt protocol v2 or above")
        with self.driver.session() as session:
            result = session.run("RETURN time('12:34:56')")
            value = result.single().value()
            self.assertIsInstance(value, time)
            self.assertEqual(value, time(12, 34, 56, tzinfo=FixedOffset(0)))

    def test_microsecond_resolution_time(self):
        if not self.at_least_protocol_version(2):
            raise SkipTest("Time type requires Bolt protocol v2 or above")
        with self.driver.session() as session:
            result = session.run("RETURN time('12:34:56.789012')")
            value = result.single().value()
            self.assertIsInstance(value, time)
            self.assertEqual(value, time(12, 34, 56, 789012, tzinfo=FixedOffset(0)))

    def test_nanosecond_resolution_time(self):
        if not self.at_least_protocol_version(2):
            raise SkipTest("Time type requires Bolt protocol v2 or above")
        with self.driver.session() as session:
            result = session.run("RETURN time('12:34:56.789012345')")
            value = result.single().value()
            self.assertIsInstance(value, time)
            self.assertEqual(value, time(12, 34, 56, 789012, tzinfo=FixedOffset(0)))

    def test_time_with_numeric_time_zone(self):
        if not self.at_least_protocol_version(2):
            raise SkipTest("Time type requires Bolt protocol v2 or above")
        with self.driver.session() as session:
            result = session.run("RETURN time('12:34:56.789012+0130')")
            value = result.single().value()
            self.assertIsInstance(value, time)
            self.assertEqual(value, time(12, 34, 56, 789012, tzinfo=FixedOffset(90)))

    def test_whole_second_localtime(self):
        if not self.at_least_protocol_version(2):
            raise SkipTest("LocalTime type requires Bolt protocol v2 or above")
        with self.driver.session() as session:
            result = session.run("RETURN localtime('12:34:56')")
            value = result.single().value()
            self.assertIsInstance(value, time)
            self.assertEqual(value, time(12, 34, 56))

    def test_microsecond_resolution_localtime(self):
        if not self.at_least_protocol_version(2):
            raise SkipTest("LocalTime type requires Bolt protocol v2 or above")
        with self.driver.session() as session:
            result = session.run("RETURN localtime('12:34:56.789012')")
            value = result.single().value()
            self.assertIsInstance(value, time)
            self.assertEqual(value, time(12, 34, 56, 789012))

    def test_nanosecond_resolution_localtime(self):
        if not self.at_least_protocol_version(2):
            raise SkipTest("LocalTime type requires Bolt protocol v2 or above")
        with self.driver.session() as session:
            result = session.run("RETURN localtime('12:34:56.789012345')")
            value = result.single().value()
            self.assertIsInstance(value, time)
            self.assertEqual(value, time(12, 34, 56, 789012))

    def test_whole_second_datetime(self):
        if not self.at_least_protocol_version(2):
            raise SkipTest("DateTime type requires Bolt protocol v2 or above")
        with self.driver.session() as session:
            result = session.run("RETURN datetime('1976-06-13T12:34:56')")
            value = result.single().value()
            self.assertIsInstance(value, datetime)
            self.assertEqual(value, datetime(1976, 6, 13, 12, 34, 56, tzinfo=utc))

    def test_microsecond_resolution_datetime(self):
        if not self.at_least_protocol_version(2):
            raise SkipTest("DateTime type requires Bolt protocol v2 or above")
        with self.driver.session() as session:
            result = session.run("RETURN datetime('1976-06-13T12:34:56.789012')")
            value = result.single().value()
            self.assertIsInstance(value, datetime)
            self.assertEqual(value, datetime(1976, 6, 13, 12, 34, 56, 789012, tzinfo=utc))

    def test_nanosecond_resolution_datetime(self):
        if not self.at_least_protocol_version(2):
            raise SkipTest("DateTime type requires Bolt protocol v2 or above")
        with self.driver.session() as session:
            result = session.run("RETURN datetime('1976-06-13T12:34:56.789012345')")
            value = result.single().value()
            self.assertIsInstance(value, datetime)
            self.assertEqual(value, datetime(1976, 6, 13, 12, 34, 56, 789012, tzinfo=utc))

    def test_datetime_with_numeric_time_zone(self):
        if not self.at_least_protocol_version(2):
            raise SkipTest("DateTime type requires Bolt protocol v2 or above")
        with self.driver.session() as session:
            result = session.run("RETURN datetime('1976-06-13T12:34:56.789012+01:30')")
            value = result.single().value()
            self.assertIsInstance(value, datetime)
            self.assertEqual(value, datetime(1976, 6, 13, 12, 34, 56, 789012, tzinfo=FixedOffset(90)))

    def test_datetime_with_textual_time_zone(self):
        if not self.at_least_protocol_version(2):
            raise SkipTest("DateTime type requires Bolt protocol v2 or above")
        with self.driver.session() as session:
            result = session.run("RETURN datetime('1976-06-13T12:34:56.789012[Europe/London]')")
            value = result.single().value()
            self.assertIsInstance(value, datetime)
            self.assertEqual(value, timezone("Europe/London").localize(datetime(1976, 6, 13, 12, 34, 56, 789012)))

    def test_whole_second_localdatetime(self):
        if not self.at_least_protocol_version(2):
            raise SkipTest("LocalDateTime type requires Bolt protocol v2 or above")
        with self.driver.session() as session:
            result = session.run("RETURN localdatetime('1976-06-13T12:34:56')")
            value = result.single().value()
            self.assertIsInstance(value, datetime)
            self.assertEqual(value, datetime(1976, 6, 13, 12, 34, 56))

    def test_microsecond_resolution_localdatetime(self):
        if not self.at_least_protocol_version(2):
            raise SkipTest("LocalDateTime type requires Bolt protocol v2 or above")
        with self.driver.session() as session:
            result = session.run("RETURN localdatetime('1976-06-13T12:34:56.789012')")
            value = result.single().value()
            self.assertIsInstance(value, datetime)
            self.assertEqual(value, datetime(1976, 6, 13, 12, 34, 56, 789012))

    def test_nanosecond_resolution_localdatetime(self):
        if not self.at_least_protocol_version(2):
            raise SkipTest("LocalDateTime type requires Bolt protocol v2 or above")
        with self.driver.session() as session:
            result = session.run("RETURN localdatetime('1976-06-13T12:34:56.789012345')")
            value = result.single().value()
            self.assertIsInstance(value, datetime)
            self.assertEqual(value, datetime(1976, 6, 13, 12, 34, 56, 789012))

    def test_duration(self):
        if not self.at_least_protocol_version(2):
            raise SkipTest("Duration type requires Bolt protocol v2 or above")
        with self.driver.session() as session:
            result = session.run("RETURN duration('P1Y2M3DT4H5M6.789S')")
            value = result.single().value()
            self.assertIsInstance(value, duration)
            self.assertEqual(value, duration(1, 2, 3, 4, 5, 6.789))
