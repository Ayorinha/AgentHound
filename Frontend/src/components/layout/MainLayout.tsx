import BackgroundGlowBlobs from "../ui/BackgroundGlowBlobs"

function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        position: "relative",
        display: "flex",
        height: "100vh",
        width: "100%",
        alignSelf: "stretch",
        justifyContent: "space-between",
        gap: 16,
        paddingRight: 16,
      }}
    >
      <BackgroundGlowBlobs />
      {children}
    </div>
  )
}

export default MainLayout