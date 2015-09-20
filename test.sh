#!/bin/bash
# We have to ignore warnings because mysql.connector's pool doesn't have a method to close cleanly
sudo PYHTONPATH=`pwd` python3 -W ignore -m unittest discover -v -s ./tests -p "*.py"
