import MainLayout from "@/components/layout/MainLayout";
import Sidebar from "@/components/layout/Sidebar";

export default function AppLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <MainLayout>
      <Sidebar name="AgentHound" />
      <div style={{ position: "relative", flex: 1, overflowY: "auto", paddingBottom: 40 }}>
        {children}
      </div>
    </MainLayout>
  );
}
