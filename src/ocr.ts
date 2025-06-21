interface Vertex {
    x: number;
    y: number;
}

interface Word {
    id: number;
    text: string;
    boundingBox: Vertex[];
}

interface OcrResponse {
    detectedLanguage: string;
    words: Word[];
}

async function getOcr(ocrImageBase64: string, googleCloudAPIKey: string): Promise<OcrResponse | undefined> {
    const response = await fetch("https://vision.googleapis.com/v1/images:annotate", {
        method: "POST",
        headers: {
            "X-goog-api-key": googleCloudAPIKey,
            "Content-Type": "application/json; charset=utf-8",
        },
        body: JSON.stringify({
            "requests": [
                {
                    "image": {
                        "content": ocrImageBase64
                    },
                    "features": {
                        "type": "TEXT_DETECTION"
                    }
                }
            ]
        }),
    });

    // TODO handle HTTP errors (including key error)

    const responseBody = await response.json();
    if (!responseBody['responses']) {
        return undefined;
    }

    const firstResponse = responseBody['responses'][0];
    const fullTextAnnotations = firstResponse['fullTextAnnotation'];
    if (!fullTextAnnotations || !fullTextAnnotations['pages']) {
        return undefined;
    }

    const page = fullTextAnnotations['pages'][0];

    const detectedLanguages = page['property']['detectedLanguages'];
    if (!detectedLanguages) {
        return undefined;
    }
    detectedLanguages.sort((l1: any, l2: any) => l1 - l2);
    const languageCode = detectedLanguages[0]['languageCode'];

    const result: OcrResponse = {
        detectedLanguage: languageCode,
        words: []
    };
    let wordId = 0;
    for (const block of page['blocks']) {
        if (block['blockType'] !== 'TEXT' && block['blockType'] !== 'TABLE') {
            continue;
        }

        for (const paragraph of block['paragraphs']) {
            for (const wordJson of paragraph['words']) {
                const word: Word = {
                    id: wordId++,
                    text: wordJson['symbols'].map((s: any) => s['text']).join(''),
                    boundingBox: JSON.parse(JSON.stringify(wordJson['boundingBox']['vertices']))
                };
                result.words.push(word);
            }
        }
    }

    return result;
}

export default getOcr;
export type {OcrResponse, Word, Vertex};
