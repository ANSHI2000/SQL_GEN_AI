import { useState } from 'react';
import { geminiAPI, queryAPI } from '../api/auth';
import { toast } from 'react-hot-toast';

export const useQuery = () => {
  const [loading, setLoading] = useState(false);
  const [sqlOptions, setSqlOptions] = useState([]);
  const [explanation, setExplanation] = useState('');
  const [preview, setPreview] = useState(null);
  const [executionResult, setExecutionResult] = useState(null);

  const generateSQL = async (connectionId, question) => {
    setLoading(true);
    try {
      const response = await geminiAPI.generateSQL({
        connection_id: connectionId,
        question: question
      });
      setSqlOptions(response.data.options || []);
      return response.data.options || [];
    } catch (error) {
      toast.error('Failed to generate SQL');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const explainQuery = async (connectionId, sql) => {
    setLoading(true);
    try {
      const response = await geminiAPI.explainQuery({
        connection_id: connectionId,
        sql_query: sql
      });
      setExplanation(response.data.explanation);
      return response.data.explanation;
    } catch (error) {
      toast.error('Failed to explain query');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const previewQuery = async (connectionId, sql) => {
    setLoading(true);
    try {
      const response = await queryAPI.preview({
        connection_id: connectionId,
        sql_query: sql
      });
      setPreview(response.data);
      return response.data;
    } catch (error) {
      toast.error('Failed to preview query');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const executeQuery = async (connectionId, sql, question = '') => {
    setLoading(true);
    try {
      const response = await queryAPI.execute({
        connection_id: connectionId,
        sql_query: sql,
        question: question
      });
      setExecutionResult(response.data);
      toast.success('Query executed successfully!');
      return response.data;
    } catch (error) {
      toast.error('Failed to execute query');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const clearResults = () => {
    setSqlOptions([]);
    setExplanation('');
    setPreview(null);
    setExecutionResult(null);
  };

  return {
    loading,
    sqlOptions,
    explanation,
    preview,
    executionResult,
    generateSQL,
    explainQuery,
    previewQuery,
    executeQuery,
    clearResults
  };
};