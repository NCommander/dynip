'''
Created on Sep 19, 2015

@author: mcasadevall
'''

class AllocationManagement(object):
    '''Interface for manipulating network state information in the database'''

    def __init__(self, location):
        '''Constructor'''

    def get_policy_information(self):
        '''Shows allocation policies'''

    def get_networks(self):
        '''Retrieves networks for this location'''

    def get_allocation_usage(self):
        '''Returns total number of IPs on this machine'''

    def reserve_unused_allocation(self):
        '''Finds an unallocated IP, and allocates it'''

    def configure_allocation(self):
        '''Configurations an allocation on a network'''

    def confirm_configuration(self):
        '''Confirms an allocation is properly configured'''

    def release_ip_to_pool(self):
        '''Releases an allocated IP back to the pool'''

    def _refresh_state_from_db(self):
        '''Updates the topology from the database'''
