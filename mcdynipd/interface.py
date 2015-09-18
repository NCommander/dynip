'''
Network Interface Configuration
Created on Sep 16, 2015

@author: mcasadevall
'''

from socket import AF_INET, AF_INET6
import ipaddress
from pyroute2.iproute import IPRoute

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
    '''High-level abstraction of a network interface's configuration

    NetworkInterfaceConfig is designed to abstract most of the pain of
    work with (rt)netlink directly, and use pythonic methods for manipulating
    network configuration. At a high level, this interface is protocol-neutral,
    though only support for IPv4 and IPv6 has been added.

    Each function call does sanity checks to try and prevent undefined behavior,
    such as defining a link-local address by accident. For ease of use, this
    interface does not use the kernel netlink bind() functionality, and instead
    works in an async fashion. Manipulation of interfaces is rechecked at
    the end of each function to make sure that the state changed properly, and
    to make sure there wasn't some sort of silent failure.

    A single IPRoute() socket is open per instance of this class for performance
    reasons. This class is thread-safe.
    '''
    def __init__(self, interface):
        '''Manipulations the configuration of a given interface

        Args:
            interface - name of the interface to manipulate (i.e. 'eth0')

        Raises:
            InvalidNetworkDevice - if the interface does not exist
        '''

        self.interface = interface
        self.iproute_api = IPRoute()

        # Confirm this is a valid interface
        # This will chuck a IndexError exception if it doesn't exist
        self.interface_index = self._get_interface_index()

    def __del__(self):
        self.iproute_api.close()

    def _get_interface_index(self):
        '''Private API to get the interface index number

        Raises:
            InvalidNetworkDevice - if an interface isn't found by pyroute2
        '''

        try:
            idx = self.iproute_api.link_lookup(ifname=self.interface)[0]
        except IndexError:
            # IndexError means the interface wasn't found. Send a cleaner message up the pipe
            raise InvalidNetworkDevice("Interface not found")

        return idx

    def get_ips(self):
        '''Returns all a list IPs for a given interface. None if no IPs are configures

        IPs are returned in a list of dictionaries for easy enumeration.

        Keys that are always available:
            ip_address - assigned address
            family - protocol family of the returned IP. Either AF_INET, or AF_INET6
            prefix_length - Length of the network prefix assigned to this interface
                            This is the CIDR representation of the netmask.

            if family == AF_INET
                broadcast - broadcast address for an interface
        '''

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
        '''Returns an ip_dict for an individual IP address. Format identical to get_ips()

        Args:
            wanted_address - a valid v4 or v6 address to search for. Value is normalized
                             by ipaddress.ip_address when returning

        Raises:
            ValueError - wanted_address is not a valid IP address
            IPNotFound - this interface doesn't have this IP address
        '''
        wanted_address = validate_and_normalize_ip(wanted_address)

        ips = self.get_ips()

        # Walk the IP table and find the specific IP we want
        for ip_address in ips:
            if ip_address['ip_address'] == wanted_address:
                return ip_address

        # If we get here, the IP wasn't found
        raise IPNotFound("IP not found on interface")

    def add_v4_ip(self, ip_address, prefix_length):
        '''Wrapper for add_ip - adds an IPv4 address to this interface

            Args:
                ip_address = IPv4 address to add
                prefix_length - Network prefix size; netmask and broadcast addresses

             Raises: - see add_ip()
        '''

        ip_dict = {'ip_address': ip_address,
                   'family': AF_INET,
                   'prefix_length': prefix_length}

        self.add_ip(ip_dict)

    def add_v6_ip(self, ip_address, prefix_length):
        '''Wrapper for add_ip - adds an IPv6 address to this interface

            Args:
                ip_address - IPv6 address to add
                prefix_length - Network prefix size; netmask and broadcast addresses

             Raises: - see add_ip()
        '''
        ip_dict = {'ip_address': ip_address,
                   'family': AF_INET6,
                   'prefix_length': prefix_length}

        self.add_ip(ip_dict)

    def add_ip(self, ip_dict):
        '''Adds an IP to an interface. Lower-level function to add an IP address

        Args:
            ip_dict - takes an IP dictionary (see get_ips) and adds it to an interface
                      directorly

        Raises:
            ValueError
                IP address invalid. See message for more info
            DuplicateIPError
                This IP is already configured
            InterfaceConfigurationError
                The ip_dict was valid, but the IP failed add
        '''
        check_and_normalize_ip_dict(ip_dict)

        # Throw an error if we try to add an existing address.
        existing_ip_check = None
        try:
            existing_ip_check = self.get_full_ip_info(ip_dict['ip_address'])
        except IPNotFound:
            pass

        if existing_ip_check:
            raise DuplicateIPError("This IP has already been assigned!")

        # We call add slightly differently based on socket family
        if ip_dict['family'] == AF_INET:
            self.iproute_api.addr('add',
                                  index=self.interface_index,
                                  family=AF_INET,
                                  address=ip_dict['ip_address'],
                                  broadcast=ip_dict['broadcast'],
                                  prefixlen=ip_dict['prefix_length'])

        if ip_dict['family'] == AF_INET6:
            self.iproute_api.addr('add',
                                  index=self.interface_index,
                                  family=AF_INET6,
                                  address=ip_dict['ip_address'],
                                  prefixlen=ip_dict['prefix_length'])

        # Do a sanity check and make sure the IP actually got added
        ip_check = self.get_full_ip_info(ip_dict['ip_address'])

        if not (ip_check['ip_address'] == ip_dict['ip_address'] and
                ip_check['prefix_length'] == ip_dict['prefix_length']):
            raise InterfaceConfigurationError("IP failed to add!")

    def remove_ip(self, ip_address):
        '''Removes an IP from an interface. Full details are looked up via
            get_full_ip_info for removal

            Args:
                ip_address - IP address to remove

            Raises:
                ValueError
                    The IP address provided was invalid
                IPNotFound
                    The IP is not configured on this interface
                InterfaceConfigurationError
                    The IP address was valid, but the IP was not successfully removed
        '''

        # San check
        ip_address = validate_and_normalize_ip(ip_address)

        # Get the full set of IP information
        ip_info = self.get_full_ip_info(ip_address)

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
            self.get_full_ip_info(ip_address)
        except IPNotFound:
            # We got it!
            return

        # Didn't get it. Throw an exception and bail
        raise InterfaceConfigurationError("IP deletion failure")

    def add_default_gateway(self, gateway, prefix_length):
        '''Adds a default gateway for a given prefix length'''

    def add_static_route(self, source, destination):
        '''Sets a static route for an interface'''

    def add_route(self, route_info):
        '''Adds a route for a given interface'''

    def remove_route(self, route_info):
        '''Removes a route from an interface'''

    def get_routes(self):
        '''Gets routes for an interface'''

        # The only way to get routes for an interface is to pull the entire routing table, and
        # filter entries for this interface. Miserable interfaces are miserable. Furthermore,
        # I can only get the v4 and v6 routes as a separate transaction

        # In theory, we can apply a filter to returned routes, but I can't figure out if
        # we can exclude things like cache entries, so we'll just grab stuff on a per family
        # level, and filter for ourselves

        # Pull the v4 and v6 global routing table
        v4_routing_table = self.iproute_api.get_routes(family=AF_INET)
        v6_routing_table = self.iproute_api.get_routes(family=AF_INET6)
        kernel_routing_table = self._filter_routing_table(v4_routing_table + v6_routing_table)

        # _filter_routing_table got rid of most of the junk we don't care about
        # so now we need to walk the table and make it something far similar to
        # praise without ripping our hair out. We also filter out link-local
        # addresses in this step because we need the full prefix to know if its
        # a link-local network

        routing_table = []
        for route in kernel_routing_table:
            route_dict = {}

            # Let's get the easy stuff first
            for attribute in route['attrs']:
                if attribute[0] == 'RTA_PREFSRC':
                    route_dict['source'] = attribute[1]
                if attribute[0] == 'RTA_DST':
                    route_dict['destination'] = attribute[1]
                if attribute[0] == 'RTA_GATEWAY':
                    route_dict['gateway'] = attribute[1]

            # Family is mapped straight through so AF_INET and AF_INET6 just match
            route_dict['family'] = route['family']

            # Attach prefixes if they're non-zero
            if route['src_len'] != 0 and 'source' in route_dict:
                route_dict['source'] += ("/%s" % route['src_len'])
            if route['dst_len'] != 0 and 'destination' in route_dict:
                route_dict['destination'] += ("/%s" % route['dst_len'])

                # Check for link-local here
                if ipaddress.ip_network(route_dict['destination']).is_link_local:
                    continue # skip the route

            if route['dst_len'] != 0 and 'gateway' in route_dict:
                route_dict['gateway'] += ("/%s" % route['dst_len'])

            # Map the protocol to something human-readable
            route_dict['protocol'] = map_protocol_number_to_string(route['proto'])
            route_dict['type'] = determine_route_type(route_dict)

            routing_table.append(route_dict)
        return routing_table

    def determine_if_route_exists(self):
        '''Checks if a route exists'''

    def validate_route_dict(self):
        '''Validates a routing information dict'''

    def _filter_routing_table(self, routing_table):
        '''Internal API. Takes output of get_routes, and filters down to what we care about'''

        # For every configured IP address, a couple of automatic routes are
        # generated that we're not interested in.
        #
        # Understanding this code requires an understanding of how the Linux kernel
        # handles routing and routing tables. For each interface, the kernel has a possible
        # 255 tables to hold routes. These exist to allow for specific routing rules and
        # preferences as the system goes from table 255->1 in determining which route
        # will be used.
        #
        # On a default configuration, only three routing tables are defined:
        # 255 - local
        # 254 - main
        # 253 - default
        #
        # Table names are controlled in /etc/iproutes.d/rt_tables
        #
        # The local table is special as it can only be added to by the kernel, and removing
        # entries from it is explicitly done "at your own risk". It defines which IPs this
        # machine owns so any attempt to communicate on it comes back to itself. As such
        # we can simply filter out 255 to make our lives considerably easier
        #
        # Unfortunately, filtering 255 doesn't get rid of all the "line noise" so to speak.
        #
        # From this point forward, I've had to work from kernel source, and the source of
        # iproute2 to understand what's going on from netlayer. But basically, here's the
        # rundown of what we need to do
        #
        # Case 1 - Cached Entries
        # This is a surprising complicated case. Cached entries are used by the kernel for
        # automatically configured routes. I haven't seen the kernel v4 table populated, but
        # that may just be because of my local usage
        #
        # IPv6 is a different story. Routing information for IPv6 can come in the form of
        # routing announcements, static configuration, and so forth. It seems all IPv6 info is
        # is marked as a cached entry. This is made more complicated that the kernel stores
        # various IPv6 routing information in the table for "random" hosts accessed. For example.
        # on my home system ...
        #
        # mcasadevall@perdition:~/workspace/mcdynipd$ route -6 -C
        # Kernel IPv6 routing cache
        # Destination                    Next Hop                   Flag Met Ref Use If
        # 2001:4860:4860::8888/128       fe80::4216:7eff:fe6c:492   UGDAC 0   0    47 eth0
        # 2607:f8b0:4001:c09::bc/128     fe80::4216:7eff:fe6c:492   UGDAC 0   1    17 eth0
        # 2607:f8b0:4004:808::1013/128   fe80::4216:7eff:fe6c:492   UGDAC 0   1    21 eth0
        # 2607:f8b0:4009:805::1005/128   fe80::4216:7eff:fe6c:492   UGDAC 0   0     3 eth0
        # 2607:f8b0:4009:80a::200e/128   fe80::4216:7eff:fe6c:492   UGDAC 0   0    85 eth0
        # 2607:f8b0:400d:c04::bd/128     fe80::4216:7eff:fe6c:492   UGDAC 0   1    76 eth0
        #
        # 2607:f8b0::/32 is owned by Google, and these were connections my system made to Google
        # systems. Looking at my router (which runs a 6to4 HE tunnel), it appears 6to4 is handled
        # via static routing and should show up sans CACHEINFO (untested - needs confirmation).
        #
        # Digging into iproute2, the proto field defines what defined a route. Here's the list
        # defined in the source
        #
        # ----------------------------------------------------------------------------
        # #define RTPROT_UNSPEC   0
        # #define RTPROT_REDIRECT 1       /* Route installed by ICMP redirects;
        #                                     not used by current IPv4 */
        # #define RTPROT_KERNEL   2       /* Route installed by kernel            */
        # #define RTPROT_BOOT     3       /* Route installed during boot          */
        # #define RTPROT_STATIC   4       /* Route installed by administrator     */
        #
        # /* Values of protocol >= RTPROT_STATIC are not interpreted by kernel;
        #    they are just passed from user and back as is.
        #    It will be used by hypothetical multiple routing daemons.
        #    Note that protocol values should be standardized in order to
        #    avoid conflicts.
        #  */
        #
        # #define RTPROT_GATED    8       /* Apparently, GateD */
        # #define RTPROT_RA       9       /* RDISC/ND router advertisements */
        # #define RTPROT_MRT      10      /* Merit MRT */
        # #define RTPROT_ZEBRA    11      /* Zebra */
        # #define RTPROT_BIRD     12      /* BIRD */
        # #define RTPROT_DNROUTED 13      /* DECnet routing daemon */
        # #define RTPROT_XORP     14      /* XORP */
        # #define RTPROT_NTK      15      /* Netsukuku */
        # #define RTPROT_DHCP     16      /* DHCP client */
        # #define RTPROT_MROUTED  17      /* Multicast daemon */
        # ----------------------------------------------------------------------------
        #
        # Looking at the behavior of the kernel, if a given prefix has a route, it will
        # place a proto 2 entry for it with no routing address. Cached table entries
        # exist to the next point:
        #
        # 2001:4860:4860::8888/128       fe80::4216:7eff:fe6c:492   UGDAC 0   0    47 eth0
        #
        # (this shows up as proto 9 in the routing table)
        #
        # To get the default route of a device in IPv6, we need entries that ONLY have RTA_GATEWAY
        # and not RTA_DEST, regardless of protocol. Otherwise, we filter out proto 9. This gets
        # output identical to route aside from the multicast address (ff00::/8)
        #
        # As a final note to this saga, after I coded this, I found rtnetlink is documented on
        # Linux systems. Run man 7 rtnetlink to save yourself a source dive :(

        filtered_table = []
        non_cached_table = []

        # Pass 1. Exclude table 255, and any entries that have RTA_CACHEINFO
        for route in routing_table:
            # If this is a 255 entry, ignore it, we don't care
            if route['table'] == 255:
                continue

            # Now the table cache
            cached_entry = False
            destination_address = None
            gateway_address = None

            routing_attributes = route['attrs']
            for attribute in routing_attributes:
                if attribute[0] == 'RTA_CACHEINFO':
                    cached_entry = True
                if attribute[0] == 'RTA_DST':
                    destination_address = attribute[1]
                if attribute[0] == 'RTA_GATEWAY':
                    gateway_address = attribute[1]

            # If its not a cached entry, always keep it
            if not cached_entry:
                non_cached_table.append(route)
                continue

            # Keep it if proto != 9
            if route['proto'] != 9:
                non_cached_table.append(route)
                continue

            # If it only has DST or GATEWAY, its a default route, keep it
            if ((gateway_address and not destination_address) or
                    (destination_address and not gateway_address)):
                non_cached_table.append(route)
                continue

        for route in non_cached_table:
            # Like IP addresses, most of the route information is stored
            # in attributes. RTA_OIF (OIF = Outbound Interface), contains
            # the index number of the interface this route is assigned to
            routing_attributes = route['attrs']

            for attribute in routing_attributes:
                if attribute[0] == 'RTA_OIF' and attribute[1] == self.interface_index:
                    filtered_table.append(route)

        # filtered_table should just contain our OIFs, pass this back up for
        # processing
        return filtered_table

