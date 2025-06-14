declare module 'react-native-background-timer' {
  interface BackgroundTimer {
    setInterval(callback: () => void, delay: number): any;
    clearInterval(intervalId: any): void;
    setTimeout(callback: () => void, delay: number): any;
    clearTimeout(timeoutId: any): void;
  }
  const BackgroundTimer: BackgroundTimer;
  export default BackgroundTimer;
}
