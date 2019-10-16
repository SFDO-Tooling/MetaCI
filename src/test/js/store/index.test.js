import reducer from 'store';

describe('reducer', () => {
  test('combines child reducers', () => {
    const actual = reducer(undefined, {});

    expect(Object.keys(actual)).toEqual(['perfData', 'perfDataUI']);
  });
});
