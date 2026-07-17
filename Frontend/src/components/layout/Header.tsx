import { Stack } from "@telefonica/mistica";
import Breadcrumb from "@/components/ui/Breadcrumb";
import type { BreadcrumbItem } from "@/types/Common";

interface HeaderProps {
    breadcrumbItems?: BreadcrumbItem[];
    children: React.ReactNode;
}

function Header({ breadcrumbItems, children }: Readonly<HeaderProps>) {
    return (
        <Stack space={56}>
            {breadcrumbItems && <Breadcrumb items={breadcrumbItems} />}
            {children}
        </Stack>
    );
}

export default Header;
