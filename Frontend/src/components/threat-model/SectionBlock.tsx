import { Box, Boxed, Stack, Text2, Text3, Text4, skinVars } from "@telefonica/mistica";
import type { ReactNode } from "react";

interface SectionBlockProps {
  title?: string;
  subtitle?: string;
  requiredTag?: string;
  required?: boolean;
  children?: ReactNode;
}

function SectionBlock({ title, subtitle, requiredTag, required, children }: SectionBlockProps) {
  return (
    <Boxed width="100%">
      <Box paddingX={32} paddingY={40}>
        <Stack space={32}>
          {(title || subtitle) && (
            <Stack space={12}>
              {title && (
                <Text4 medium as="h3">
                  {title}
                  {required && requiredTag && (
                    <>
                      {" "}
                      <Text2 regular color={skinVars.colors.textSecondary}>{requiredTag}</Text2>
                    </>
                  )}
                </Text4>
              )}
              {subtitle && (
                <Text3 regular color={skinVars.colors.textSecondary}>{subtitle}</Text3>
              )}
            </Stack>
          )}
          {children}
        </Stack>
      </Box>
    </Boxed>
  );
}

export default SectionBlock;
