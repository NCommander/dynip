#!/bin/bash
sudo PYHTONPATH=`pwd` python3 -m unittest discover -v -s ./tests -p "*.py"
