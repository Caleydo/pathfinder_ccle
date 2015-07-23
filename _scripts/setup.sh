#!/usr/bin/env bash

#search for the right parent directory
while [ ! -f "Vagrantfile" ]
do
  cd ..
done

mkdir -p _data/
cd _data

if [ -f "ccle.h5" ]
then
  echo "ccle.h5 already there"
else
  echo "downloading ccle.h5 file"
  #TODO wrong link
  wget -O ccle.h5.gz "https://googledrive.com/host/0B7lah7E3BqlAfmNnQ3ptNUhtbG1fWklkemVGc0xnZkNyZ21lUi15aFlIb3NSZ2FWOTR3NHM/ccle.h5.gz"
  gunzip ccle.h5.gz
  rm ccle.h5.gz
fi
