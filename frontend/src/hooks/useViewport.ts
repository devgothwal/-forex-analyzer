// Viewport and responsive hooks

import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { setViewport, setIsMobile } from '@/store/slices/uiSlice';
import { RootState } from '@/store';

// Hook to handle viewport resize events
export const useViewportResize = () => {
  const dispatch = useDispatch();

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      const isMobile = width < 768;

      dispatch(setViewport({ width, height }));
      dispatch(setIsMobile(isMobile));
    };

    // Set initial values
    handleResize();

    // Add event listener
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [dispatch]);
};

// Hook to get current viewport information
export const useViewport = () => {
  const viewport = useSelector((state: RootState) => ({
    width: state.ui.viewport.width,
    height: state.ui.viewport.height,
    isMobile: state.ui.isMobile,
    isTablet: state.ui.viewport.width >= 768 && state.ui.viewport.width < 1024,
    isDesktop: state.ui.viewport.width >= 1024,
  }));

  return viewport;
};

// Hook for responsive breakpoints
export const useBreakpoints = () => {
  const viewport = useViewport();

  return {
    xs: viewport.width < 600,
    sm: viewport.width >= 600 && viewport.width < 960,
    md: viewport.width >= 960 && viewport.width < 1280,
    lg: viewport.width >= 1280 && viewport.width < 1920,
    xl: viewport.width >= 1920,
    isMobile: viewport.isMobile,
    isTablet: viewport.isTablet,
    isDesktop: viewport.isDesktop,
  };
};