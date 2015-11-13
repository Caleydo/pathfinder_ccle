
from flask import Flask, request, Response, abort
import tables
import numpy as np
import itertools
from caleydo_server.util import to_json, jsonify

# create the api application
app = Flask(__name__)

import caleydo_server.config
filename=caleydo_server.config.get('file','pathfinder_ccle')
print filename
h5 = tables.open_file(filename, 'r')

import memcache
mc = memcache.Client(['127.0.0.1:11211'], debug=0)

mc_prefix='ccle_'


@app.route('/')
def all():
  key = mc_prefix+'_info'
  obj = mc.get(key)
  if not obj:
    obj = all_impl()
    mc.set(key, obj)
  return Response(obj, mimetype='application/json')

def all_impl():
  r = []
  for group in h5.walk_groups('/'):
    if 'type' not in group._v_attrs:
      continue
    print group
    tt = group._v_attrs.type
    base = dict(id=group._v_name, name=group._v_title.strip(),type=tt)
    if tt == 'matrix':
      base['coltype'] = group._v_attrs.coltype.strip()
      base['rowtype'] = group._v_attrs.rowtype.strip()
    elif tt == 'stratification':
      base['idtype'] = group._v_attrs.idtype.strip()
    r.append(base)

  return to_json(r)


@app.route('/<dataset>')
def get_info(dataset):
  key = mc_prefix+dataset+'_info'
  obj = mc.get(key)
  if not obj:
    obj = get_info_impl(dataset)
    mc.set(key, obj)
  return Response(obj, mimetype='application/json')

def get_info_impl(dataset):
  if '/'+dataset not in h5:
    abort(404)

  group = h5.get_node('/'+dataset)
  if group._v_attrs.type == 'matrix':
      return to_json(name=group._v_name, title=group._v_title.strip()
                      , coltype=group._v_attrs.coltype.strip()
                      , rowtype=group._v_attrs.rowtype.strip(),
                      dim=map(int, group.data.shape))
  if group._v_attrs.type == 'stratification':
    return to_json(name=group._v_name, title=group._v_title.strip()
                      , idtype=group._v_attrs.idtype.strip(),
                      groups={name: dict(title=gf._v_title,size=len(gf)) for name,gf in group._v_children.iteritems()})

def resolve(dataset):
  rows = request.args.getlist('rows[]')
  cols = request.args.getlist('cols[]')
  rowdata = h5.get_node('/' + dataset + '/rows')
  if len(rows) > 0:
    rowids = np.nonzero(np.in1d(rowdata, rows))[0]
    rowdata = rowdata[rowids]
  else:
    rowids = Ellipsis
  coldata = h5.get_node('/' + dataset + '/cols')
  if len(cols) > 0:
    colids = np.nonzero(np.in1d(coldata, cols))[0]
    coldata = coldata[colids]
  else:
    colids = Ellipsis
  data = h5.get_node('/' + dataset + '/data')
  mini = data[rowids, colids]
  return mini,rowdata,coldata

@app.route('/<dataset>/data', methods=['GET','POST'])
def get_data(dataset):
  key = mc_prefix+dataset+'_data'
  obj = mc.get(key)
  if not obj:
    obj = get_data_impl(dataset)
    mc.set(key, obj)
  return Response(obj, mimetype='application/json')

def get_data_impl(dataset):
  if '/'+dataset not in h5:
    abort(404)
  mini,rows,cols = resolve(dataset)
  return to_json(dict(data=mini,cols=cols,rows=rows))

@app.route('/<dataset>/stats', methods=['GET','POST'])
def get_stats(dataset):
  axis = request.args.get('axis',None)
  key = mc_prefix+dataset+'_stats'+(axis if axis is not None else '')
  obj = mc.get(key)
  if not obj:
    obj = get_stats_impl(dataset, axis)
    mc.set(key, obj)
  return Response(obj, mimetype='application/json')

