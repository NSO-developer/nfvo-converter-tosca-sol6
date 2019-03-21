#!/usr/bin/env bash

# Check for python3
if hash python3 2>/dev/null; then
    echo "python3 found"
else
    echo "python3 not found, please install from python.org"
    exit
fi

# Check for pip3
if hash pip3 2>/dev/null; then
    echo "Pip3 found"
else
    echo "Pip3 not found, please update your python3"
    exit
fi

echo "Installing TOML"
pip3 install toml --user

echo "Installing PyYaml"
pip3 install pyyaml --user
