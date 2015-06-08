__author__ = 'Samuel Gratzl'


import tables
import numpy as np
import glob
import csv

h5 = tables.open_file('/vagrant_data/ccle.h5','w')


for f in glob.glob('/vagrant_data/ccle/*_data.csv'):
  name = f.replace('_data.csv','')
  cleaned = name.lower().replace(' ','').replace('-','').split('/')[-1]
  print cleaned

  group = h5.create_group('/',cleaned, name)
  #TODO handle table cases
  h5.set_node_attr(group, 'type', 'matrix')
  h5.set_node_attr(group, 'value', 'real')

  with open(name+'_cols.csv') as cc:
    l = cc.readline().split(';')
    h5.set_node_attr(group, 'coltype', l[1].strip())
  with open(name+'_rows.csv') as cc:
    l = cc.readline().split(';')
    h5.set_node_attr(group, 'rowtype', l[1].strip())

  cols = np.loadtxt(name+'_cols.csv', dtype=np.string_, delimiter=';', skiprows=1, usecols=(1,))
  h5.create_array(group, 'cols', cols)

  rows = np.loadtxt(name+'_rows.csv', dtype=np.string_, delimiter=';', skiprows=1, usecols=(1,))
  h5.create_array(group, 'rows', rows)

  data = np.genfromtxt(f, dtype=np.float32, delimiter=';', missing_values='NaN', filling_values=np.NaN)
  h5.create_array(group, 'data', data)
  h5.flush()

h5.close()
