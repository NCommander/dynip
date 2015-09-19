#!/usr/bin/python3
'''
DynIPD - Dynamic static IP configuration
'''

import sys
import argparse
import configparser
from dynipd.config_parser import ConfigurationParser
from dynipd.mysql_datastore import MySQLDataStore

def main():
    '''Starts by loading our configuration and reporting settings'''

    # Let's start with some basic environment setup. Argument parsing comes file
    parser_description = "Dynamically Configures Static IPs From A Database"
    parser = argparse.ArgumentParser(description=parser_description,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-c", "--config-file",
                        dest='filename',
                        help="Configuration file for dynipd",
                        metavar="FILE", default="/etc/dynipd.ini")
    args = parser.parse_args()

    cfg_file = None
    try:
        cfg_file = ConfigurationParser(args.filename)
    except FileNotFoundError:
        sys.stderr.write(("Configuration file %s not found. Bailing out!\n") % args.filename)
        sys.exit(-1)
    except configparser.MissingSectionHeaderError:
        sys.stderr.write("Configuration stanza is missing. Bailing out!\n")
        sys.exit(-1)

    # Establish connection to the datastore
    data_store = MySQLDataStore(cfg_file.get_database_configuration())
#    import pprint
#    pprint.pprint(cfg_file.get_database_configuration())
main()
