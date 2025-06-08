export default function HomePage() {
  const streamlitUrl = 'https://nhl-what-if-simulator.streamlit.app/';

  return (
    <div style={{ display: 'flex', justifyContent: 'center' }}>
      <iframe
        src={streamlitUrl}
        style={{ width: '100%', height: '90vh', border: 'none' }}
        title="NHL What-If Simulator"
      />
    </div>
  );
}
"use client";                   // Next.js App Router: make this a client component

export default function HomePage() {
  return (
    <div style={{
      width: "100%",
      height: "100vh",
      display: "flex",
      flexDirection: "column",
      alignItems: "stretch",
    }}>
      {/* You can tweak height to whatever suits you */}
      <iframe
        title="NHL What-If Simulator"
        src="https://share.streamlit.io/tristenh12/nhl-simulator/main/main.py"
        style={{
          border: "none",
          flexGrow: 1,
        }}
        allowFullScreen
      />
    </div>
  );
}
