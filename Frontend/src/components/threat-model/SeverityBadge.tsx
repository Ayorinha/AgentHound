import { Tag } from "@telefonica/mistica";
import { SEVERITY_STYLES, type Severity } from "@/lib/severity";

interface SeverityBadgeProps {
  severity: Severity;
  children: string;
  small?: boolean;
}

function SeverityBadge({ severity, children, small }: SeverityBadgeProps) {
  const style = SEVERITY_STYLES[severity];
  return (
    <Tag backgroundColor={style.background} textColor={style.text} small={small}>
      {children}
    </Tag>
  );
}

export default SeverityBadge;