# Utility functions go down here
def validate_and_normalize_ip(ip_addr):
    '''Validates an IP address using ipaddress'''
    return str(ipaddress.ip_address(ip_addr))

def confirm_valid_network(ip_network):
    '''Confirms a network is valid for unicast assignment'''
    if ip_network.is_loopback:
        raise ValueError('Will not allocate loopback address')

    if ip_network.is_link_local:
        raise ValueError('Will not allocate link-local address')

    if ip_network.is_multicast:
        raise ValueError('Will not allocate multicast address')

    if ip_network.is_reserved:
        raise ValueError('Will not use reserved address space')

    if ip_network.is_unspecified:
        raise ValueError('Will not use unspecified address space')

def check_and_normalize_ip_dict(ip_dict):
    '''Validates and normalize the information given in an ip_dict'''

    # Check IP first, and make sure we've got the right family
    ip_address = ipaddress.ip_address(ip_dict['ip_address'])

    # Validate based on address family
    if ip_dict['family'] == AF_INET:
        # First, make sure we've got a v4 address
        if not isinstance(ip_address, ipaddress.IPv4Address):
            raise ValueError('AF_INET specified, but not an IPv4 address.')

        # Glue the prefix length on, and calculate the broadcast address
        ip_network = ipaddress.ip_network(str(ip_address) + "/%s" % ip_dict['prefix_length'],
                                          strict=False)
        ip_dict['ip_address'] = str(ip_address)
        ip_dict['broadcast'] = str(ip_network.broadcast_address)

        # Make sure we're not using the network address or broadcast as an actual network address
        if ip_network.broadcast_address == ip_address:
            raise ValueError('Refusing to add broadcast address as an IP')

        if ip_network.network_address == ip_address:
            raise ValueError('Refusing to use network address as IP due to prefix length!')

        # Final checks, make sure we're not using loopback, multicast address or class E address
        confirm_valid_network(ip_network)

    elif ip_dict['family'] == AF_INET6:
        # v6 is slightly similar, we just need to validate the address, and the prefix_length
        if not isinstance(ip_address, ipaddress.IPv6Address):
            raise ValueError('AF_INET6 specified but not an IPv6 adddress')

        # Normalizing v6 addresses is important for sanity reasons
        ip_dict['ip_address'] = str(ip_address)

        # I've debated making this check stricter by disallowing < 32 ...
        if ip_dict['prefix_length'] < 1 or ip_dict['prefix_length'] > 128:
            raise ValueError('Invalid prefix length')

        # Generate a IPv6Network object to do final confirmation tests
        ip_network = ipaddress.ip_network(str(ip_address) + "/%s" % ip_dict['prefix_length'],
                                          strict=False)

        # Run the battery of IPv6 sanity checks
        confirm_valid_network(ip_network)

    else:
        raise ValueError('Unknown protocol family')


def map_protocol_number_to_string(protocol_number):
    '''Maps kernel routing protocol to string.'''
    protocol_mapping_table = {0: 'unspec',
                              1: 'redirect',
                              2: 'kernel',
                              3: 'boot',
                              4: 'static',
                              8: 'gated',
                              9: 'ra',
                              10: 'mrt',
                              11: 'zebra',
                              12: 'bird',
                              13: 'decnet',
                              14: 'xorp',
                              15: 'ntk',
                              16: 'dhcp',
                              17: 'mrouted'}

    return protocol_mapping_table.get(protocol_number, 'unknown')

def determine_route_type(route):
    '''Determines the type of route depending on the fields set'''
    route_type = 'unknown'

    # Handle the known cases
    if 'source' in route and 'destination' in route:
        # Special case if source is a network, and NOT an address, its a network route
        try:
            ipaddress.ip_network(route['source'], strict=True)
        except ValueError:
            # It's point to point, return static
            return 'static'

        route_type = 'network'
    if 'destination' in route and not 'source' in route:
        route_type = 'network'

    if 'gateway' in route:
        route_type = 'default'

    return route_type
