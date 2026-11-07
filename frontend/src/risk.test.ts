import { describe, expect, it } from 'vitest';
import { riskClass } from './risk';

describe('risk label styling', () => {
  it('maps multiword labels to stable CSS classes', () => {
    expect(riskClass('DATA LIMITED')).toBe('data-limited');
  });
  it('preserves simple severity labels', () => {
    expect(riskClass('CRITICAL')).toBe('critical');
  });
});
