'''
Created on Sep 19, 2015

@author: mcasadevall
'''

import ipaddress
from dynipd.validation import ValidationAndNormlization as check

class Allocation(object):
    '''An _allocation is a block of IP or IPs that a machine can use'''

    def __init__(self, ip_range):
        '''Create a new _allocation based on this range'''

        self._allocation_utilization = {}

        # Do the usual validation and sanity check
        self._allocation = check.confirm_valid_network(ipaddress.ip_network(ip_range, strict=True))

        # Power of 2 math to the rescue; work out how many IPs we represent
        self._total_number_of_ip = 2**(self._allocation.prefixlen)
        self._available_ips = self._total_number_of_ip

        # If we're IPv4, the network address and broadcast addresses are unusable within a block.
        #
        # Go forth and mark them as such
        if self._total_number_of_ip != 1:
            if isinstance(ipaddress.IPv4Network, self._allocation):
                self._mark_broadcast_address()
                self._mark_network_address()

    def get_status(self):
        '''Reports the status of all IPs within a block'''

    def get_usage(self):
        '''Reports current status of IPs within an _allocation'''

    def mark_ip_as_utilized(self):
        '''Marks an IP as utilized'''

    def return_ip_to_standby(self):
        '''Returns an IP to standby if its not being used'''

    def _mark_network_address(self):
        '''Marks the network address in an _allocation'''

        # The network address is always the first one of a block so ...
        self._allocation_utilization[0]['ip_address'] = self._allocation.network_address
        self._allocation_utilization[0]['status'] = 'NETWORK_ADDRESS'
        self._available_ips =- 1

    # pylint: disable=line-too-long
    def _mark_broadcast_address(self):
        '''Mark the broadcast address'''

        # The broadcast address is top of the block
        self._allocation_utilization[self._total_number_of_ip]['ip_address'] = self._allocation.broadcast_address
        self._allocation_utilization[self._total_number_of_ip]['status'] = 'BROADCAST_ADDRESS'
        self._available_ips =- 1
