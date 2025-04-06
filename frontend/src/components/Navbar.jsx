import { useState } from 'react';
import { Link } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Button, IconButton, Box, Drawer, List, ListItem, ListItemText, Switch, FormControlLabel } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';

function Navbar({ darkMode, toggleDarkMode }) {
  const [drawerOpen, setDrawerOpen] = useState(false);

  const navLinks = [
    { name: 'Home', path: '/' },
    { name: 'Conferences', path: '/conferences' },
    { name: 'Papers', path: '/papers' },
    { name: 'Trends', path: '/trends' },
    { name: 'Query', path: '/query' }
  ];

  const toggleDrawer = (open) => (event) => {
    if (event.type === 'keydown' && (event.key === 'Tab' || event.key === 'Shift')) {
      return;
    }
    setDrawerOpen(open);
  };

  return (
    <AppBar position="static" color="default" style={{ backgroundColor: darkMode ? '#1A1A1A' : '#FFF' }}>
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1, color: darkMode ? '#FFF' : '#333' }}>
          Conference Monitor
        </Typography>
        
        {/* Desktop nav links */}
        <Box sx={{ display: { xs: 'none', md: 'flex' } }}>
          {navLinks.map((link) => (
            <Button 
              key={link.name} 
              component={Link} 
              to={link.path} 
              sx={{ color: darkMode ? '#FFF' : '#333', mx: 1 }}
            >
              {link.name}
            </Button>
          ))}
          
          {/* Dark mode toggle for desktop */}
          <IconButton onClick={toggleDarkMode} sx={{ ml: 2 }}>
            {darkMode ? <Brightness7Icon /> : <Brightness4Icon />}
          </IconButton>
        </Box>
        
        {/* Mobile menu icon */}
        <Box sx={{ display: { xs: 'flex', md: 'none' } }}>
          <IconButton onClick={toggleDrawer(true)} sx={{ color: darkMode ? '#FFF' : '#333' }}>
            <MenuIcon />
          </IconButton>
        </Box>

        {/* Mobile drawer */}
        <Drawer
          anchor="right"
          open={drawerOpen}
          onClose={toggleDrawer(false)}
          PaperProps={{
            sx: {
              backgroundColor: darkMode ? '#1A1A1A' : '#FFF',
              color: darkMode ? '#FFF' : '#333'
            }
          }}
        >
          <Box
            sx={{ width: 250 }}
            role="presentation"
            onClick={toggleDrawer(false)}
            onKeyDown={toggleDrawer(false)}
          >
            <List>
              {navLinks.map((link) => (
                <ListItem button key={link.name} component={Link} to={link.path}>
                  <ListItemText primary={link.name} />
                </ListItem>
              ))}
              <ListItem>
                <FormControlLabel
                  control={
                    <Switch 
                      checked={darkMode} 
                      onChange={toggleDarkMode} 
                      color="primary" 
                    />
                  }
                  label="Dark Mode"
                />
              </ListItem>
            </List>
          </Box>
        </Drawer>
      </Toolbar>
    </AppBar>
  );
}

export default Navbar; 