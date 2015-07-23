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
  wget -O ccle.h5.gz https://drive.google.com/uc?export=download&id=0B7lah7E3BqlAZ1ZsOVhtZ3M2TXc
  gunzip ccle.h5.gz
  rm ccle.h5.gz
fi
