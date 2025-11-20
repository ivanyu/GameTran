<p align="center"><img src="assets/icon_big.png" /></p>

# <p align="center">GameTran</p>
<p align="center">Your language assistant in computer games.</p>
<p align="center"><img src="docs/readme_img1.jpg" width="1024" /></p>

GameTran allows you to:
1. **Pause a game** (including "unpausable" cut scenes).
2. **Select words and phrases** to get their translation or ChatGPT explanation, open a dictionary.

The app uses Cloud Vision API for text detection and recognition and Google Cloud Natural Language API for linguistic analysis. For these, you need to provide the API key. Don't worry, it's not difficult and in most cases will cost you nothing. [How to create an API key](docs/api_key.md).

## How to use it

1. Press the hot key to pause the game and open the GameTran overlay.
2. Click and hold the left mouse button to select words.
3. Press `T` or the translate button on the toolbar to get access to linguistic analysis, translations, dictionaries.
4. Words are clickable, you can open dictionaries for them.
5. Press `Esc`, or the resume button on the toolbar, or the hot key (works even when GameTran is not in the foreground) to unpause the game and continue playing.

The default hot key is `Alt+x`, but you can configure it.

## Compatibility

Tested on Windows and Linux with X11 on x64. MacOS and Wayland will be supported later.

## Development

On both Linux and Windows, you need [uv](https://docs.astral.sh/uv/).

On Windows, install `make` and `7zip`, for example, with [Chocolatey](https://chocolatey.org/).

## License

GNU General Public License, version 3.

### Button icons

[Fluent System Icons](https://github.com/microsoft/fluentui-system-icons). Licensed under the MIT license.

## Acknowledgements

- [Universal Pause Button](https://github.com/ryanries/UniversalPauseButton) for the idea of "universal pause".
