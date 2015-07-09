/**
 * Created by Samuel Gratzl on 08.06.2015.
 */

define(['exports', '../caleydo_web/main'], function (exports, C) {
  exports.list = function () {
    return C.getAPIJSON('/ccle');
  };
  exports.data = function (dataset, row_ids, col_ids, method) {
    row_ids = row_ids || [];
    col_ids = col_ids || [];
    method = method || 'data';
    var param = {};
    if (row_ids.length > 0) {
      param['rows'] = row_ids;
    }
    if (col_ids.length > 0) {
      param['cols'] = col_ids;
    }
    return C.getAPIJSON('/ccle/' + dataset + '/'+method, param);
  };
  exports.stats = function(dataset, row_ids, col_ids) {
    return exports.data(dataset, row_ids, col_ids, 'stats');
  };
  exports.rows = function (dataset, row_ids) {
    row_ids = row_ids || [];
    var param = {};
    if (row_ids.length > 0) {
      param['rows'] = row_ids;
    }
    return C.getAPIJSON('/ccle/' + dataset + '/rows', param);
  };
  exports.cols = function (dataset, col_ids) {
    col_ids = col_ids || [];
    var param = {};
    if (row_ids.length > 0) {
      param['cols'] = col_ids;
    }
    return C.getAPIJSON('/ccle/' + dataset + '/cols', param);
  };
  exports.group = function (dataset, group) {
    if (typeof group !== 'undefined') {
      return C.getAPIJSON('/ccle/' + dataset + '/group/'+group);
    } else {
      return C.getAPIJSON('/ccle/' + dataset + '/group');
    }
  };


  function boxplotImpl(genes, summaryOfGroups) {
    genes = genes || null;
    summaryOfGroups = summaryOfGroups || null;
    var param = {};
    if (genes) {
      param['g'] = genes.join(',');
    }
    if (summaryOfGroups) {
      param['groups'] = summaryOfGroups
    }
    return C.getAPIJSON('/ccle/boxplot', param);
  }

  var cache = {};

  function resolveImpl(key, summaryOfGroups) {
    var t = cache[key];
    var promise = boxplotImpl(t.to_be_queried.map(function(d) { return d.gene; }), summaryOfGroups);
    var sent = t.to_be_queried;
    sent.forEach(function(g) {
      t.cache[g.gene] = promise;
    });
    promise.then(function(output) {
      sent.forEach(function(g) {
        g.callback(output[g.gene]);
      });
    });
    t.to_be_queried = [];
  }
  exports.boxplot_of = function(gene, callback, summaryOfGroups) {
    var key = summaryOfGroups ? summaryOfGroups.join('_') : '_individual';
    var t;
    if (key in cache) {
      t = cache[key]
    } else {
      t = { to_be_queried : [], cache : {}, wait_timer : -1};
      cache[key] = t
    }
    if (gene in t.cache) {
      t.cache[gene].then(function(output) {
        callback(output[gene]);
      });
    } else {
      t.to_be_queried.push({ gene: gene, callback: callback});
      if (t.wait_timer > 0) {
        clearTimeout(t.wait_timer);
        t.wait_timer = -1;
      }
      if (t.to_be_queried.length > 10) {
        resolveImpl(key, summaryOfGroups)
      } else {
        t.wait_timer = setTimeout(function() {
          resolveImpl(key, summaryOfGroups)
        }, 200); //wait and collect 200 milliseconds
      }
    }
  };
});