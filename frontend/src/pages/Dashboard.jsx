import { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Button } from 'react-bootstrap';
import { useAuth } from '../context/AuthContext';
import { databaseAPI, geminiAPI, queryAPI } from '../api/auth';
import Loader from '../components/Common/Loader';
import { toast } from 'react-hot-toast';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { docco } from 'react-syntax-highlighter/dist/esm/styles/hljs';

const Dashboard = () => {
  const { user } = useAuth();
  const [connections, setConnections] = useState([]);
  const [selectedConnection, setSelectedConnection] = useState(null);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [sqlOptions, setSqlOptions] = useState([]);
  const [selectedSQL, setSelectedSQL] = useState(null);
  const [explanation, setExplanation] = useState('');
  const [preview, setPreview] = useState(null);
  const [executionResult, setExecutionResult] = useState(null);

  useEffect(() => {
    loadConnections();
  }, []);

  const loadConnections = async () => {
    try {
      const response = await databaseAPI.list();
      setConnections(response.data);
    } catch (error) {
      toast.error('Failed to load connections');
    }
  };

  const handleGenerateSQL = async () => {
    if (!selectedConnection) {
      toast.error('Please select a database connection');
      return;
    }
    if (!query.trim()) {
      toast.error('Please enter your query');
      return;
    }

    setLoading(true);
    try {
      const response = await geminiAPI.generateSQL({
        connection_id: selectedConnection,
        question: query
      });
      setSqlOptions(response.data.options || []);
      if (response.data.options?.length > 0) {
        setSelectedSQL(response.data.options[0]);
      }
      toast.success('SQL generated successfully!');
    } catch (error) {
      toast.error('Failed to generate SQL');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleExplain = async (sql) => {
    if (!selectedConnection) return;
    
    setLoading(true);
    try {
      const response = await geminiAPI.explainQuery({
        connection_id: selectedConnection,
        sql_query: sql
      });
      setExplanation(response.data.explanation);
    } catch (error) {
      toast.error('Failed to explain query');
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async (sql) => {
    if (!selectedConnection) return;
    
    setLoading(true);
    try {
      const response = await queryAPI.preview({
        connection_id: selectedConnection,
        sql_query: sql
      });
      setPreview(response.data);
    } catch (error) {
      toast.error('Failed to preview query');
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async (sql) => {
    if (!selectedConnection) return;
    
    setLoading(true);
    try {
      const response = await queryAPI.execute({
        connection_id: selectedConnection,
        sql_query: sql,
        question: query
      });
      setExecutionResult(response.data);
      toast.success('Query executed successfully!');
    } catch (error) {
      toast.error('Failed to execute query');
    } finally {
      setLoading(false);
    }
  };

  const renderSQLOption = (option, index) => (
    <Card key={index} className="mb-3">
      <Card.Body>
        <div className="d-flex justify-content-between align-items-start">
          <div>
            <h6>Option {index + 1}</h6>
            <span className="badge bg-info me-2">Confidence: {option.confidence}%</span>
          </div>
          <div>
            <Button
              variant="outline-primary"
              size="sm"
              className="me-2"
              onClick={() => handleExplain(option.sql)}
            >
              Explain
            </Button>
            <Button
              variant="outline-secondary"
              size="sm"
              className="me-2"
              onClick={() => handlePreview(option.sql)}
            >
              Preview
            </Button>
            <Button
              variant="success"
              size="sm"
              onClick={() => handleExecute(option.sql)}
            >
              Execute
            </Button>
          </div>
        </div>
        <SyntaxHighlighter language="sql" style={docco} className="mt-2">
          {option.sql}
        </SyntaxHighlighter>
        <small className="text-muted">{option.explanation}</small>
      </Card.Body>
    </Card>
  );

  return (
    <Container fluid className="py-4">
      <Row>
        <Col lg={8}>
          <Card className="mb-4">
            <Card.Body>
              <h5>Ask a Question</h5>
              <div className="mb-3">
                <select
                  className="form-select mb-3"
                  value={selectedConnection || ''}
                  onChange={(e) => setSelectedConnection(Number(e.target.value))}
                >
                  <option value="">Select database connection</option>
                  {connections.map((conn) => (
                    <option key={conn.id} value={conn.id}>
                      {conn.database_name} ({conn.db_type})
                    </option>
                  ))}
                </select>
                <textarea
                  className="form-control"
                  rows="3"
                  placeholder="E.g., Show me the top 10 customers by total orders"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
              </div>
              <Button
                variant="primary"
                onClick={handleGenerateSQL}
                disabled={loading}
              >
                {loading ? 'Generating...' : 'Generate SQL'}
              </Button>
            </Card.Body>
          </Card>

          {sqlOptions.length > 0 && (
            <div>
              <h5 className="mb-3">SQL Options</h5>
              {sqlOptions.map((option, index) => renderSQLOption(option, index))}
            </div>
          )}

          {explanation && (
            <Card className="mb-4">
              <Card.Body>
                <h6>Explanation</h6>
                <p className="text-muted">{explanation}</p>
              </Card.Body>
            </Card>
          )}

          {executionResult && (
            <Card className="mb-4">
              <Card.Body>
                <h6>Execution Result</h6>
                {executionResult.success ? (
                  <>
                    {executionResult.query_type === 'SELECT' ? (
                      <>
                        <p>Rows returned: {executionResult.rows_returned}</p>
                        <div className="table-responsive">
                          <table className="table table-sm table-striped">
                            <thead>
                              <tr>
                                {executionResult.columns?.map((col) => (
                                  <th key={col}>{col}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {executionResult.data?.slice(0, 20).map((row, i) => (
                                <tr key={i}>
                                  {executionResult.columns?.map((col) => (
                                    <td key={col}>{String(row[col] || '')}</td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </>
                    ) : (
                      <p>Rows affected: {executionResult.rows_affected}</p>
                    )}
                    <small className="text-muted">
                      Execution time: {executionResult.execution_time.toFixed(3)}s
                    </small>
                  </>
                ) : (
                  <div className="alert alert-danger">
                    Error: {executionResult.error}
                  </div>
                )}
              </Card.Body>
            </Card>
          )}
        </Col>

        <Col lg={4}>
          <Card className="mb-4">
            <Card.Body>
              <h6>Quick Stats</h6>
              <div className="border-bottom py-2">
                <small className="text-muted">Connected Databases</small>
                <h5>{connections.length}</h5>
              </div>
              <div className="border-bottom py-2">
                <small className="text-muted">Recent Queries</small>
                <h5>Coming soon</h5>
              </div>
            </Card.Body>
          </Card>

          {preview && (
            <Card>
              <Card.Body>
                <h6>Preview</h6>
                <p className="text-muted">
                  Estimated rows: {preview.estimated_rows}
                </p>
                {preview.preview?.length > 0 ? (
                  <div className="table-responsive">
                    <table className="table table-sm">
                      <thead>
                        <tr>
                          {preview.columns?.slice(0, 3).map((col) => (
                            <th key={col}>{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {preview.preview.slice(0, 5).map((row, i) => (
                          <tr key={i}>
                            {preview.columns?.slice(0, 3).map((col) => (
                              <td key={col}>{String(row[col] || '')}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p>No preview data available</p>
                )}
              </Card.Body>
            </Card>
          )}
        </Col>
      </Row>

      {loading && <Loader />}
    </Container>
  );
};

export default Dashboard;