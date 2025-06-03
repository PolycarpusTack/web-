export interface NavItem {
  title: string;
  href?: string;
  disabled?: boolean;
  external?: boolean;
  label?: string;
  icon?: string;
}

export interface SidebarNavItem extends NavItem {
  items?: SidebarNavItem[];
}

export interface DocsConfig {
  mainNav: NavItem[];
  sidebarNav: SidebarNavItem[];
}

export const docsConfig: DocsConfig = {
  mainNav: [
    {
      title: "Home",
      href: "/",
    },
    {
      title: "Models",
      href: "/models",
    },
    {
      title: "Chat",
      href: "/chat",
    },
    {
      title: "Pipelines",
      href: "/pipelines",
    },
  ],
  sidebarNav: [
    {
      title: "Getting Started",
      items: [
        {
          title: "Introduction",
          href: "/docs",
        },
        {
          title: "Installation",
          href: "/docs/installation",
        },
      ],
    },
    {
      title: "Features",
      items: [
        {
          title: "Models",
          href: "/docs/models",
        },
        {
          title: "Chat Interface",
          href: "/docs/chat",
        },
        {
          title: "Pipelines",
          href: "/docs/pipelines",
        },
      ],
    },
  ],
};