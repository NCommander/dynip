'''
DynIPD - MySQL datastore for network configuration
Created on Sep 19, 2015

@author: mcasadevall
'''

import mysql.connector
from dynipd.server.allocation import AllocationServerSide
from dynipd.network_block import NetworkBlock
from dynipd.validation import ValidationAndNormlization as check
from dynipd.server.machine import Machine

class MySQLDataStore(object):
    '''Implements the data storage model on a MySQL database'''
    _networks = { }

    def __init__(self, db_info_dict):
        '''Opens a connection to the MySQL database'''
        self.db_info = db_info_dict
        self.mysql_pool = mysql.connector.pooling.MySQLConnectionPool(pool_name = "datastore_pool",
                                                                     pool_size=20,
                                                                     **self.db_info)

        #self._refresh_network_topogoly()

    def create_machine(self, name, token):
        '''Creates a machine in the database'''
        query = 'INSERT INTO machine_info (name, token) VALUES (%s, %s)'
        self._do_insert(query, (name,token))

    def create_network(self, name, location, family, network, allocation_size, reserved_blocks):
        # pylint: disable=too-many-arguments
        '''Creates a network in the database'''

        # Argument validation
        check.is_valid_ip_family(family)
        network = check.validate_and_normalize_ip_network(network)
        check.is_valid_prefix_size(allocation_size, family)

        # FIXME: make sure we're not trying to add ourselves twice
        query = '''INSERT INTO network_topology (name, location, family, network, allocation_size,
                                                 reserved_blocks) VALUES (%s, %s, %s,%s, %s, %s)'''

        self._do_insert(query, (name, location, int(family), network, allocation_size,
                               reserved_blocks))

        # Update our state information to see the new network
        self.refresh_network_topogoly()

    def assign_new_allocation(self, machine, new_allocation):
        '''Assigns an a new allocation to a machine'''

        # Sanity check the input
        if not isinstance(machine, Machine):
            raise ValueError('machine is not Machine object')
        if not isinstance(new_allocation, AllocationServerSide):
            raise ValueError('new_allocation must be AllocationServerSide')

        query = '''INSERT INTO allocated_blocks (allocated_block, network_id, machine_id, status,
                   reservation_expires) VALUES
                   (%s, %s, %s, 'RESERVED', ADDTIME(NOW(), '00:05:00'))'''

        allocation_id = self._do_insert(query,  (new_allocation.get_allocation_cidr(),
                                                 new_allocation.get_network_block().get_id(),
                                                 machine.get_id()))

        new_allocation.set_id(allocation_id)

        # Return the allocation+ID to the caller
        return new_allocation

    def set_ip_status(self, ip_address, status, allocation, machine):
        '''Sets an IP status to reserved in the database'''

        # Sanity check our input
        ip_address = check.validate_and_normalize_ip(ip_address)
        if not isinstance(allocation, AllocationServerSide):
            raise ValueError('Invalid Allocation object')
        if not isinstance(machine, Machine):
            raise ValueError('Invalid Machine object')
        if not (status == 'UNMANAGED' or
                status == 'RESERVED' or
                status == 'STANDBY' or
                status == 'ACTIVE_UTILIZATION'):
            raise ValueError('Invalid status for IP')

        # We use REPLACE to make sure statuses are always accurate to the server. In case
        # of conflict, the server is always the correct source of information
        query = '''REPLACE INTO ip_allocations (from_allocation, allocated_to, ip_address,
                   status, reservation_expires) VALUES (%s, %s, %s, %s, %s)'''

        # reservation status is null unless we're going to/from RESERVED
        reservation_status = 'NULL'
        self._do_insert(query, (allocation.get_id(),
                                machine.get_id(),
                                ip_address,
                                status,
                                reservation_status))

    def refresh_network_topogoly(self):
        '''Updates the network topology in the database'''

        # Setup the connection, and cursor
        cnx = self.mysql_pool.get_connection()
        cursor = cnx.cursor(dictionary=True)

        # Pull the entire topology from the database
        query = "SELECT * FROM network_topology ORDER BY id"
        cursor.execute(query)

        for row in cursor:
            self._networks[row['id']] = NetworkBlock(row, self)

        cnx.close()

    def get_machine(self, name):
        '''Retrieves a machine from the database'''
        cnx = self.mysql_pool.get_connection()
        cursor = cnx.cursor(dictionary=True)
        query = '''SELECT * FROM machine_info WHERE name=%s'''
        cursor.execute(query, (name,))
        machine_dict = cursor.fetchone()
        cnx.close()

        return machine_dict

    def get_network_by_name(self, network_name):
        '''Returns the network with a given name'''
        network_list = self.get_networks()

        for network in network_list:
            if network_name == network.get_name():
                return network

        # Network not found
        raise ValueError('Network does not exist')

    def get_networks(self):
        '''Returns a list of networks'''

        network_list = []
        # We don't want to return the internal dict because someone might do something stupid with
        # it, especially because it exposes the id number. So build a list and return that

        for network in self._networks.values():
            network_list.append(network)

        return network_list


    # Helper for test code; used to load the schema into a test database
    def load_file_into_database(self, filename):
        #pylint: disable=unused-variable

        '''Reads a file and executes all queries in it. Meant for use by the testing API'''
        file = open(filename, mode='r')
        sql = file.read()
        file.close()

        # Setup the connection, and cursor
        cnx = self.mysql_pool.get_connection()
        cursor = cnx.cursor()
        result = cursor.execute(sql, multi=True)

        # We need to iterate on result to get it to execute; while loop just hangs
        for row in result: #@UnusedVariable
            pass
        cnx.close()

    def _do_insert(self, query, argument_tuple):
        '''Wrapper for doing INSERTs. Returns lastrowid'''
        cnx = self.mysql_pool.get_connection()
        cursor = cnx.cursor()
        cursor.execute(query, argument_tuple)
        cnx.commit()
        cnx.close()

        return cursor.lastrowid
