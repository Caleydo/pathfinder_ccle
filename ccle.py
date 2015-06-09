
from flask import Flask, request, jsonify, Response
import tables
import numpy as np
import json

# create the api application
app = Flask(__name__)


class NumpyAwareJSONEncoder(json.JSONEncoder):
  """
  helper class for converting a numpy array to json,

  see http://stackoverflow.com/questions/3488934/simplejson-and-numpy-array
  """

  def default(self, obj):
    if isinstance(obj, np.ndarray) or isinstance(obj, tables.Array):
      if obj.ndim == 1:
        return [x for x in obj]
      else:
        return [self.default(obj[i]) for i in range(obj.shape[0])]
    if isinstance(obj, np.generic):
      a = np.asscalar(obj)
      if isinstance(a, float) and np.isnan(a):
        return None
      return a
    return super(NumpyAwareJSONEncoder, self).default(obj)

h5 = tables.open_file('/vagrant_data/ccle.h5', 'r')

@app.route('/')
def all():
  r = []
  for group in h5.walk_groups('/'):
    print group
    try:
      if group._v_attrs.type == 'matrix':
        r.append(dict(name=group._v_name, title=group._v_title.strip()
                      , coltype=group._v_attrs.coltype.strip()
                      , rowtype=group._v_attrs.rowtype.strip()))
    except AttributeError, e:
      print e
  return json.dumps(r)


def filter_ids(to_include, arr):
  return

@app.route('/<dataset>')
def get_info(dataset):
  group = h5.get_node('/'+dataset)
  return jsonify(name=group._v_name, title=group._v_title.strip()
                      , coltype=group._v_attrs.coltype.strip()
                      , rowtype=group._v_attrs.rowtype.strip(),
                      dim=map(int, group.data.shape))

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

@app.route('/<dataset>/data')
def get_data(dataset):
  mini,rows,cols = resolve(dataset)
  t = json.dumps(dict(data=mini,cols=cols,rows=rows),cls=NumpyAwareJSONEncoder)
  return Response(t, mimetype='application/json')

@app.route('/<dataset>/stats')
def get_stats(dataset):
  mini,rows,cols = resolve(dataset)
  axis = request.args.get('axis',None)
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
    return jsonify(min=float(amin),max=float(amax),median=float(amedian),mean=float(amean),std=float(astd))
  elif axis == 1:
    r = dict()
    for i,row in enumerate(rows):
      r[row] = dict(min=float(amin[i]),max=float(amax[i]),median=float(amedian[i]),mean=float(amean[i]),std=float(astd[i]))
    return jsonify(**r)
  elif axis == 0:
    r = dict()
    for i,row in enumerate(cols):
      r[row] = dict(min=float(amin[i]),max=float(amax[i]),median=float(amedian[i]),mean=float(amean[i]),std=float(astd[i]))
    return jsonify(**r)


@app.route('/<dataset>/rows')
def get_rows(dataset):
  rows = request.args.getlist('rows[]')
  if len(rows) > 0:
    rowids = filter_ids(rows, h5.get_node('/' + dataset + '/rows'))
  else:
    rowids = Ellipsis
  data = h5.get_node('/' + dataset + '/rows')
  return json.dumps(data[rowids].tolist())


@app.route('/<dataset>/cols')
def get_cols(dataset):
  rows = request.args.getlist('cols[]')
  if len(rows) > 0:
    rowids = filter_ids(rows, h5.get_node('/' + dataset + '/cols'))
  else:
    rowids = Ellipsis
  data = h5.get_node('/' + dataset + '/cols')
  return json.dumps(data[rowids].tolist())


def create(*args, **kwargs):
  return app


if __name__ == '__main__':
  app.debug = True
  app.run(host='0.0.0.0', port=9000)
