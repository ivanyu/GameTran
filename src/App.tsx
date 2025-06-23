import './App.css';
import {
    Link,
    Spinner,
    Toast,
    Toaster,
    ToastFooter,
    ToastTitle,
    useId,
    useToastController
} from "@fluentui/react-components";
import {useCallback, useEffect, useRef} from "react";
import {OcrResponse} from "./ocr.ts";

interface AppProps {
    screenshotUrl: string | undefined;
    ocrResult: OcrResponse | undefined;
    loadingError: string | undefined;
}

function App({screenshotUrl, ocrResult, loadingError}: AppProps) {
    const initialMountMade = useRef(false);

    const toasterId = useId("toaster");
    const {dismissToast, dispatchToast, updateToast} = useToastController(toasterId);
    const loadingToastId = useId("toast-loading");

    const resumeGame = useCallback(() => {
        // const appWebview = getCurrentWebviewWindow();
        // appWebview.emit('resume_requested');
    }, []);

    useEffect(() => {
        const toastFooter = <ToastFooter>
            <Link onClick={resumeGame}>Close and resume game</Link>
        </ToastFooter>;
        if (!initialMountMade.current) {
            initialMountMade.current = true;

            dispatchToast(
                <Toast>
                    <ToastTitle media={<Spinner size="tiny"/>}>Taking screenshot</ToastTitle>
                    {toastFooter}
                </Toast>,
                {toastId: loadingToastId, timeout: -1, position: "top"}
            );
        }

        if (loadingError) {
            updateToast({
                toastId: loadingToastId,
                content: <Toast>
                    <ToastTitle>{loadingError}</ToastTitle>
                    {toastFooter}
                </Toast>,
                intent: 'error'
            });
        } else if (!screenshotUrl) {
            updateToast({
                toastId: loadingToastId,
                content: <Toast>
                    <ToastTitle media={<Spinner size="tiny"/>}>Taking screenshot</ToastTitle>
                    {toastFooter}
                </Toast>,
            });
        } else if (!ocrResult) {
            updateToast({
                toastId: loadingToastId,
                content: <Toast>
                    <ToastTitle media={<Spinner size="tiny"/>}>Running OCR</ToastTitle>
                    {toastFooter}
                </Toast>,
            });
        } else {
            dismissToast(loadingToastId);
        }
    }, [screenshotUrl, ocrResult, loadingError]);

    const screenshot = screenshotUrl
        ? <img src={screenshotUrl} />
        : <></>;

    return (<>
        <Toaster toasterId={toasterId}/>
        {screenshot}
    </>);
}

export default App;
