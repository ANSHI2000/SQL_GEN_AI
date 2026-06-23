import { Spinner } from 'react-bootstrap';

const Loader = ({ size = 'lg', message = 'Loading...' }) => {
  return (
    <div className="text-center py-5">
      <Spinner animation="border" variant="primary" size={size} />
      <p className="mt-3 text-muted">{message}</p>
    </div>
  );
};

export default Loader;