def get_stats_impl(dataset, axis):
  mini,rows,cols = resolve(dataset)
  if axis == 'rows':
    axis = 1
  elif axis == 'cols':
    axis = 0
  amin = np.nanmin(mini, axis=axis)
  amax = np.nanmax(mini, axis=axis)
  amedian = np.median(mini, axis=axis)
  amean = np.nanmean(mini, axis=axis)
  astd = np.nanstd(mini, axis=axis)
  if axis is None:
    return to_json(dict(min=float(amin),max=float(amax),median=float(amedian),mean=float(amean),std=float(astd)))
  elif axis == 1:
    r = dict()
    for i,row in enumerate(rows):
      r[row] = dict(dict(min=float(amin[i]),max=float(amax[i]),median=float(amedian[i]),mean=float(amean[i]),std=float(astd[i])))
    return to_json(**r)
  elif axis == 0:
    r = dict()
    for i,row in enumerate(cols):
      r[row] = dict(dict(min=float(amin[i]),max=float(amax[i]),median=float(amedian[i]),mean=float(amean[i]),std=float(astd[i])))
    return to_json(**r)


@app.route('/<dataset>/rows', methods=['GET','POST'])
def get_rows(dataset):
  rows = request.args.getlist('rows[]')
  key = mc_prefix+dataset+'_rows_'+','.join(rows)
  obj = mc.get(key)
  if not obj:
    obj = get_rows_impl(dataset, rows)
    mc.set(key, obj)
  return Response(obj, mimetype='application/json')

def get_rows_impl(dataset, rows):
  if '/'+dataset not in h5:
    abort(404)
  if len(rows) > 0:
    rowids = np.nonzero(np.in1d(h5.get_node('/' + dataset + '/rows'), rows))[0]
  else:
    rowids = Ellipsis
  data = h5.get_node('/' + dataset + '/rows')
  return to_json(data[rowids])

@app.route('/<dataset>/cols', methods=['GET','POST'])
def get_cols(dataset):
  rows = request.args.getlist('cols[]')
  key = mc_prefix+dataset+'_cols_'+','.join(rows)
  obj = mc.get(key)
  if not obj:
    obj = get_cols_impl(dataset, rows)
    mc.set(key, obj)
  return Response(obj, mimetype='application/json')

def get_cols_impl(dataset, rows):
  if '/'+dataset not in h5:
    abort(404)
  if len(rows) > 0:
    rowids = np.nonzero(np.in1d(h5.get_node('/' + dataset + '/cols'), rows))[0]
  else:
    rowids = Ellipsis
  data = h5.get_node('/' + dataset + '/cols')
  return to_json(data[rowids])

@app.route('/<dataset>/group')
def get_groups(dataset):
  key = mc_prefix+dataset+'_groups'
  obj = mc.get(key)
  if not obj:
    obj = get_groups_impl(dataset)
    mc.set(key, obj)
  return Response(obj, mimetype='application/json')

def get_groups_impl(dataset):
  if '/'+dataset not in h5:
    abort(404)
  g = h5.get_node('/'+dataset)
  r = {name: dict(title=gf._v_title,ids=gf) for name,gf in g._v_children.iteritems()}
  return to_json(r)

def boxplot_impl(d):
  d = np.array(d)

  h = np.percentile(d, [25, 75])
  lower_iqr = h[0] - (h[1] - h[0]) * 1.5
  upper_iqr = h[1] + (h[1] - h[0]) * 1.5

  r = dict(
    min=np.nanmin(d),
    max=np.nanmax(d),
    nans=np.isnan(d).sum(),
    median=np.median(d),
    mean=np.nanmean(d),
    std=np.nanstd(d),
    quartile25=h[0],
    quartile75=h[1],
    iqrMin=np.nan,
    iqrMax=np.nan,
    numElements=d.size)
  d = d.flat
  candidates = d[np.logical_and(lower_iqr <= d, d <= h[0])]
  if len(candidates) > 0:
    r['iqrMin'] = candidates[0]
  candidates = d[np.logical_and(h[1] <= d, d <= upper_iqr)]
  if len(candidates) > 0:
    r['iqrMax'] = candidates[-1]

  return r

cache = dict()

