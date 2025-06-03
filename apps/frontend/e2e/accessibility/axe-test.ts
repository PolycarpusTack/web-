import { test as base } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

type AxeFixture = {
  makeAxeBuilder: () => AxeBuilder;
};

// Extend base test with axe-core
export const test = base.extend<AxeFixture>({
  makeAxeBuilder: async ({ page }, use) => {
    const makeAxeBuilder = () => new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .exclude('#third-party-content'); // Exclude third-party content if any
    
    await use(makeAxeBuilder);
  }
});

export { expect } from '@playwright/test';

// Helper to format accessibility violations
export function formatViolations(violations: any[]) {
  return violations.map(violation => {
    const targets = violation.nodes.map((node: any) => node.target.join(', ')).join('\n  ');
    return `
Rule: ${violation.id}
Impact: ${violation.impact}
Description: ${violation.description}
Help: ${violation.help}
Help URL: ${violation.helpUrl}
Affected elements:
  ${targets}
`;
  }).join('\n---\n');
}