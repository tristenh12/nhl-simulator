export default function About_page() {
  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h1>About the NHL What-If Simulator</h1>
      <p>
        This tool lets you pick any 32 NHL squads (across eras), simulate an 82-game season, view standings & playoff
        brackets. Built with Streamlit + Next.js for embedding, ads, and easy navigation!
      </p>
      <h2>How It Works</h2>
      <ul>
        <li>Select your 32 teams and seasons</li>
        <li>Run a full-season sim or a one-game sim</li>
        <li>View standings, playoffs, and series details</li>
      </ul>
    </div>
  );
}
