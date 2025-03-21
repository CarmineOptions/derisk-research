import { Link } from '@tanstack/react-router';

export default function Navbar() {
  return (
    <nav style={{ padding: '1rem', borderBottom: '1px solid #ddd', width: "100%"  }}>
      <Link to="/" style={{ marginRight: '1rem' }}>Home</Link>
      <Link to="/about">About</Link>
    </nav>
  );
}
