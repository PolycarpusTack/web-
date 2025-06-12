import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { Button } from '../button';
import { testAccessibility, testAriaAttributes } from '@/test-utils/accessibility';

describe('Button Accessibility', () => {
  it('should have no accessibility violations', async () => {
    const { container } = render(
      <div>
        <Button>Click me</Button>
        <Button variant="secondary">Secondary</Button>
        <Button variant="destructive">Delete</Button>
        <Button disabled>Disabled</Button>
      </div>
    );
    
    await testAccessibility(container);
  });

  it('should be keyboard accessible', async () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    const button = screen.getByRole('button', { name: /click me/i });
    
    // Focus button with Tab
    await userEvent.tab();
    expect(button).toHaveFocus();
    
    // Activate with Enter
    await userEvent.keyboard('{Enter}');
    expect(handleClick).toHaveBeenCalledTimes(1);
    
    // Activate with Space
    await userEvent.keyboard(' ');
    expect(handleClick).toHaveBeenCalledTimes(2);
  });

  it('should have proper ARIA attributes when disabled', () => {
    render(<Button disabled>Disabled Button</Button>);
    
    const button = screen.getByRole('button', { name: /disabled button/i });
    testAriaAttributes(button, {
      'aria-disabled': 'true'
    });
  });

  it('should support aria-label', () => {
    render(
      <Button aria-label="Save document">
        <span aria-hidden="true">💾</span>
      </Button>
    );
    
    const button = screen.getByRole('button', { name: /save document/i });
    expect(button).toBeInTheDocument();
  });

  it('should have visible focus indicator', async () => {
    render(<Button>Focus me</Button>);
    
    const button = screen.getByRole('button', { name: /focus me/i });
    
    // Focus the button
    await userEvent.tab();
    expect(button).toHaveFocus();
    
    // Check if focus styles are applied (checking for focus-visible class)
    expect(button).toHaveClass('focus-visible:ring-2');
  });

  it('should announce loading state to screen readers', () => {
    const { rerender } = render(<Button>Submit</Button>);
    
    rerender(<Button disabled aria-busy="true">
      <span className="sr-only">Loading</span>
      <span aria-hidden="true">⌛</span>
      Submit
    </Button>);
    
    const button = screen.getByRole('button', { name: /loading submit/i });
    expect(button).toHaveAttribute('aria-busy', 'true');
    expect(button).toHaveAttribute('aria-disabled', 'true');
  });

  it('should maintain focus when content changes', async () => {
    const { rerender } = render(<Button>Original</Button>);
    
    const button = screen.getByRole('button');
    await userEvent.tab();
    expect(button).toHaveFocus();
    
    // Change button content
    rerender(<Button>Updated</Button>);
    
    // Focus should remain on button
    expect(screen.getByRole('button')).toHaveFocus();
  });
});