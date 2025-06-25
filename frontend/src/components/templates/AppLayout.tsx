// Main application layout template

import React from 'react';
import {
  Box,
  AppBar,
  Toolbar,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  IconButton,
  useMediaQuery,
  useTheme,
  Divider,
  Avatar,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard,
  Storage,
  Analytics,
  Lightbulb,
  BarChart,
  Extension,
  Settings,
  AccountCircle,
  Brightness4,
  Brightness7,
} from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '@/store';
import { setSidebarOpen, toggleThemeMode } from '@/store/slices/uiSlice';

interface AppLayoutProps {
  children: React.ReactNode;
}

// Navigation items configuration
const navigationItems = [
  { id: 'dashboard', label: 'Dashboard', path: '/dashboard', icon: Dashboard },
  { id: 'data', label: 'Data Management', path: '/data', icon: Storage },
  { id: 'analysis', label: 'Analysis', path: '/analysis', icon: Analytics },
  { id: 'insights', label: 'Insights', path: '/insights', icon: Lightbulb },
  { id: 'visualizations', label: 'Visualizations', path: '/visualizations', icon: BarChart },
  { id: 'plugins', label: 'Plugins', path: '/plugins', icon: Extension },
  { id: 'settings', label: 'Settings', path: '/settings', icon: Settings },
];

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { layout, theme: themeConfig } = useSelector((state: RootState) => state.ui);
  
  const [profileMenuAnchor, setProfileMenuAnchor] = React.useState<null | HTMLElement>(null);

  // Auto-adjust sidebar for mobile
  React.useEffect(() => {
    if (isMobile && layout.sidebar.open && layout.sidebar.variant === 'permanent') {
      dispatch(setSidebarOpen(false));
    }
  }, [isMobile, layout.sidebar.open, layout.sidebar.variant, dispatch]);

  const handleDrawerToggle = () => {
    dispatch(setSidebarOpen(!layout.sidebar.open));
  };

  const handleNavigation = (path: string) => {
    navigate(path);
    // Close drawer on mobile after navigation
    if (isMobile) {
      dispatch(setSidebarOpen(false));
    }
  };

  const handleThemeToggle = () => {
    dispatch(toggleThemeMode());
  };

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setProfileMenuAnchor(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setProfileMenuAnchor(null);
  };

  const drawerWidth = layout.sidebar.width;

  // Sidebar content
  const sidebarContent = (
    <Box sx={{ overflow: 'auto', height: '100%' }}>
      {/* Logo/Brand */}
      <Box
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          borderBottom: 1,
          borderColor: 'divider',
        }}
      >
        <Avatar
          sx={{
            bgcolor: 'primary.main',
            width: 32,
            height: 32,
          }}
        >
          <Analytics />
        </Avatar>
        <Typography variant="h6" noWrap component="div">
          Forex Analyzer
        </Typography>
      </Box>

      {/* Navigation */}
      <List sx={{ pt: 1 }}>
        {navigationItems.map((item) => {
          const Icon = item.icon;
          const isSelected = location.pathname === item.path;

          return (
            <ListItemButton
              key={item.id}
              selected={isSelected}
              onClick={() => handleNavigation(item.path)}
              sx={{
                mx: 1,
                mb: 0.5,
                borderRadius: 1,
              }}
            >
              <ListItemIcon>
                <Icon />
              </ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          );
        })}
      </List>

      {/* Footer */}
      <Box
        sx={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          p: 2,
          borderTop: 1,
          borderColor: 'divider',
        }}
      >
        <Typography variant="caption" color="text.secondary" align="center">
          v1.0.0 - Modular Platform
        </Typography>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          width: { md: `calc(100% - ${layout.sidebar.open ? drawerWidth : 0}px)` },
          ml: { md: layout.sidebar.open ? `${drawerWidth}px` : 0 },
          transition: theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        <Toolbar>
          {/* Menu button */}
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>

          {/* Page title */}
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {navigationItems.find(item => item.path === location.pathname)?.label || 'Forex Analyzer'}
          </Typography>

          {/* Theme toggle */}
          <IconButton onClick={handleThemeToggle} color="inherit">
            {themeConfig.mode === 'dark' ? <Brightness7 /> : <Brightness4 />}
          </IconButton>

          {/* Profile menu */}
          <IconButton
            onClick={handleProfileMenuOpen}
            color="inherit"
            sx={{ ml: 1 }}
          >
            <AccountCircle />
          </IconButton>
          
          <Menu
            anchorEl={profileMenuAnchor}
            open={Boolean(profileMenuAnchor)}
            onClose={handleProfileMenuClose}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'right',
            }}
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
          >
            <MenuItem onClick={handleProfileMenuClose}>Profile</MenuItem>
            <MenuItem onClick={handleProfileMenuClose}>Account</MenuItem>
            <Divider />
            <MenuItem onClick={handleProfileMenuClose}>Logout</MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      {/* Sidebar */}
      <Box
        component="nav"
        sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
      >
        <Drawer
          variant={isMobile ? 'temporary' : 'persistent'}
          open={layout.sidebar.open}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile
          }}
          sx={{
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              position: 'relative',
            },
          }}
        >
          {sidebarContent}
        </Drawer>
      </Box>

      {/* Main content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { md: `calc(100% - ${layout.sidebar.open ? drawerWidth : 0}px)` },
          minHeight: '100vh',
          transition: theme.transitions.create('width', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        {/* Toolbar spacer */}
        <Toolbar />
        
        {/* Page content */}
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default AppLayout;