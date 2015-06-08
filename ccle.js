/**
 * Created by Samuel Gratzl on 08.06.2015.
 */

define(['exports', '../caleydo/main'], function (exports, C) {
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
  }
});