'''
Created on Sep 16, 2015

@author: mcasadevall
'''

import unittest
from socket import AF_INET, AF_INET6
from pyroute2.iproute import IPRoute

from mcdynipd.interface import NetworkInterfaceConfig, DuplicateIPError,\
    InvalidNetworkDevice, IPNotFound

class InterfaceConfigTest(unittest.TestCase):
    '''Tests all aspects of the NetworkInterfaceConfig API

    A dummy interface (dummy0) is used to test APIs and read back configuration. Testing
    may report a false positive if this interface exists for whatever reason.'''
    def __init__(self, *args, **kwargs):
        super(InterfaceConfigTest, self).__init__(*args, **kwargs)
        self.iproute_api = IPRoute()

    def setUp(self):
        self.iproute_api.link_create(name='dummy0', kind='dummy')


    def tearDown(self):
        idx = self.iproute_api.link_lookup(ifname='dummy0')[0]
        self.iproute_api.link_remove(idx)
        self.iproute_api.close()

    def test_nonexistent_interface(self):
        '''Tests that InvalidNetworkDevice is raised if an interface is non-existent'''
        with self.assertRaises(InvalidNetworkDevice):
            NetworkInterfaceConfig('nonexistent0')

    def test_empty_configuration(self):
        '''Confirms that we properly handle no configuration data on an interface'''
        # The interface has just been created as part of setup, there shouldn't be any IPs
        interface_cfg = NetworkInterfaceConfig('dummy0')

        if interface_cfg.get_ips():
            self.fail("dummy configuration returned an IP!")

    def test_add_ipv4(self):
        '''Adds an IPv4 address, and then confirms it via get_ips()'''
        interface_cfg = NetworkInterfaceConfig('dummy0')

        interface_cfg.add_v4_ip(ip_addr='10.0.241.123',
                                broadcast='10.0.241.255',
                                prefixlen=24)

        # Retrieve the IPs on the interface and make sure its the only one
        # plus that it is the correct IP
        ips = interface_cfg.get_ips()
        self.assertEqual(len(ips), 1, "dummy interface either didn't get the IP or has multiple!")
        self.assertEqual(ips[0]['ip_address'], '10.0.241.123', "IP assignment failure!")
        self.assertEqual(ips[0]['family'], AF_INET)
        self.assertEqual(ips[0]['broadcast'], '10.0.241.255', "IP assignment failure!")
        self.assertEqual(ips[0]['prefix_length'], 24, "IP assignment failure!")

    def test_add_ipv6(self):
        '''Adds an IPv6 address and then confirms it'''
        interface_cfg = NetworkInterfaceConfig('dummy0')
        interface_cfg.add_v6_ip('dead:beef::1', 64)
        ips = interface_cfg.get_ips()
        self.assertEqual(len(ips), 1, "dummy interface either didn't get the IP or has multiple!")
        self.assertEqual(ips[0]['ip_address'], 'dead:beef::1', "IP assignment failure!")
        self.assertEqual(ips[0]['family'], AF_INET6, "IP assignment failure!")
        self.assertEqual(ips[0]['prefix_length'], 64, "IP assignment failure!")


    def test_remove_ipv6(self):
        '''Removes an IPv6 address and confirms it'''
        interface_cfg = NetworkInterfaceConfig('dummy0')
        interface_cfg.add_v6_ip('dead:beef::1', 64)
        interface_cfg.remove_ip('dead:beef::1')

        if interface_cfg.get_ips():
            self.fail("dummy configuration returned an IP!")

    def test_duplicate_ip_failure(self):
        '''Tests duplicate address protection'''
        interface_cfg = NetworkInterfaceConfig('dummy0')
        interface_cfg.add_v4_ip(ip_addr='10.0.241.123',
                                broadcast='10.0.241.255',
                                prefixlen=24)

        with self.assertRaises(DuplicateIPError):
            interface_cfg.add_v4_ip(ip_addr='10.0.241.123',
                                    broadcast='10.0.241.255',
                                    prefixlen=24)

    def test_remove_ipv4(self):
        '''Tests interface deconfiguration of v4 addresses'''
        interface_cfg = NetworkInterfaceConfig('dummy0')
        interface_cfg.add_v4_ip(ip_addr='10.0.241.123',
                                broadcast='10.0.241.255',
                                prefixlen=24)

        # Now remove the IP
        interface_cfg.remove_ip('10.0.241.123')

        # And make sure its gone
        if interface_cfg.get_ips():
            self.fail("dummy configuration returned an IP!")

    def test_invalid_ip_check(self):
        '''Makes sure we raise ValueError on if we pass in an invalid IP'''
        interface_cfg = NetworkInterfaceConfig('dummy0')
        with self.assertRaises(ValueError):
            interface_cfg.add_v4_ip(ip_addr='ImNotAnIP!',
                                    broadcast='Nope',
                                    prefixlen=1337)

    def test_check_for_nonexistent_ip(self):
        '''Tests IPNotFound response when getting information for a specific IP'''
        interface_cfg = NetworkInterfaceConfig('dummy0')
        with self.assertRaises(IPNotFound):
            interface_cfg.get_full_ip_info("10.0.21.123")

    def test_get_routes(self):
        '''Tests that get_routes works properly for v4 and v6 addresses'''
        interface_cfg = NetworkInterfaceConfig('eth0')
        interface_cfg.get_routes()

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
