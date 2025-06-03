import { axe, toHaveNoViolations } from 'jest-axe';
import { RenderResult } from '@testing-library/react';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

/**
 * Run accessibility tests on a component
 * @param container - The container element from render result
 * @param options - Optional axe configuration
 */
export async function testAccessibility(
  container: RenderResult['container'],
  options?: any
) {
  const results = await axe(container, options);
  expect(results).toHaveNoViolations();
}

/**
 * Test keyboard navigation for a component
 * @param element - The element to test
 * @param expectedOrder - Array of expected element labels/text in tab order
 */
export async function testKeyboardNavigation(
  element: HTMLElement,
  expectedOrder: string[]
) {
  const focusableElements = element.querySelectorAll(
    'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  
  expect(focusableElements.length).toBe(expectedOrder.length);
  
  focusableElements.forEach((el, index) => {
    const elementText = el.textContent || el.getAttribute('aria-label') || '';
    expect(elementText).toContain(expectedOrder[index]);
  });
}

/**
 * Check if element has proper ARIA attributes
 * @param element - The element to test
 * @param expectedAttributes - Object of expected ARIA attributes
 */
export function testAriaAttributes(
  element: HTMLElement,
  expectedAttributes: Record<string, string>
) {
  Object.entries(expectedAttributes).forEach(([attr, value]) => {
    expect(element).toHaveAttribute(attr, value);
  });
}

/**
 * Test color contrast ratio
 * Note: This is a simplified check - for comprehensive testing use axe-core
 */
export function getContrastRatio(
  foreground: string,
  background: string
): number {
  // Convert colors to RGB
  const getRGB = (color: string) => {
    const match = color.match(/\d+/g);
    return match ? match.map(Number) : [0, 0, 0];
  };
  
  const getLuminance = (rgb: number[]) => {
    const [r, g, b] = rgb.map(val => {
      val = val / 255;
      return val <= 0.03928 ? val / 12.92 : Math.pow((val + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  
  const l1 = getLuminance(getRGB(foreground));
  const l2 = getLuminance(getRGB(background));
  
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  
  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Check if contrast ratio meets WCAG standards
 * @param ratio - The contrast ratio
 * @param level - WCAG level ('AA' or 'AAA')
 * @param largeText - Whether the text is large (18pt+ or 14pt+ bold)
 */
export function meetsWCAGContrast(
  ratio: number,
  level: 'AA' | 'AAA' = 'AA',
  largeText = false
): boolean {
  if (level === 'AA') {
    return largeText ? ratio >= 3 : ratio >= 4.5;
  } else {
    return largeText ? ratio >= 4.5 : ratio >= 7;
  }
}