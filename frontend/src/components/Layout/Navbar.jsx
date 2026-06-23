import { Navbar, Nav, Container, Button } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { FaDatabase, FaHistory } from 'react-icons/fa';

const AppNavbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <Navbar bg="dark" variant="dark" expand="lg" className="mb-4">
      <Container>
        <Navbar.Brand as={Link} to="/dashboard">
          <span className="text-info">SQL</span> Genie
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="ms-auto">
            {user && (
              <>
                <Nav.Link as={Link} to="/dashboard">
                  <FaDatabase className="me-1" /> Dashboard
                </Nav.Link>
                <Nav.Link as={Link} to="/connections">
                  Connections
                </Nav.Link>
                <Nav.Link as={Link} to="/history">
                  <FaHistory className="me-1" /> History
                </Nav.Link>
                <Nav.Link className="text-light">
                  Welcome, {user.name || user.email}
                </Nav.Link>
                <Button variant="outline-light" size="sm" onClick={handleLogout}>
                  Logout
                </Button>
              </>
            )}
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default AppNavbar;