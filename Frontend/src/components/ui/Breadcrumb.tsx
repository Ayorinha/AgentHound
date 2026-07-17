import type { BreadcrumbProps } from "@/types/Common";
import { Text2, skinVars } from "@telefonica/mistica";
import Link from "next/link";

function Breadcrumb({ items }: BreadcrumbProps) {
    return (
        <nav aria-label="Breadcrumb">
            {items.map((item, index) => {
                const isLast = index === items.length - 1;
                const isFirst = index === 0;

                return (
                    <span key={item.label}>
                        {/* Separator */}
                        {!isFirst && (
                            <Text2 regular color={skinVars.colors.textSecondary} as="span">
                                {" / "}
                            </Text2>
                        )}

                        {/* Item */}
                        {item.href && !isLast ? (
                            <Link href={item.href}>
                                <Text2
                                    regular
                                    color={skinVars.colors.textPrimary}
                                    as="span"
                                >
                                    {item.label}
                                </Text2>
                            </Link>
                        ) : (
                            <Text2
                                regular
                                color={isLast ? skinVars.colors.textSecondary : skinVars.colors.textPrimary}
                                as="span"
                            >
                                {item.label}
                            </Text2>
                        )}
                    </span>
                );
            })}
        </nav>
    );
}

export default Breadcrumb;
