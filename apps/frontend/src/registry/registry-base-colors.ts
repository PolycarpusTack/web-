export interface BaseColor {
  name: string;
  label: string;
  activeColor: {
    light: string;
    dark: string;
  };
  cssVars: {
    light: Record<string, string>;
    dark: Record<string, string>;
  };
}

export const baseColors: BaseColor[] = [
  {
    name: "slate",
    label: "Slate",
    activeColor: {
      light: "240 5.9% 10%",
      dark: "240 5.2% 33.9%",
    },
    cssVars: {
      light: {
        "--primary": "240 5.9% 10%",
        "--primary-foreground": "0 0% 98%",
      },
      dark: {
        "--primary": "0 0% 98%",
        "--primary-foreground": "240 5.9% 10%",
      },
    },
  },
  {
    name: "zinc",
    label: "Zinc",
    activeColor: {
      light: "240 5.2% 26%",
      dark: "240 5.2% 33.9%",
    },
    cssVars: {
      light: {
        "--primary": "240 5.9% 10%",
        "--primary-foreground": "0 0% 98%",
      },
      dark: {
        "--primary": "0 0% 98%",
        "--primary-foreground": "240 5.9% 10%",
      },
    },
  },
];