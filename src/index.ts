/**
 * Created by Samuel Gratzl on 08.06.2015.
 */

import {getAPIJSON} from 'phovea_core/src/ajax';
import Timer = NodeJS.Timer;


export function list() {
  return getAPIJSON('/ccle');
}

export function data(dataset: string, rowIds: string[] = [], colIds: string[] = [], method: string = 'data') {
  const param: any = {};
  if (rowIds.length > 0) {
    param.rows = rowIds;
  }
  if (colIds.length > 0) {
    param.cols = colIds;
  }
  return getAPIJSON(`/ccle/${dataset}/${method}`, param);
}

export function stats(dataset: string, rowIds: string[] = [], colIds: string[] = []) {
  return data(dataset, rowIds, colIds, 'stats');
}
export function rows(dataset: string, rowIds: string[] = []) {
  const param: any = {};
  if (rowIds.length > 0) {
    param.rows = rowIds;
  }
  return getAPIJSON(`/ccle/${dataset}/rows`, param);
}
export function cols(dataset: string, colIds: string[] = []) {
  const param: any = {};
  if (colIds.length > 0) {
    param.cols = colIds;
  }
  return getAPIJSON(`/ccle/${dataset}/cols`, param);
}
export function group(dataset: string, group?: string) {
  if (typeof group !== 'undefined') {
    return getAPIJSON(`/ccle/${dataset}/group/${group}`);
  } else {
    return getAPIJSON(`/ccle/${dataset}/group`);
  }
}


function boxplotImpl(genes?: string[], summaryOfGroups?: string) {
  const param: any = {};
  if (genes) {
    param.g = genes.join(',');
  }
  if (summaryOfGroups) {
    param.groups = summaryOfGroups;
  }
  return getAPIJSON('/ccle/boxplot', param);
}

interface IQueried {
  gene: string;
  callback(r: any): void;
}

const cache = new Map<string, {toBeQueried: IQueried[], cache: Map<string, Promise<any>>, waitTimer: number}>();

async function resolveImpl(key: string, summaryOfGroups?: string[]) {
  const t = cache.get(key);
  const promise = boxplotImpl(t.toBeQueried.map((d) => d.gene, summaryOfGroups));
  const sent = t.toBeQueried;
  sent.forEach((g) => {
    t.cache.set(g.gene, promise);
  });
  t.toBeQueried.splice(0, t.toBeQueried.length);

  const output: any = await promise;
  sent.forEach((g) => {
    g.callback(output[g.gene]);
  });
}

export function boxplot_of(gene: string, callback: (r: any) => void, summaryOfGroups?: string[]) {
  const key = summaryOfGroups ? summaryOfGroups.join('_') : '_individual';
  if (!cache.has(key)) {
    cache.set(key, {toBeQueried: [], cache: new Map<string, Promise<any>>(), waitTimer: -1});
  }
  const t = cache.get(key);
  if (t.cache.has(gene)) {
    t.cache.get(gene).then((output) => callback(output[gene]));
  } else {
    t.toBeQueried.push({gene, callback});
    if (t.waitTimer > 0) {
      clearTimeout(t.waitTimer);
      t.waitTimer = -1;
    }
    if (t.toBeQueried.length > 10) {
      resolveImpl(key, summaryOfGroups);
    } else {
      t.waitTimer = <any>setTimeout(() => {
        resolveImpl(key, summaryOfGroups);
      }, 200); //wait and collect 200 milliseconds
    }
  }
}
