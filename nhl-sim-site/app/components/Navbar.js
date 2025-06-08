// app/components/Navbar.js
import Link from 'next/link'

export default function Navbar() {
  return (
    <nav style={{
      display: 'flex',
      justifyContent: 'center',
      gap: '2rem',
      padding: '1rem 0',
      borderBottom: '1px solid #ddd'
    }}>
      <Link href="/">Home</Link>
      <Link href="/about">About</Link>
    </nav>
  )
}
