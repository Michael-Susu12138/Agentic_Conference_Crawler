import { useState } from 'react';
import { 
  Container, Typography, Box, TextField, Button, 
  Paper, CircularProgress, Divider, Card, CardContent 
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import ApiService from '../services/api';

function Query() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [queryHistory, setQueryHistory] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    
    try {
      const result = await ApiService.runQuery(query);
      
      if (result.success) {
        setResponse(result.response);
        
        // Add to query history
        setQueryHistory([
          { query, response: result.response },
          ...queryHistory
        ]);
      } else {
        setError('Failed to get a response from the AI assistant.');
      }
    } catch (err) {
      console.error('Error running query:', err);
      setError('An error occurred while processing your query. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSampleQuery = (sampleQuery) => {
    setQuery(sampleQuery);
  };

  const sampleQueries = [
    "What are the top AI conferences in 2024?",
    "When is the deadline for ICML 2024?",
    "What are the trending topics in machine learning?",
    "Summarize recent papers on large language models",
    "Which conferences should I attend for computer vision research?"
  ];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        AI Query Assistant
      </Typography>
      <Typography variant="body1" color="textSecondary" paragraph>
        Ask questions about academic conferences, research papers, or any topic related to your research area.
      </Typography>

      {/* Query Form */}
      <Paper component="form" onSubmit={handleSubmit} elevation={3} sx={{ p: 3, mb: 4 }}>
        <TextField
          fullWidth
          label="Ask a question"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          variant="outlined"
          multiline
          rows={3}
          placeholder="e.g., What are the top AI conferences in 2024?"
          sx={{ mb: 2 }}
        />
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            type="submit"
            variant="contained"
            color="primary"
            endIcon={<SendIcon />}
            disabled={loading || !query.trim()}
          >
            {loading ? 'Asking...' : 'Ask'}
          </Button>
        </Box>
      </Paper>

      {/* Sample Queries */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="subtitle1" gutterBottom>
          Try these sample queries:
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {sampleQueries.map((sampleQuery, index) => (
            <Button 
              key={index} 
              variant="outlined" 
              size="small" 
              onClick={() => handleSampleQuery(sampleQuery)}
              sx={{ mb: 1 }}
            >
              {sampleQuery}
            </Button>
          ))}
        </Box>
      </Box>

      {/* Loading Indicator */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Error Message */}
      {error && (
        <Paper sx={{ p: 3, mb: 4, bgcolor: '#ffebee' }}>
          <Typography color="error">{error}</Typography>
        </Paper>
      )}

      {/* Current Response */}
      {response && !loading && (
        <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
            <SmartToyIcon sx={{ mr: 2, color: 'primary.main' }} />
            <Box>
              <Typography variant="subtitle1" fontWeight="bold">
                AI Assistant
              </Typography>
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                {response}
              </Typography>
            </Box>
          </Box>
        </Paper>
      )}

      {/* Query History */}
      {queryHistory.length > 0 && (
        <Box sx={{ mt: 6 }}>
          <Typography variant="h6" gutterBottom>
            Recent Questions
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          {queryHistory.map((item, index) => (
            <Card key={index} sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="subtitle2" color="primary" gutterBottom>
                  You asked:
                </Typography>
                <Typography variant="body2" paragraph>
                  {item.query}
                </Typography>
                
                <Typography variant="subtitle2" color="primary" gutterBottom>
                  Response:
                </Typography>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {item.response}
                </Typography>
              </CardContent>
            </Card>
          ))}
        </Box>
      )}
    </Container>
  );
}

export default Query; 