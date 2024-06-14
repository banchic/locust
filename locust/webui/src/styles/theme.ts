import { PaletteMode, createTheme as baseCreateTheme } from '@mui/material';

const createTheme = (mode: PaletteMode) =>
  baseCreateTheme({
    palette: {
      mode,
      primary: {
        main: '#0088BB',
      },
      success: {
        main: '#00BBEE',
      },
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          ':root': {
            '--footer-height': '40px',
          },
        },
      },
    },
  });

export default createTheme;
