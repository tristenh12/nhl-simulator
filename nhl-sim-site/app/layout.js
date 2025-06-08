// app/layout.js
import './globals.css';
import Navbar from './components/Navbar';

export const metadata = {
  title: 'NHL What-If Simulator',
  description: 'Pick any 32 NHL teams across eras, simulate a season, view standings & playoffs',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        <main style={{ padding: '1rem' }}>
          {children}
        </main>
      </body>
    </html>
  );
}
