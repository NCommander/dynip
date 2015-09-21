'''
Created on Sep 19, 2015

@author: mcasadevall
'''

import ipaddress
from dynipd.validation import ValidationAndNormlization as check
from _socket import AF_INET, AF_INET6

class Allocation(object):
    '''An _allocation is a block of IP or IPs that a machine can use'''

    def __init__(self, ip_range):
        '''Create a new _allocation based on this range'''
        self.allocation_id = None
        self._allocation_utilization = {}

        # Do the usual validation and sanity check
        self._allocation = check.confirm_valid_network(ipaddress.ip_network(ip_range, strict=True))
        self._allocation_start = self._allocation.network_address

        address_size = None
        if self._allocation.version == 4:
            address_size = 32
            self.family = AF_INET

        if self._allocation.version == 6:
            address_size = 128
            self.family = AF_INET6

        # Power of 2 math to the rescue; work out how many IPs we represent
        self._total_number_of_ip = 2**(address_size-self._allocation.prefixlen)
        self._available_ips = self._total_number_of_ip

        # The network address is unusable in IPv4, and for our sanity, mark it
        # unusable in IPv6 (dealing with b1oc:: as a valid IP is bleh)
        #
        # If we're IPv4, the  broadcast addresses is unusable within a block.
        if self._total_number_of_ip != 1:
            self._mark_network_address()

            if self.family == AF_INET:
                self._mark_broadcast_address()

    def set_id(self, allocation_id):
        '''Sets the ID from the database to the object'''
        self.allocation_id = allocation_id

    def get_id(self):
        '''Returns stored database ID, or None if one hasn't been assigned'''
        return self.allocation_id

    def get_network_block(self):
        '''Returns string of the CIDR representation of the block'''
        return str(self._allocation)

    def get_usage(self):
        '''Reports the status of all IPs within a block'''
        saner_dict = {}
        for ip_offset, status in sorted(self._allocation_utilization.items()):
            saner_dict.update({(self._allocation_start+ip_offset): status})

            return saner_dict

    def mark_ip_as_reserved(self):
        '''Moves an IP from unused to reserved'''
        raise NotImplementedError('Must be subclassed')

    def move_ip_to_standby(self):
        '''Moves an IP to standby status'''
        raise NotImplementedError('Must be subclassed')

    def move_ip_as_utilized(self):
        '''Moves an IP to standby status'''
        raise NotImplementedError('Must be subclassed')

    def return_ip_to_standby(self):
        '''Returns an IP to standby if its not being used'''
        raise NotImplementedError('Must be subclassed')

    def return_ip_to_unused(self):
        '''Returns an IP to unused'''
        raise NotImplementedError('Must be subclassed')

    def _mark_network_address(self):
        '''Marks the network address in an _allocation'''

        # The network address is always the first one of a block so ...
        self._allocation_utilization.update({0 : 'NETWORK_ADDRESS'})
        self._available_ips =- 1

    # pylint: disable=line-too-long
    def _mark_broadcast_address(self):
        '''Mark the broadcast address'''

        # The broadcast address is top of the block
        self._allocation_utilization.update({self._total_number_of_ip : 'BROADCAST_ADDRESS'})
        self._available_ips =- 1
