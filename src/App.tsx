import './App.css';

interface AppProps {
    screenshotUrl: string;
}

function App({screenshotUrl}: AppProps) {
    return (<img src={screenshotUrl} />);
}

export default App;
