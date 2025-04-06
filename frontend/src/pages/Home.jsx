import { useState, useEffect } from 'react';
import { Typography, Box, Grid, Card, CardContent, CardHeader, CardActionArea, Button, Container, Paper, Divider } from '@mui/material';
import { Link } from 'react-router-dom';
import ApiService from '../services/api';

function Home() {
  const [apiStatus, setApiStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        const status = await ApiService.getApiStatus();
        setApiStatus(status);
        setLoading(false);
      } catch (err) {
        console.error('Error checking API status:', err);
        setError('Failed to connect to the API. Please ensure the backend server is running.');
        setLoading(false);
      }
    };

    checkApiStatus();
  }, []);

  const features = [
    {
      title: 'Conference Monitoring',
      description: 'Track upcoming academic conferences in your research areas of interest',
      link: '/conferences'
    },
    {
      title: 'Research Papers',
      description: 'Stay updated with the latest papers in your field',
      link: '/papers'
    },
    {
      title: 'Trending Topics',
      description: 'Discover trending research topics and stay ahead of the curve',
      link: '/trends'
    },
    {
      title: 'AI Query Assistant',
      description: 'Ask questions and get AI-powered answers about conferences and research',
      link: '/query'
    }
  ];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4, mb: 4, borderRadius: 2 }}>
        <Typography variant="h4" component="h1" gutterBottom align="center">
          Conference Monitor
        </Typography>
        <Typography variant="h6" color="textSecondary" align="center" paragraph>
          Your AI-powered assistant for tracking academic conferences and research papers
        </Typography>
        
        {/* API Status */}
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
          {loading ? (
            <Typography>Checking API connection...</Typography>
          ) : error ? (
            <Typography color="error">{error}</Typography>
          ) : (
            <Box sx={{ textAlign: 'center' }}>
              <Typography color="primary">
                API Status: {apiStatus?.status} | Provider: {apiStatus?.api_provider}
              </Typography>
              <Typography variant="caption">
                API Version: {apiStatus?.version}
              </Typography>
            </Box>
          )}
        </Box>

        <Divider sx={{ my: 3 }} />
        
        <Typography variant="h5" gutterBottom align="center" sx={{ mb: 3 }}>
          What would you like to do?
        </Typography>

        <Grid container spacing={3}>
          {features.map((feature) => (
            <Grid item xs={12} sm={6} key={feature.title}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardActionArea component={Link} to={feature.link}>
                  <CardHeader title={feature.title} />
                  <CardContent>
                    <Typography variant="body1">{feature.description}</Typography>
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Paper>
      
      <Box sx={{ textAlign: 'center', mt: 4 }}>
        <Button 
          variant="contained" 
          color="primary" 
          component={Link} 
          to="/query"
          size="large"
        >
          Ask the AI Assistant
        </Button>
      </Box>
    </Container>
  );
}

export default Home; 