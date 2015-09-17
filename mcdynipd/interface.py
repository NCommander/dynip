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

# Exception classes for Network Interface Configuration
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

    def get_ips(self):
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
            ip_address = None
            family = None
            broadcast = None
            prefixlen = None

            ip_attrs = ip_cfg['attrs']
            for attribute in ip_attrs:
                if attribute[0] == "IFA_ADDRESS":
                    ip_address = attribute[1]
                if attribute[0] == "IFA_BROADCAST":
                    broadcast = attribute[1]
            prefixlen = ip_cfg['prefixlen']
            family = ip_cfg['family'] # 2 for AF_INET, 10 for AF_INET6

            # Build IP dictionary
            ip_dict = {'ip_address': ip_address,
                       'prefix_length': prefixlen,
                       'family' : family}

            # Handle v4-only information
            if broadcast:
                ip_dict['broadcast'] = broadcast

            # Push it onto the list to be returned
            ips.append(ip_dict)

        # And break!
        return ips

    def get_full_ip_info(self, wanted_address):
        '''Retrieves the broadcast, and prefix length for a given IP on this interface'''
        ips = self.get_ips()

        # Walk the IP table and find the specific IP we want
        for ip_address in ips:
            if ip_address['ip_address'] == wanted_address:
                return ip_address

        # If we get here, the IP wasn't found
        raise IPNotFound("IP not found on interface")

    def add_v4_ip(self, ip_addr, broadcast, prefixlen):
        '''Adds an IPv4 address to this interface'''

        ip_dict = {'ip_address': ip_addr,
                   'family': AF_INET,
                   'broadcast': broadcast,
                   'prefix_length': prefixlen}

        self.add_ip(ip_dict)

    def add_v6_ip(self, ip_addr, prefixlen):
        '''Adds an IPv6 address to this interface'''
        ip_dict = {'ip_address': ip_addr,
                   'family': AF_INET6,
                   'prefix_length': prefixlen}

        self.add_ip(ip_dict)

    def add_ip(self, ip_info):
        '''Adds an IP to an interface'''
        validate_ip(ip_info['ip_address'])

        # Throw an error if we try to add an existing address.
        existing_ip_check = None
        try:
            existing_ip_check = self.get_full_ip_info(ip_info['ip_address'])
        except IPNotFound:
            pass

        if existing_ip_check:
            raise DuplicateIPError("This IP has already been assigned!")

        # We call add slightly differently based on socket family
        if ip_info['family'] == AF_INET:
            self.iproute_api.addr('add',
                                  index=self.interface_index,
                                  family=AF_INET,
                                  address=ip_info['ip_address'],
                                  broadcast=ip_info['broadcast'],
                                  prefixlen=ip_info['prefix_length'])

        if ip_info['family'] == AF_INET6:
            self.iproute_api.addr('add',
                                  index=self.interface_index,
                                  family=AF_INET6,
                                  address=ip_info['ip_address'],
                                  prefixlen=ip_info['prefix_length'])

        # Do a sanity check and make sure the IP actually got added
        ip_check = self.get_full_ip_info(ip_info['ip_address'])

        if not (ip_check['ip_address'] == ip_info['ip_address'] and
                ip_check['prefix_length'] == ip_info['prefix_length']):
            raise InterfaceConfigurationError("IP failed to add!")

    def remove_ip(self, ip_addr):
        '''Removes an IP from an interface'''
        validate_ip(ip_addr)

        # Get the full set of IP information
        ip_info = self.get_full_ip_info(ip_addr)

        # Attempt to delete
        if ip_info['family'] == AF_INET:
            self.iproute_api.addr('delete',
                                  index=self.interface_index,
                                  address=ip_info['ip_address'],
                                  broadcast=ip_info['broadcast'],
                                  prefixlen=ip_info['prefix_length'])

        if ip_info['family'] == AF_INET6:
            self.iproute_api.addr('delete',
                                  index=self.interface_index,
                                  address=ip_info['ip_address'],
                                  prefixlen=ip_info['prefix_length'])

        # Confirm the delete. get_full_ip_info will throw an exception if it can't find it
        try:
            self.get_full_ip_info(ip_addr)
        except IPNotFound:
            # We got it!
            return

        # Didn't get it. Throw an exception and bail
        raise InterfaceConfigurationError("IP deletion failure")

    def add_route(self):
        '''Adds a route for a given interface'''

    def remove_route(self):
        '''Removes a route from an interface'''

    def get_routes(self):
        '''Gets routes for an interface'''

        # The only way to get routes for an interface is to pull the entire routing table, and
        # find entries for this interface. Miserable interfaces are miserable. Furthermore,
        # I can only get the v4 and v6 routes as a separate transaction

        # Pull the v4 global routing table
        v4_routing_table = self.iproute_api.get_routes(family=AF_INET)
        filtered_v4_table = self._filter_routing_table(v4_routing_table)

        import pprint
        #pprint.pprint(filtered_v4_table)
        return

    def determine_if_route_exists(self):
        '''Checks if a route exists'''

    def _filter_routing_table(self, routing_table):
        '''Internal API. Takes output of get_routes, and filters down to what we care about'''

        # For every configured IP address, a couple of automatic routes are
        # generated that we're not interested in.
        #
        # Case 1, the self route:
        # The routing table has a "self" route indicating packets to this IP
        # should come to ourselves. Technically, we can filter on table 255 (local)
        # for this, but its possible that this information may be stored in a different
        # table. I won't put it past NetworkManager to do exactly that
        #
        # We can identify these routes since DST and PREFSRC will match, but we need
        # to walk attrs again to find these, so store this route in a temp variable
        # for a second route of processing
        #
        # Case 2, self->broadcast (IPv4 only)
        # When an IP is configured via netlink, it gets a routing entry of itself
        # to the broadcast address. Unfortunately, to figure this out requires knowing
        # our prefix length, and the broadcast address of an interface. We then compare
        # DST to the broadcast entry.

        # Python best practices says to build a new list every time we
        # need to edit it. That's a lot of lists
        filtered_table = []
        interface_routes = []

        for route in routing_table:
            # Like IP addresses, most of the route information is stored
            # in attributes. RTA_OIF (OIF = Outbound Interface), contains
            # the index number of the interface this route is assigned to
            routing_attributes = route['attrs']


            for attribute in routing_attributes:
                if attribute[0] == 'RTA_OIF' and attribute[1] == self.interface_index:
                    interface_routes.append(route)

            # Now we loop through the interface routes, and get rid of the ones we don't care about
            for route in interface_routes:
                # Gateway routes won't have this attribute
                # they only exist on point-to-point routes
                route_prefsrc = None
                route_dst = None
                for attribute in routing_attributes:
                    if attribute[0] == 'RTA_PREFSRC':
                        route_prefsrc = attribute[1]
                    if attribute[0] == 'RTA_DST':
                        route_dst = attribute[1]

                # Now we do the check and decide if we want to filter or not
                if route_prefsrc != route_dst:
                    filtered_table.append(route)

        # filtered_table should just contain our OIFs, pass this back up for
        # processing
        return filtered_table

