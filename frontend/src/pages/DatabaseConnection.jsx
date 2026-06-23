import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Form, Button, Alert } from 'react-bootstrap';
import { databaseAPI } from '../api/auth';
import { toast } from 'react-hot-toast';

const DatabaseConnection = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [formData, setFormData] = useState({
    db_type: 'postgresql',
    host: 'localhost',
    port: 5432,
    username: '',
    password: '',
    database_name: '',
    connection_name: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await databaseAPI.connect(formData);
      toast.success('Database connected successfully!');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to connect database');
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    if (!formData.host || !formData.username || !formData.database_name) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    setTesting(true);
    setTestResult(null);
    
    try {
      const response = await databaseAPI.testConnection({
        db_type: formData.db_type,
        host: formData.host,
        port: formData.port,
        username: formData.username,
        password: formData.password,
        database_name: formData.database_name
      });
      
      setTestResult(response.data);
      if (response.data.success) {
        toast.success('Connection test passed! ✅');
      } else {
        toast.error(response.data.message || 'Connection failed');
      }
    } catch (error) {
      const msg = error.response?.data?.message || error.response?.data?.detail || 'Connection test failed';
      setTestResult({ success: false, message: msg });
      toast.error(msg);
    } finally {
      setTesting(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'port' ? parseInt(value) || 0 : value
    }));
  };

  return (
    <div className="container mt-4">
      <div className="row justify-content-center">
        <div className="col-md-8">
          <Card>
            <Card.Body className="p-4">
              <h3 className="mb-4">Connect Database</h3>
              
              {testResult && (
                <Alert variant={testResult.success ? 'success' : 'danger'}>
                  {testResult.message}
                </Alert>
              )}
              
              <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-3">
                  <Form.Label>Connection Name (Optional)</Form.Label>
                  <Form.Control
                    type="text"
                    name="connection_name"
                    value={formData.connection_name}
                    onChange={handleChange}
                    placeholder="My Production DB"
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Database Type</Form.Label>
                  <Form.Select
                    name="db_type"
                    value={formData.db_type}
                    onChange={handleChange}
                  >
                    <option value="postgresql">PostgreSQL</option>
                    <option value="mysql">MySQL</option>
                  </Form.Select>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Host</Form.Label>
                  <Form.Control
                    type="text"
                    name="host"
                    value={formData.host}
                    onChange={handleChange}
                    required
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Port</Form.Label>
                  <Form.Control
                    type="number"
                    name="port"
                    value={formData.port}
                    onChange={handleChange}
                    required
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Username</Form.Label>
                  <Form.Control
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    required
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Password (Optional)</Form.Label>
                  <Form.Control
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="Leave empty if no password"
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Database Name</Form.Label>
                  <Form.Control
                    type="text"
                    name="database_name"
                    value={formData.database_name}
                    onChange={handleChange}
                    required
                  />
                </Form.Group>

                <div className="d-flex gap-2">
                  <Button
                    variant="secondary"
                    onClick={handleTestConnection}
                    disabled={testing}
                  >
                    {testing ? 'Testing...' : 'Test Connection'}
                  </Button>
                  <Button
                    variant="primary"
                    type="submit"
                    disabled={loading}
                  >
                    {loading ? 'Connecting...' : 'Save Connection'}
                  </Button>
                  <Button
                    variant="outline-secondary"
                    onClick={() => navigate('/dashboard')}
                  >
                    Cancel
                  </Button>
                </div>
              </Form>
            </Card.Body>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default DatabaseConnection;