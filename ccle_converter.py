__author__ = 'Samuel Gratzl'


import tables
import numpy as np
import glob
import json
import os

base = '/vagrant_data/tcga_sampled'

h5 = tables.open_file(base+'.h5','w')

def clean_name(name):
  n = name.lower().replace(' ','').replace('-','').replace('(','_').replace(')','').split('/')[-1]
  if n[0].isdigit():
    n = '_' + n
  return n

for f in glob.glob(base+'/*_data.csv'):
  name = f.replace('_data.csv','')
  cleaned = clean_name(name)
  print cleaned

  group = h5.create_group('/',cleaned, name.split('/')[-1])

  def load_stratification(ids, idtype):
    if not os.path.exists(name+'_'+idtype+'.json'):
      return
    with open(name+'_'+idtype+'.json') as fs:
      strats = json.load(fs)
      for key,value in strats.iteritems():
        s = h5.create_group('/',clean_name(cleaned+'_'+key), key)
        h5.set_node_attr(s, 'type', 'stratification')
        h5.set_node_attr(s, 'idtype', idtype)
        for gg,indices in value.iteritems():
          h5.create_array(s, clean_name(gg), ids[indices], gg)


  with open(name+'_rows.csv','r') as cc:
    l = cc.readline().split(';')
    rowtype = l[1].strip()
    h5.set_node_attr(group, 'rowtype', rowtype)

  rows = np.loadtxt(name+'_rows.csv', dtype=np.string_, delimiter=';', skiprows=1, usecols=(1,))
  h5.create_array(group, 'rows', rows)
  load_stratification(rows, rowtype)

  if os.path.exists(name+'_cols.csv'): #matrix case
    h5.set_node_attr(group, 'type', 'matrix')
    h5.set_node_attr(group, 'value', 'real')

    with open(name+'_cols.csv','r') as cc:
      l = cc.readline().split(';')
      coltype = l[1].strip()
      h5.set_node_attr(group, 'coltype', coltype)

    cols = np.loadtxt(name+'_cols.csv', dtype=np.string_, delimiter=';', skiprows=1, usecols=(1,))
    h5.create_array(group, 'cols', cols)

    data = np.genfromtxt(f, dtype=np.float32, delimiter=';', missing_values='NaN', filling_values=np.NaN)
    h5.create_array(group, 'data', data)
    load_stratification(cols,coltype)

  if os.path.exists(name+'_desc.csv'): #table case
    h5.set_node_attr(group, 'type', 'table')
    import csv
    with open(name+'_desc.csv','r') as cc:
      desc = dict()
      lookup = dict(uint8=tables.UInt8Col,uint16=tables.UInt16Col,uint32=tables.UInt32Col,
                    int8=tables.UInt8Col,int16=tables.Int16Col,int32=tables.Int32Col,
                    float16=tables.Float16Col,float32=tables.Float32Col,float64=tables.Float64Col,
                    bool=tables.BoolCol)
      columns = []
      mapper = []
      for row in csv.reader(cc,delimiter=';'):
        t = None
        pos = int(row[0])
        if row[2] == 'string':
          t = tables.StringCol(int(row[3]),pos=pos)
          t2 = 'string'+row[3]
          m = str
        elif row[2] == 'enum':
          keys = row[3:]
          keys.append('NA')
          print keys
          enum_ = tables.misc.enum.Enum(keys)
          t2 = 'enum:'+':'.join(keys)
          t = tables.EnumCol(enum_, 'NA', base='uint8',pos=pos)
          def wrap(e): #wrap in a function for the right scope
            return lambda x: e[x]
          m = wrap(enum_)
        else:
          t2 = row[2]
          t = lookup[t2](pos=pos)
          if t2[0] == 'f':
            m = lambda x : np.NaN if x == 'NA' or x == '' else float(x)
          else:
            m = lambda x : -1 if x == 'NA' or x == '' else int(x)
        desc[clean_name(row[1])] = t
        columns.append(dict(key=clean_name(row[1]),name=row[1],type=t2))
        mapper.append(m)
    h5.set_node_attr(group,'columns',columns)

    table = h5.create_table(group,'table',desc)
    with open(name+'_data.csv','r') as d:
      entry = table.row
      for row in csv.reader(d,delimiter=';'):
        for col,m,v in zip(columns,mapper,row):
          entry[col['key']] = m(v)
        entry.append()

  h5.flush()

h5.close()
