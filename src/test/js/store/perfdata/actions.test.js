import fetchMock from 'fetch-mock';

import { assertUIData } from '@/api/testmethod_perf_UI_JSON_schema';
import { assertPerfData } from '@/api/testmethod_perfdata_JSON_schema';
import * as actions from '@/store/perfdata/actions';

import testmethod_perf_data from '../../api/testmethod_perf.json';
import testmethod_perf_UI_data from '../../api/testmethod_perf_UI.json';
import { storeWithApi } from './../../utils';

describe('perfRESTFetch', () => {
  const url = actions.testmethod_perfdata_url;
  test('Downloads data', () => {
    const store = storeWithApi({});
    fetchMock.getOnce(
      `begin:${actions.testmethod_perfdata_url}`,
      testmethod_perf_data,
    );
    expect.assertions(1);
    return store.dispatch(actions.perfRESTFetch(url)).then(() => {
      const action_list = store.getActions().map((a) => a.type);
      expect(action_list).toEqual(['PERF_DATA_LOADING', 'PERF_DATA_AVAILABLE']);
      assertPerfData(store.getActions()[1].payload);
    });
  });
  test('Freaks out if server returns wrong shaped data', () => {
    const store = storeWithApi({});
    fetchMock.getOnce(`begin:${actions.testmethod_perfdata_url}`, {});
    expect.assertions(1);
    return store.dispatch(actions.perfRESTFetch(url)).catch((reason) => {
      expect(reason).toHaveProperty('message');
    });
  });

  test('Freaks out if server returns nothing', () => {
    const store = storeWithApi({});
    fetchMock.getOnce(`begin:${actions.testmethod_perfdata_url}`, 200);
    expect.assertions(1);
    return store.dispatch(actions.perfRESTFetch(url)).catch((reason) => {
      expect(reason).toHaveProperty('message');
    });
  });

  test('Freaks out if server returns Server error', () => {
    const store = storeWithApi({});
    fetchMock.getOnce(`begin:${actions.testmethod_perfdata_url}`, 500);
    expect.assertions(1);
    return store.dispatch(actions.perfRESTFetch(url)).catch((reason) => {
      expect(reason).toHaveProperty('message');
    });
  });
  test('Freaks out if server returns werd HTTP error', () => {
    const store = storeWithApi({});
    fetchMock.getOnce(`begin:${actions.testmethod_perfdata_url}`, 100);
    expect.assertions(1);
    return store.dispatch(actions.perfRESTFetch(url)).catch((reason) => {
      expect(reason).toHaveProperty('message');
    });
  });
  test('Freaks out if there are networking problems', () => {
    const store = storeWithApi({});
    fetchMock.getOnce(`begin:${actions.testmethod_perfdata_url}`, () => {
      throw new Error('my error');
    });
    expect.assertions(1);
    return store.dispatch(actions.perfRESTFetch(url)).catch((reason) => {
      expect(reason).toHaveProperty('message');
    });
  });

  test('Freaks out if server returns JSON error', () => {
    const store = storeWithApi({});
    fetchMock.getOnce(`begin:${actions.testmethod_perfdata_url}`, {
      error: 'oops',
    });
    expect.assertions(1);
    return store.dispatch(actions.perfRESTFetch(url)).catch((reason) => {
      expect(reason).toHaveProperty('message');
    });
  });
});

describe('perfRESTFetch_UI', () => {
  test('Downloads UI data', () => {
    const store = storeWithApi({});
    fetchMock.getOnce(
      `begin:${actions.testmethod_perf_UI_url}`,
      testmethod_perf_UI_data,
    );
    expect.assertions(1);
    return store.dispatch(actions.perfREST_UI_Fetch()).then(() => {
      const action_list = store.getActions().map((a) => a.type);
      expect(action_list).toEqual(['UI_DATA_LOADING', 'UI_DATA_AVAILABLE']);
      assertUIData(store.getActions()[1].payload);
    });
  });
});
