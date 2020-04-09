# -*- coding: utf-8 -*-
"""
integration tests for nilirt_ip
"""

from __future__ import absolute_import, print_function, unicode_literals

import shutil
import time

import pytest
from tests.support.case import ModuleCase


@pytest.mark.destructive_test
@pytest.mark.skip_if_not_root
@pytest.mark.skipif(
    'grains["os_family"] == "NILinuxRT"', reason="Tests applicable only to NILinuxRT"
)
class Nilrt_ipModuleTest(ModuleCase):
    """
    Validate the nilrt_ip module
    """

    @classmethod
    def setUpClass(cls):
        cls.initialState = {}

    @classmethod
    def tearDownClass(cls):
        cls.initialState = None

    def setUp(self):
        """
        Get current settings
        """
        # save files from var/lib/connman*
        super(Nilrt_ipModuleTest, self).setUp()
        shutil.move("/var/lib/connman", "/tmp/connman")

    def tearDown(self):
        """
        Reset to original settings
        """
        # restore files
        shutil.move("/tmp/connman", "/var/lib/connman")
        self.run_function("service.restart", ["connman"])
        time.sleep(10)  # wait 10 seconds for connman to be fully loaded
        interfaces = self.__interfaces()
        for interface in interfaces:
            self.run_function("ip.up", [interface])

    def __connected(self, interface):
        return interface["up"]

    def __interfaces(self):
        interfaceList = []
        for iface in self.run_function("ip.get_interfaces_details")["interfaces"]:
            interfaceList.append(iface["connectionid"])
        return interfaceList

    def test_down(self):
        interfaces = self.__interfaces()
        for interface in interfaces:
            result = self.run_function("ip.down", [interface])
            self.assertTrue(result)
        info = self.run_function("ip.get_interfaces_details")
        for interface in info["interfaces"]:
            self.assertFalse(self.__connected(interface))

    def test_up(self):
        interfaces = self.__interfaces()
        # first down all interfaces
        for interface in interfaces:
            self.run_function("ip.down", [interface])
        # up interfaces
        for interface in interfaces:
            result = self.run_function("ip.up", [interface])
            self.assertTrue(result)
        info = self.run_function("ip.get_interfaces_details")
        for interface in info["interfaces"]:
            self.assertTrue(self.__connected(interface))

    def test_set_dhcp_linklocal_all(self):
        interfaces = self.__interfaces()
        for interface in interfaces:
            result = self.run_function("ip.set_dhcp_linklocal_all", [interface])
            self.assertTrue(result)
        info = self.run_function("ip.get_interfaces_details")
        for interface in info["interfaces"]:
            self.assertEqual(interface["ipv4"]["requestmode"], "dhcp_linklocal")

    def test_static_all(self):
        interfaces = self.__interfaces()
        for interface in interfaces:
            result = self.run_function(
                "ip.set_static_all",
                [
                    interface,
                    "192.168.10.4",
                    "255.255.255.0",
                    "192.168.10.1",
                    "8.8.4.4 8.8.8.8",
                ],
            )
            self.assertTrue(result)

        info = self.run_function("ip.get_interfaces_details")
        for interface in info["interfaces"]:
            self.assertIn("8.8.4.4", interface["ipv4"]["dns"])
            self.assertIn("8.8.8.8", interface["ipv4"]["dns"])
            self.assertEqual(interface["ipv4"]["requestmode"], "static")
            self.assertEqual(interface["ipv4"]["address"], "192.168.10.4")
            self.assertEqual(interface["ipv4"]["netmask"], "255.255.255.0")
            self.assertEqual(interface["ipv4"]["gateway"], "192.168.10.1")
