import type { NavItem } from "@/types/Common";
import { IconListFilled, IconStatusChartRegular } from "@telefonica/mistica";

const NAV_ITEMS: NavItem[] = [
  { labelKey: "layout.nav.overview", href: "/overview", icon: IconListFilled },
  { labelKey: "layout.nav.results", href: "/results", icon: IconStatusChartRegular },
];

export { NAV_ITEMS };
