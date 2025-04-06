import { useState, useEffect } from 'react';
import { 
  Container, Typography, Box, Grid, CircularProgress, 
  Card, CardContent, FormControl, Select, MenuItem, 
  InputLabel, Alert, List, ListItem, ListItemIcon, 
  ListItemText, Divider, Chip
} from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import ApiService from '../services/api';

function Trends() {
  const [trends, setTrends] = useState({});
  const [researchAreas, setResearchAreas] = useState([]);
  const [selectedArea, setSelectedArea] = useState('artificial intelligence');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load research areas on component mount
  useEffect(() => {
    const fetchAreas = async () => {
      try {
        const areas = await ApiService.getResearchAreas();
        setResearchAreas(areas);
        
        if (areas.length > 0 && !areas.includes(selectedArea)) {
          setSelectedArea(areas[0]);
        }
      } catch (err) {
        console.error('Error loading research areas:', err);
        setError('Failed to load research areas. Please try again later.');
      }
    };

    fetchAreas();
  }, []);

  // Load trends when selected area changes
  useEffect(() => {
    const fetchTrends = async () => {
      if (!selectedArea) return;
      
      setLoading(true);
      setError(null);
      
      try {
        const trendsData = await ApiService.getTrends(selectedArea, 20);
        setTrends(trendsData.trends || {});
        setLoading(false);
      } catch (err) {
        console.error('Error loading trends:', err);
        setError('Failed to load trends. Please try again later.');
        setLoading(false);
      }
    };

    fetchTrends();
  }, [selectedArea]);

  const handleAreaChange = (event) => {
    setSelectedArea(event.target.value);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Trending Research Topics
      </Typography>
      <Typography variant="body1" color="textSecondary" paragraph>
        Discover current trending topics and research directions in your field of interest.
      </Typography>

      {/* Research Area Selector */}
      <Box sx={{ mb: 4, maxWidth: 400 }}>
        <FormControl fullWidth variant="outlined">
          <InputLabel id="research-area-label">Research Area</InputLabel>
          <Select
            labelId="research-area-label"
            value={selectedArea}
            onChange={handleAreaChange}
            label="Research Area"
          >
            {researchAreas.map((area) => (
              <MenuItem key={area} value={area}>
                {area}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 4 }}>
          {error}
        </Alert>
      )}

      {/* Trends Display */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3}>
          {Object.keys(trends).length > 0 ? (
            Object.entries(trends).map(([area, areaTopics]) => (
              <Grid item xs={12} key={area}>
                <Card elevation={3}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Trends in {area}
                    </Typography>
                    
                    <Divider sx={{ mb: 2 }} />
                    
                    {areaTopics && areaTopics.length > 0 ? (
                      <List>
                        {areaTopics.map((topic, index) => (
                          <ListItem key={index} alignItems="flex-start">
                            <ListItemIcon>
                              <TrendingUpIcon color="primary" />
                            </ListItemIcon>
                            <ListItemText 
                              primary={topic}
                            />
                          </ListItem>
                        ))}
                      </List>
                    ) : (
                      <Typography variant="body2">
                        No trending topics found for this research area.
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))
          ) : (
            <Grid item xs={12}>
              <Alert severity="info">
                No trends available for the selected research area. Try another area or check back later.
              </Alert>
            </Grid>
          )}
        </Grid>
      )}

      {/* Explanation Section */}
      <Box sx={{ mt: 6 }}>
        <Typography variant="h6" gutterBottom>
          About Trending Topics
        </Typography>
        <Typography variant="body2" paragraph>
          Trending topics are identified by analyzing recent research papers and conferences in each field.
          Our AI assistant evaluates publication patterns, citation counts, and emerging themes to identify
          the most active areas of research.
        </Typography>
        <Typography variant="body2">
          These trends can help researchers identify promising areas for their work,
          understand shifts in research focus, and discover potential collaboration opportunities.
        </Typography>
      </Box>
    </Container>
  );
}

export default Trends; 