def to_datasetid(dataset, k, cols, genes):
  global cache
  key = dataset+'_'+k
  if key in cache:
    return cache[key]
  r = np.nonzero(np.in1d(cols, genes))[0]
  cache[key] = r
  return r

@app.route('/boxplot',methods=['GET','POST'])
def boxplot():
  """
  boxplot data for a specific case
  :return:
  """
  strat = request.args.get('stratification','compoundcelleffect_siteprimary')
  datasets = request.args.getlist('datasets[]')
  if len(datasets) == 0:
    datasets = ['copynumbervariation','mrnaexpression']
  summary = request.args.getlist('groups[]')
  if len(summary) == 0:
    summary = None
  genes = request.args['g'].split(',') if 'g' in request.args else None

  obj = boxplot_api(genes, summary, strat, datasets)
  return Response(obj, mimetype='application/json')

def boxplot_api(genes, summary=None, strat='compoundcelleffect_siteprimary', datasets=['copynumbervariation','mrnaexpression']):
  key = mc_prefix+'boxplot@'+to_json(dict(strat=strat,datsets=datasets,summary=summary,genes=genes)).replace(' ','_')

  obj = mc.get(key)
  if obj:
    return obj

  strat = h5.get_node('/'+strat)
  groups = {name: gf for name,gf in strat._v_children.iteritems()}

  if summary is not None: #create a summary
    s = set()
    for k,v in groups.iteritems():
      if k in summary or '_all' in summary:
        s = s.union(v)
    groups = dict()
    groups['_'.join(summary)] = np.array(list(s))


  all_genes = genes is None
  import collections
  r = collections.defaultdict(dict)
  for dataset in datasets:
    d = h5.get_node('/'+dataset+'/data')
    if all_genes:
      rowdata = ['summary']
      rowids = [Ellipsis]
    else:
      rowdata = h5.get_node('/' + dataset + '/rows')
      rowids = np.nonzero(np.in1d(rowdata, genes))[0]
      rowdata = rowdata[rowids]

    coldata = h5.get_node('/' + dataset + '/cols')
    dgroups = { k : to_datasetid(dataset, k, coldata, v) for k,v in groups.iteritems()}

    for gene, row in itertools.izip(rowdata,rowids):
      data = d[row,]
      container = dict()
      r[gene][dataset] = container
      for group, groupids in dgroups.iteritems():
        #print data.shape, groupids, group
        dg = data[...,groupids]
        stats = boxplot_impl(dg)
        container[group] =  dict(stats=stats,data=dg)

  obj = to_json(r)
  mc.set(key, obj)
  return obj


def boxplot_api2(gene, strat='compoundcelleffect_siteprimary', datasets=['copynumbervariation','mrnaexpression']):
  strat = h5.get_node('/'+strat)
  groups = {name: gf for name,gf in strat._v_children.iteritems()}

  s = set()
  for k,v in groups.iteritems():
    s = s.union(v)
  groups['_all'] = np.array(list(s))


  import collections
  r = collections.defaultdict(dict)
  for dataset in datasets:
    d = h5.get_node('/'+dataset+'/data')
    rowdata = h5.get_node('/' + dataset + '/rows')
    row = np.nonzero(np.in1d(rowdata, [gene]))[0]

    if len(row) == 0:
      return dict()
    row = row[0]

    coldata = h5.get_node('/' + dataset + '/cols')
    dgroups = { k : to_datasetid(dataset, k, coldata, v) for k,v in groups.iteritems()}

    data = d[row,]
    container = dict()
    r[dataset] = container
    for group, groupids in dgroups.iteritems():
      #print data.shape, groupids, group
      dg = data[...,groupids]
      stats = boxplot_impl(dg)
      container[group] =  dict(stats=stats,data=dg)

  return r


@app.route('/<dataset>/group/<group>')
def get_group(dataset, group):
  if '/'+dataset+'/'+group not in h5:
    abort(404)
  g = h5.get_node('/'+dataset+'/'+group)
  return jsonify(g)

def create():
  return app

if __name__ == '__main__':
  app.debug = True
  app.run(host='0.0.0.0', port=9000)
