import { useState, useEffect } from 'react';
import { 
  Container, Typography, Box, Button, Card, CardContent, 
  CardHeader, Grid, CircularProgress, TextField, MenuItem, 
  FormControl, Select, InputLabel, Chip, Divider, Alert 
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import EventIcon from '@mui/icons-material/Event';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import ApiService from '../services/api';

function Conferences() {
  const [conferences, setConferences] = useState([]);
  const [researchAreas, setResearchAreas] = useState([]);
  const [selectedArea, setSelectedArea] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [totalCount, setTotalCount] = useState(0);

  // Load conferences and research areas on component mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        const areasData = await ApiService.getResearchAreas();
        setResearchAreas(areasData);
        
        const conferencesData = await ApiService.getConferences();
        setConferences(conferencesData);
        setTotalCount(conferencesData.length);
        
        setLoading(false);
      } catch (err) {
        console.error('Error loading data:', err);
        setError('Failed to load data. Please try again later.');
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Filter conferences when research area changes
  useEffect(() => {
    const filterConferences = async () => {
      if (!selectedArea) return;
      
      setLoading(true);
      try {
        const filteredData = await ApiService.getConferences(selectedArea);
        setConferences(filteredData);
        setTotalCount(filteredData.length);
        setLoading(false);
      } catch (err) {
        console.error('Error filtering conferences:', err);
        setError('Failed to filter conferences. Please try again.');
        setLoading(false);
      }
    };

    filterConferences();
  }, [selectedArea]);

  const handleRefresh = async () => {
    setRefreshing(true);
    setSuccess(null);
    setError(null);
    
    try {
      // Default to selected area or use all areas if none selected
      const areasToRefresh = selectedArea ? [selectedArea] : researchAreas.slice(0, 3);
      
      const result = await ApiService.refreshConferences(areasToRefresh);
      
      if (result.success) {
        setSuccess(`Successfully refreshed conferences! Found ${result.results?.total_conferences || 0} conferences.`);
        
        // Reload the conferences with the new data
        const refreshedData = await ApiService.getConferences(selectedArea);
        setConferences(refreshedData);
      } else {
        setError('Refresh completed but no new conferences were found.');
      }
    } catch (err) {
      console.error('Error refreshing conferences:', err);
      setError('Failed to refresh conferences. Please try again later.');
    } finally {
      setRefreshing(false);
    }
  };

  const handleAreaChange = (event) => {
    setSelectedArea(event.target.value);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Upcoming Academic Conferences
      </Typography>
      <Typography variant="body1" color="textSecondary" paragraph>
        Browse and track upcoming academic conferences in various research areas.
        Only showing valid, non-duplicate conferences with future dates.
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
            {refreshing ? 'Refreshing...' : 'Refresh Conferences'}
          </Button>
        </Grid>
      </Grid>

      {/* Conferences Stats */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle1">
          Showing {totalCount} upcoming conferences
          {selectedArea ? ` in "${selectedArea}"` : ''}
        </Typography>
      </Box>

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

      {/* Conferences List */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      ) : conferences && conferences.length > 0 ? (
        <Grid container spacing={3}>
          {conferences.map((conference) => (
            <Grid item xs={12} md={6} key={conference.id}>
              <Card sx={{ height: '100%' }}>
                <CardHeader
                  title={conference.title}
                  subheader={
                    <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                      <EventIcon fontSize="small" sx={{ mr: 1 }} />
                      {conference.dates || 'Date not specified'}
                    </Box>
                  }
                />
                <CardContent>
                  {conference.research_areas && conference.research_areas.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                      {conference.research_areas.map((area, index) => (
                        <Chip 
                          key={index} 
                          label={area}
                          size="small" 
                          color="primary"
                          variant="outlined"
                          sx={{ mr: 1, mb: 1 }} 
                        />
                      ))}
                    </Box>
                  )}
                  
                  {conference.description && (
                    <Typography variant="body2" paragraph>
                      {conference.description}
                    </Typography>
                  )}
                  
                  {conference.location && (
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <LocationOnIcon fontSize="small" sx={{ mr: 1 }} />
                      <Typography variant="body2">
                        {conference.location}
                      </Typography>
                    </Box>
                  )}
                  
                  <Divider sx={{ my: 1 }} />
                  
                  {/* Deadlines Section */}
                  {conference.deadlines && conference.deadlines.length > 0 && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Important Deadlines:
                      </Typography>
                      {conference.deadlines.map((deadline, index) => (
                        <Chip 
                          key={index} 
                          label={deadline} 
                          size="small" 
                          sx={{ mr: 1, mb: 1 }} 
                        />
                      ))}
                    </Box>
                  )}
                  
                  {/* Link to conference */}
                  {conference.url && (
                    <Box sx={{ mt: 2 }}>
                      <Button 
                        variant="outlined" 
                        size="small" 
                        href={conference.url} 
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        Visit Website
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
          No conferences found. Try changing the filter or refreshing the data.
        </Alert>
      )}
    </Container>
  );
}

export default Conferences; 