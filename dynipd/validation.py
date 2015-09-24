'''
Created on Sep 20, 2015

@author: mcasadevall
'''

import ipaddress
from socket import AF_INET, AF_INET6
from twisted.internet import address

class ValidationAndNormlization(object):
    '''Catch-all for validationing information'''

    @staticmethod
    def is_valid_ip_family(family):
        '''Confirmed a family is AF_INET or AF_INET6'''
        if not (family == AF_INET or family == AF_INET6):
            raise ValueError('Unknown family error')

        return family

    @staticmethod
    def is_ip_within_block(ip_address, ip_network):
        '''Checks that an IP is within a given CIDR block'''

        # If we got a string, create the right objects
        if isinstance(ip_address, str):
            ip_address = ipaddress.ip_address(ip_address)
        if isinstance(ip_network, str):
            ip_network = ipaddress.ip_network(ip_network, strict=True)

        # Create an IPvXNetwork from the address
        ip_network_origin = ipaddress.ip_network(ip_address)

        return ip_network.overlaps(ip_network_origin)

    @staticmethod
    def validate_and_normalize_ip_network(ip_network):
        '''Validates a CIDR network and normalizes it'''
        return str(ipaddress.ip_network(ip_network))

    @staticmethod
    def validate_and_normalize_ip(ip_addr):
        '''Validates an IP address using ipaddress'''
        return str(ipaddress.ip_address(ip_addr))

    @staticmethod
    def is_valid_prefix_size(prefix_length, family):
        '''Checks that the prefix is valid for the family'''
        if family == AF_INET:
            if prefix_length < 1 or prefix_length > 128:
                raise ValueError('Invalid prefix length')

        if family == AF_INET6:
            if prefix_length < 1 or prefix_length > 128:
                raise ValueError('Invalid prefix length')
        return prefix_length

    @staticmethod
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
        return ip_network

    @staticmethod
    def validate_and_normalize_ip_dict(ip_dict):
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

            # Make sure we're not using the network address or broadcast as an actual address
            if ip_network.broadcast_address == ip_address:
                raise ValueError('Refusing to add broadcast address as an IP')

            if ip_network.network_address == ip_address:
                raise ValueError('Refusing to use network address as IP due to prefix length!')

            # Make sure prefix length is sane
            ValidationAndNormlization.is_valid_prefix_size(ip_dict['prefix_length'],
                                                           ip_dict['family'])

            # Final checks, make sure we're not using loopback, multicast address or class E address
            ValidationAndNormlization.confirm_valid_network(ip_network)

        elif ip_dict['family'] == AF_INET6:
            # v6 is slightly similar, we just need to validate the address, and the prefix_length
            if not isinstance(ip_address, ipaddress.IPv6Address):
                raise ValueError('AF_INET6 specified but not an IPv6 adddress')

            # Normalizing v6 addresses is important for sanity reasons
            ip_dict['ip_address'] = str(ip_address)

            # I've debated making this check stricter by disallowing < 32 ...
            ValidationAndNormlization.is_valid_prefix_size(ip_dict['prefix_length'],
                                                           ip_dict['family'])

            # Generate a IPv6Network object to do final confirmation tests
            ip_network = ipaddress.ip_network(str(ip_address) + "/%s" % ip_dict['prefix_length'],
                                              strict=False)

            # Run the battery of IPv6 sanity checks
            ValidationAndNormlization.confirm_valid_network(ip_network)

        else:
            raise ValueError('Unknown protocol family')

        return ip_dict
