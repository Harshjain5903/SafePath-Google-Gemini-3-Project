import { render, screen } from '@testing-library/react';
import LocationSearch from '../LocationSearch';

const noop = () => {};

describe('LocationSearch', () => {
  it('shows coordinates for an externally set value', () => {
    render(<LocationSearch placeholder="Origin" value={[41.88257, -87.62259]} onSelect={noop} onClear={noop} />);
    expect(screen.getByPlaceholderText('Origin')).toHaveValue('41.8826, -87.6226');
  });

  it('updates when the value changes and clears when it is removed', () => {
    const { rerender } = render(<LocationSearch placeholder="Origin" value={null} onSelect={noop} onClear={noop} />);
    const input = screen.getByPlaceholderText('Origin');
    expect(input).toHaveValue('');

    rerender(<LocationSearch placeholder="Origin" value={[41.89186, -87.60501]} onSelect={noop} onClear={noop} />);
    expect(input).toHaveValue('41.8919, -87.6050');

    rerender(<LocationSearch placeholder="Origin" value={null} onSelect={noop} onClear={noop} />);
    expect(input).toHaveValue('');
  });
});
