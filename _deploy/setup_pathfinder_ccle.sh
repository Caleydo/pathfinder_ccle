#!/usr/bin/env bash

#search for the right parent directory such that we have a common start directory
while [[ ! -f "run.sh" ]] && [[ ! -f "Vagrantfile" ]]
do
  cd ..
done


mkdir -p _data/
cd _data


function update_file {
  echo "downloading ccle.h5 file"
  baseurl="https://googledrive.com/host/0B7lah7E3BqlAfmNnQ3ptNUhtbG1fWklkemVGc0xnZkNyZ21lUi15aFlIb3NSZ2FWOTR3NHM/"
  wget --timestamping -O ccle.h5.gz "${baseurl}/ccle.h5.gz"
  gunzip -f ccle.h5.gz
  rm -f ccle.h5.gz
}

function setup {
  if [ -f "ccle.h5" ]
  then
    echo "ccle.h5 already there"
  else
    update_file
  fi
}

function update {
  #update_file
  echo "nothing to update"
}

function uninstall {
  rm -f "ccle.h5"
}

#command switch
case "$1" in
update)
  update
  ;;
uninstall)
  uninstall
  ;;
*)
  setup
  ;;
esac