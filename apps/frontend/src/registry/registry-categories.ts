export interface RegistryCategory {
  name: string;
  slug: string;
  hidden?: boolean;
}

export const registryCategories: RegistryCategory[] = [
  {
    name: "Application",
    slug: "application",
  },
  {
    name: "Dashboard",
    slug: "dashboard",
  },
  {
    name: "Marketing",
    slug: "marketing",
  },
  {
    name: "E-commerce",
    slug: "ecommerce",
  },
];