'''
Network Interface Configuration
Created on Sep 16, 2015

@author: mcasadevall
'''

from socket import AF_INET, AF_INET6
import ipaddress
from pyroute2.iproute import IPRoute

def validate_ip(ip_addr):
    '''Validates an IP address using ipaddress'''
    ipaddress.ip_address(ip_addr)

class InterfaceConfigurationError(Exception):
    '''An interface failed to configure; this error is generated if
    an IP still exists/doesn't exist after calling IPRoute. Check
    the kernel dmesg and syslog to debug'''
    def __init__(self, value):
        super(InterfaceConfigurationError, self).__init__(value)
        self.value = value
    def __str__(self):
        return repr(self.value)

class IPNotFound(Exception):
    '''The requested IP in getIP/getFullIP was not found on this interface'''
    def __init__(self, value):
        super(IPNotFound, self).__init__(value)
        self.value = value
    def __str__(self):
        return repr(self.value)

class InvalidNetworkDevice(Exception):
    '''The interface specified does not exist'''
    def __init__(self, value):
        super(InvalidNetworkDevice, self).__init__(value)
        self.value = value
    def __str__(self):
        return repr(self.value)

class DuplicateIPError(Exception):
    '''The interface already has this IP. Delete and readd to reconfigure'''
    def __init__(self, value):
        super(DuplicateIPError, self).__init__(value)
        self.value = value
    def __str__(self):
        return repr(self.value)

class NetworkInterfaceConfig(object):
    '''
    classdocs
    '''
    def __init__(self, interface):
        '''Manipulations the configuration of a given interface

        Args:
            interface - name of the interface to manipulate

        Raises:
            IndexError - if the interface does not exist
        '''

        self.interface = interface
        self.iproute_api = IPRoute()

        # Confirm this is a valid interface
        # This will chuck a IndexError exception if it doesn't exist
        self.interface_index = self.get_interface_index()

    def __del__(self):
        self.iproute_api.close()

    def get_interface_index(self):
        '''
        Retrieve the index for a given interface.
        '''

        try:
            idx = self.iproute_api.link_lookup(ifname=self.interface)[0]
        except IndexError:
            # IndexError means the interface wasn't found. Send a cleaner message up the pipe
            raise InvalidNetworkDevice("Interface not found")

        return idx

    def get_ips(self, fullinfo=False):
        '''Returns all a list IPs for a given interface. None if no IPs are configures'''

        # I'd like to use label= here, but IPv6 information is not returned
        # when doing so. Possibly a bug in pyroute2
        ip_cfgs = self.iproute_api.get_addr(index=self.interface_index)

        # get_addr returns IPs in a nasty to praise format. We need to look at the attrs
        # section of each item we get, and find IFA_ADDRESS, and check the second element
        # of the tuple to get the IP address

        # Here's an example of what we're praising
        #
        # [{'attrs': [['IFA_ADDRESS', '10.0.241.123'],
        #    ['IFA_LOCAL', '10.0.241.123'],
        #    ['IFA_BROADCAST', '10.0.241.255'],
        #    ['IFA_LABEL', 'dummy0'],
        #    ['IFA_CACHEINFO',
        #     {'cstamp': 181814615,
        #      'ifa_prefered': 4294967295,
        #      'ifa_valid': 4294967295,
        #      'tstamp': 181814615}]],
        #      'event': 'RTM_NEWADDR',
        #      'family': 2,
        #      'flags': 128,
        #      'header': {'error': None,
        #                 'flags': 2,
        #                 'length': 80,
        #                 'pid': 4294395048,
        #                 'sequence_number': 255,
        #                 'type': 20},
        #      'index': 121,
        #      'prefixlen': 24,
        #      'scope': 0}]'''

        # Walk the list
        ips = []
        for ip_cfg in ip_cfgs:
            iproute_api = None
            broadcast = None
            prefixlen = None

            ip_attrs = ip_cfg['attrs']
            for attribute in ip_attrs:
                if attribute[0] == "IFA_ADDRESS":
                    iproute_api = attribute[1]
                if attribute[0] == "IFA_BROADCAST":
                    broadcast = attribute[1]
            prefixlen = ip_cfg['prefixlen']

            if fullinfo:
                ips.append((iproute_api, broadcast, prefixlen))
            else:
                ips.append(iproute_api)

        # And break!
        return ips

    def get_full_ip_info(self, wanted_address):
        '''Retrieves the broadcast, and prefix length for a given IP on this interface'''
        ips = self.get_ips(fullinfo=True)

        # Walk the IP table and find the specific IP we want
        for ip_address in ips:
            if ip_address[0] == wanted_address:
                return ip_address

        # If we get here, the IP wasn't found
        raise IPNotFound("IP not found on interface")

    def add_v4_ip(self, ip_addr, broadcast, prefixlen):
        '''Adds an IPv4 address to this interface'''
        self.add_ip(ip_addr, AF_INET, broadcast, prefixlen)

    def add_v6_ip(self, ip_addr, prefixlen):
        '''Adds an IPv6 address to this interface'''
        self.add_ip(ip_addr, AF_INET6, None, prefixlen)

    def add_ip(self, ip_addr, family, broadcast, prefixlen):
        '''Adds an IP to an interface'''
        validate_ip(ip_addr)

        # Throw an error if we try to add an existing address.
        existing_ip_check = None
        try:
            existing_ip_check = self.get_full_ip_info(ip_addr)
        except IPNotFound:
            pass

        if existing_ip_check:
            raise DuplicateIPError("This IP has already been assigned!")

        # We call add slightly differently based on socket family
        if family == AF_INET:
            self.iproute_api.addr('add',
                                  index=self.interface_index,
                                  address=ip_addr,
                                  broadcast=broadcast,
                                  prefixlen=prefixlen)

        if family == AF_INET6:
            self.iproute_api.addr('add',
                                  index=self.interface_index,
                                  family=AF_INET6,
                                  address=ip_addr,
                                  prefixlen=prefixlen)

        # Do a sanity check and make sure the IP actually got added
        ip_check = self.get_full_ip_info(ip_addr)

        if not (ip_check[0] == ip_addr and
                ip_check[1] == broadcast and
                ip_check[2] == prefixlen):
            raise InterfaceConfigurationError("IP failed to add!")

    def remove_ip(self, ip_addr):
        '''Removes an IP from an interface'''
        validate_ip(ip_addr)

        # Get the full set of IP information
        ip_info = self.get_full_ip_info(ip_addr)

        # Attempt to delete
        self.iproute_api.addr('delete',
                              index=self.interface_index,
                              address=ip_info[0],
                              broadcast=ip_info[1],
                              prefixlen=ip_info[2])

        # Confirm the delete. get_full_ip_info will throw an exception if it can't find it
        try:
            self.get_full_ip_info(ip_addr)
        except IPNotFound:
            # We got it!
            return

        # Didn't get it. Throw an exception and bail
        raise InterfaceConfigurationError("IP deletion failure")
