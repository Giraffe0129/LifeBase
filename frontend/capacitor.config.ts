import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.myawesomeapp.mobile',
  appName: 'My Awesome App',
  webDir: 'dist',
  server: {
    androidScheme: 'http',
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      backgroundColor: '#6366f1',
      androidScaleType: 'CENTER_CROP',
    },
    StatusBar: {
      style: 'DARK',
      backgroundColor: '#6366f1',
    },
  },
  android: {
    webContentsDebuggingEnabled: true,
  },
};

export default config;
