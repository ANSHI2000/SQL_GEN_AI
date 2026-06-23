import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authAPI } from '../api/auth';
import { toast } from 'react-hot-toast';

const VerifyOTP = () => {
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [timer, setTimer] = useState(300);
  const { verifyOTP } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email || '';

  useEffect(() => {
    if (!email) {
      navigate('/signup');
    }

    const interval = setInterval(() => {
      setTimer((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [email, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const result = await verifyOTP({ email, otp });
      toast.success('Email verified! You can now login.');
      navigate('/login');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Invalid OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleResendOTP = async () => {
    setResending(true);
    try {
      const response = await authAPI.resendOTP({ email });
      if (response.data.otp) {
        toast.success(`New OTP: ${response.data.otp} (email sending failed)`);
      } else {
        toast.success('OTP resent successfully!');
      }
      setTimer(300);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to resend OTP');
    } finally {
      setResending(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2 className="text-center mb-4">Verify Email</h2>
        <p className="text-center text-muted">
          Enter the 6-digit code sent to <strong>{email}</strong>
        </p>
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="form-label">OTP Code</label>
            <input
              type="text"
              className="form-control text-center"
              maxLength="6"
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
              placeholder="Enter 6-digit OTP"
              required
            />
          </div>
          <div className="text-center mb-3">
            <small className="text-muted">
              {timer > 0 ? `Time remaining: ${formatTime(timer)}` : 'OTP expired'}
            </small>
          </div>
          <button type="submit" className="btn btn-primary w-100" disabled={loading || timer === 0}>
            {loading ? 'Verifying...' : 'Verify OTP'}
          </button>
        </form>
        <p className="text-center mt-3">
          <button 
            className="btn btn-link btn-sm" 
            onClick={handleResendOTP}
            disabled={resending}
          >
            {resending ? 'Resending...' : 'Resend OTP'}
          </button>
        </p>
      </div>
    </div>
  );
};

export default VerifyOTP;