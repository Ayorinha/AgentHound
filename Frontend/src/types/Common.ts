
export type IconProps = {
  color?: string
  size?: number
}

export interface NavItem {
  labelKey: string
  href: string
  icon: React.ComponentType<IconProps>
  active?: boolean
}

export interface SidebarProps {
  name?: string
  className?: string
}

export interface BreadcrumbItem {
  label: string
  href?: string
}

export interface BreadcrumbProps {
  items: BreadcrumbItem[]
}
