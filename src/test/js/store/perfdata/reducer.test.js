import { perfDataReducer, perfDataUIReducer } from '@/store/perfdata/reducer';

describe('PerfDataReducer', () => {
  test('Should initialize to loading state', () => {
    const store = perfDataReducer(undefined, { type: 'xyzzy' });
    expect(store).toHaveProperty('status');
    expect(store.status).toEqual('LOADING');
  });
  test('Should accept PERF_DATA_LOADING action', () => {
    let store = perfDataReducer(undefined, { type: 'xyzzy' });
    store = perfDataReducer(store, {
      type: 'PERF_DATA_LOADING',
      payload: { url: 'zombo.com' },
    });
    expect(store.status).toEqual('LOADING');
    expect(store.url).toEqual('zombo.com');
  });
  test('Should remember perfdata while loading', () => {
    let store = perfDataReducer(undefined, { type: 'xyzzy' });
    store = perfDataReducer(store, {
      type: 'PERF_DATA_LOADING',
      payload: { url: 'zombo.com' },
    });
    store = perfDataReducer(store, {
      type: 'PERF_DATA_AVAILABLE',
      payload: 'dummy perfdata',
    });
    expect(store.status).toEqual('AVAILABLE');
    expect(store.url).toEqual('zombo.com');
    expect(store.perfdata).toEqual('dummy perfdata');
    store = perfDataReducer(store, {
      type: 'PERF_DATA_LOADING',
      payload: { url: 'html5zombo.com' },
    });
    expect(store.status).toEqual('LOADING');
    expect(store.url).toEqual('html5zombo.com');
    expect(store.perfdata).toEqual('dummy perfdata');
  });
  test('Should remember URL after error and clear errors', () => {
    let store = perfDataReducer(undefined, { type: 'xyzzy' });
    store = perfDataReducer(store, {
      type: 'PERF_DATA_LOADING',
      payload: { url: 'zombo.com' },
    });
    store = perfDataReducer(store, {
      type: 'PERF_DATA_ERROR',
      payload: 'dummy error',
    });
    expect(store.status).toEqual('ERROR');
    expect(store.url).toEqual('zombo.com');
    expect(store.reason).toEqual('dummy error');
    store = perfDataReducer(store, {
      type: 'PERF_DATA_LOADING',
      payload: { url: 'html5zombo.com' },
    });
    expect(store.status).toEqual('LOADING');
    expect(store.url).toEqual('html5zombo.com');
    expect(store).not.toHaveProperty('reason');
  });
});

describe('perfDataUIReducer', () => {
  test('Should initialize to loading state', () => {
    const store = perfDataUIReducer(undefined, { type: 'xyzzy' });
    expect(store).toHaveProperty('status');
    expect(store.status).toEqual('LOADING');
  });
  test('Should accept UI_DATA_LOADING action', () => {
    let store = perfDataUIReducer(undefined, { type: 'xyzzy' });
    store = perfDataUIReducer(store, {
      type: 'UI_DATA_LOADING',
      payload: { url: 'zombo.com' },
    });
    expect(store.status).toEqual('LOADING');
    expect(store.url).toEqual('zombo.com');
  });
  test('Should remember perfdata while loading', () => {
    let store = perfDataUIReducer(undefined, { type: 'xyzzy' });
    store = perfDataUIReducer(store, {
      type: 'UI_DATA_LOADING',
      payload: { url: 'zombo.com' },
    });
    store = perfDataUIReducer(store, {
      type: 'UI_DATA_AVAILABLE',
      payload: 'dummy perfdata',
    });
    expect(store.status).toEqual('AVAILABLE');
    expect(store.url).toEqual('zombo.com');
    expect(store.uidata).toEqual('dummy perfdata');
    store = perfDataUIReducer(store, {
      type: 'UI_DATA_LOADING',
      payload: { url: 'html5zombo.com' },
    });
    expect(store.status).toEqual('LOADING');
    expect(store.url).toEqual('html5zombo.com');
    expect(store.uidata).toEqual('dummy perfdata');
  });
  test('Should remember URL after error and clear errors', () => {
    let store = perfDataUIReducer(undefined, { type: 'xyzzy' });
    store = perfDataUIReducer(store, {
      type: 'UI_DATA_LOADING',
      payload: { url: 'zombo.com' },
    });
    store = perfDataUIReducer(store, {
      type: 'UI_DATA_ERROR',
      payload: 'dummy error',
    });
    expect(store.status).toEqual('ERROR');
    expect(store.url).toEqual('zombo.com');
    expect(store.reason).toEqual('dummy error');
    store = perfDataUIReducer(store, {
      type: 'UI_DATA_LOADING',
      payload: { url: 'html5zombo.com' },
    });
    expect(store.status).toEqual('LOADING');
    expect(store.url).toEqual('html5zombo.com');
    expect(store).not.toHaveProperty('reason');
  });
});
