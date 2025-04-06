import { useState, useEffect } from 'react';
import { 
  Container, Typography, Box, Button, Card, CardContent, 
  CardHeader, Grid, CircularProgress, TextField, MenuItem, 
  FormControl, Select, InputLabel, Chip, Divider, Alert, 
  IconButton, Link, Collapse 
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ApiService from '../services/api';

function Papers() {
  const [papers, setPapers] = useState([]);
  const [researchAreas, setResearchAreas] = useState([]);
  const [selectedArea, setSelectedArea] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [expandedPapers, setExpandedPapers] = useState({});

  // Load papers and research areas on component mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        const areasData = await ApiService.getResearchAreas();
        setResearchAreas(areasData);
        
        const papersData = await ApiService.getPapers();
        setPapers(papersData);
        
        setLoading(false);
      } catch (err) {
        console.error('Error loading data:', err);
        setError('Failed to load data. Please try again later.');
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Filter papers when research area changes
  useEffect(() => {
    const filterPapers = async () => {
      if (!selectedArea) return;
      
      setLoading(true);
      try {
        const filteredData = await ApiService.getPapers(selectedArea);
        setPapers(filteredData);
        setLoading(false);
      } catch (err) {
        console.error('Error filtering papers:', err);
        setError('Failed to filter papers. Please try again.');
        setLoading(false);
      }
    };

    filterPapers();
  }, [selectedArea]);

  const handleRefresh = async () => {
    setRefreshing(true);
    setSuccess(null);
    setError(null);
    
    try {
      // Default to selected area or use all areas if none selected
      const areasToRefresh = selectedArea ? [selectedArea] : researchAreas.slice(0, 3);
      
      const result = await ApiService.refreshPapers(areasToRefresh);
      
      if (result.success) {
        setSuccess(`Successfully refreshed papers! Found ${result.results?.total_papers || 0} papers.`);
        
        // Reload the papers with the new data
        const refreshedData = await ApiService.getPapers(selectedArea);
        setPapers(refreshedData);
      } else {
        setError('Refresh completed but no new papers were found.');
      }
    } catch (err) {
      console.error('Error refreshing papers:', err);
      setError('Failed to refresh papers. Please try again later.');
    } finally {
      setRefreshing(false);
    }
  };

  const handleAreaChange = (event) => {
    setSelectedArea(event.target.value);
  };

  const toggleExpand = (paperId) => {
    setExpandedPapers(prev => ({
      ...prev,
      [paperId]: !prev[paperId]
    }));
  };

  const truncateText = (text, maxLength = 200) => {
    if (!text || text.length <= maxLength) return text;
    return text.slice(0, maxLength) + '...';
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Research Papers
      </Typography>
      <Typography variant="body1" color="textSecondary" paragraph>
        Browse recent research papers in various academic fields.
      </Typography>

      {/* Filter and Refresh Controls */}
      <Grid container spacing={2} alignItems="center" sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <FormControl fullWidth variant="outlined">
            <InputLabel id="research-area-label">Filter by Research Area</InputLabel>
            <Select
              labelId="research-area-label"
              value={selectedArea}
              onChange={handleAreaChange}
              label="Filter by Research Area"
            >
              <MenuItem value="">
                <em>All Areas</em>
              </MenuItem>
              {researchAreas.map((area) => (
                <MenuItem key={area} value={area}>
                  {area}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} md={6}>
          <Button
            variant="contained"
            color="primary"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={refreshing}
            fullWidth
          >
            {refreshing ? 'Refreshing...' : 'Refresh Papers'}
          </Button>
        </Grid>
      </Grid>

      {/* Status Messages */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {/* Papers List */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      ) : papers && papers.length > 0 ? (
        <Grid container spacing={3}>
          {papers.map((paper) => (
            <Grid item xs={12} key={paper.id}>
              <Card sx={{ height: '100%' }}>
                <CardHeader
                  title={paper.title}
                  subheader={
                    <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                      <Chip 
                        label={paper.research_area || 'Research Area Not Specified'} 
                        size="small" 
                        color="primary" 
                        variant="outlined"
                      />
                      {paper.year && (
                        <Chip 
                          label={paper.year} 
                          size="small" 
                          sx={{ ml: 1 }} 
                        />
                      )}
                    </Box>
                  }
                  action={
                    paper.abstract && (
                      <IconButton onClick={() => toggleExpand(paper.id)}>
                        {expandedPapers[paper.id] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                      </IconButton>
                    )
                  }
                />
                <CardContent>
                  {/* Authors */}
                  {paper.authors && (
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      <strong>Authors:</strong> {paper.authors}
                    </Typography>
                  )}
                  
                  {/* Abstract (collapsible) */}
                  {paper.abstract && (
                    <>
                      <Typography variant="subtitle2" gutterBottom>
                        Abstract:
                      </Typography>
                      <Typography variant="body2" paragraph>
                        {expandedPapers[paper.id] ? paper.abstract : truncateText(paper.abstract)}
                      </Typography>
                      {paper.abstract.length > 200 && !expandedPapers[paper.id] && (
                        <Button 
                          size="small" 
                          onClick={() => toggleExpand(paper.id)}
                          sx={{ mb: 2 }}
                        >
                          Read More
                        </Button>
                      )}
                    </>
                  )}
                  
                  <Divider sx={{ my: 1 }} />
                  
                  {/* Link to paper */}
                  {paper.url && (
                    <Box sx={{ mt: 2 }}>
                      <Button 
                        variant="outlined" 
                        size="small" 
                        href={paper.url} 
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        View Paper
                      </Button>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      ) : (
        <Alert severity="info" sx={{ my: 2 }}>
          No papers found. Try changing the filter or refreshing the data.
        </Alert>
      )}
    </Container>
  );
}

export default Papers; 