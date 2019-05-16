#!/usr/bin/env bash

cd documentation
echo "Compiling to .fo"
tailf-doc fo ./solcon-documentation.xml

echo "Compiling to .pdf"
tailf-doc pdf ./solcon-documentation.fo

echo "Removing .fo"
rm ./solcon-documentation.fo
