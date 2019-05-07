import React from 'react';
import { render } from 'react-testing-library';

import ErrorBoundary, { AuthError } from 'components/error';

class TestableErrorBoundary extends ErrorBoundary {
  constructor(props) {
    super(props);
    this.state = { hasError: true };
  }
}

describe('<ErrorBoundary />', () => {
  test('renders children', () => {
    const { getByText } = render(
      <ErrorBoundary>
        <div>child</div>
      </ErrorBoundary>,
    );

    expect(getByText('child')).toBeVisible();
  });

  test('renders error msg if errors', () => {
    const { getByText, queryByText } = render(
      <TestableErrorBoundary>
        <div>child</div>
      </TestableErrorBoundary>,
    );

    expect(queryByText('child')).toBeNull();
    expect(getByText('Yikes!', { exact: false })).toBeVisible();
  });
});

describe('<AuthError />', () => {
  test('authentication error component', () => {
    const { getByText } = render(<AuthError message={'This is the error'} />);
    expect(getByText('This is the error')).toBeVisible();
  });
});
