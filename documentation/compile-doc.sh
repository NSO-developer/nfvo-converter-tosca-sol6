#!/usr/bin/env bash

cd documentation
echo "Compiling to .fo"
tailf-doc --cisco fo ./solcon-documentation.xml

echo "Compiling to .pdf"
tailf-doc --cisco pdf ./solcon-documentation.fo

echo "Removing .fo"
rm ./solcon-documentation.fo
