__author__ = 'Samuel Gratzl'


import tables
import numpy as np
import glob
import json

base = '/vagrant_data/ccle'

h5 = tables.open_file(base+'.h5','w')

def clean_name(name):
  return name.lower().replace(' ','').replace('-','').split('/')[-1]

for f in glob.glob(base+'/*_data.csv'):
  name = f.replace('_data.csv','')
  cleaned = clean_name(name)
  print cleaned

  group = h5.create_group('/',cleaned, name.split('/')[-1])
  #TODO handle table cases
  h5.set_node_attr(group, 'type', 'matrix')
  h5.set_node_attr(group, 'value', 'real')

  with open(name+'_cols.csv') as cc:
    l = cc.readline().split(';')
    coltype = l[1].strip()
    h5.set_node_attr(group, 'coltype', coltype)
  with open(name+'_rows.csv') as cc:
    l = cc.readline().split(';')
    rowtype = l[1].strip()
    h5.set_node_attr(group, 'rowtype', rowtype)

  cols = np.loadtxt(name+'_cols.csv', dtype=np.string_, delimiter=';', skiprows=1, usecols=(1,))
  h5.create_array(group, 'cols', cols)

  rows = np.loadtxt(name+'_rows.csv', dtype=np.string_, delimiter=';', skiprows=1, usecols=(1,))
  h5.create_array(group, 'rows', rows)

  data = np.genfromtxt(f, dtype=np.float32, delimiter=';', missing_values='NaN', filling_values=np.NaN)
  h5.create_array(group, 'data', data)

  def load_stratification(ids, idtype):
    with open(name+'_'+idtype+'.json') as fs:
      strats = json.load(fs)
      for key,value in strats.iteritems():
        s = h5.create_group('/',clean_name(key), key)
        h5.set_node_attr(s, 'type', 'stratification')
        h5.set_node_attr(s, 'idtype', idtype)
        for gg,indices in value.iteritems():
          h5.create_array(s, clean_name(gg), ids[indices], gg)
  load_stratification(cols,coltype)
  load_stratification(rows, rowtype)


  h5.flush()

h5.close()
