# Python Battleships

## Project Overview

This project is a basic one sided battleships game in which the user competes against a computer to sink all of the computers battleships. The users score is based on how many shots it takes to sink all of the computers battle ships.

## Features

- High scores are saved to disk
- User can save and load game files
- Saved game files cannot be read by user
- Built in help screen\*
- Random placement of ships in the game board

\*Requires network connection for first use

## Supported systems

| Name       | Supported | Tested |
| ---------- | --------- | ------ |
| Windows 10 | ☑         | ☑      |
| Debian 10  | ☑         | ☑      |
| MacOS      | ☑         | ☒      |
| FreeBSD    | ☒         | ☒      |

## System requirements

- Python 3.8.0 or greater
- Python standard packages
- Working internet connection for help menu

## Troubleshooting

It is recommended that this software is run in the terminal or command line as apposed to being run in IDLE. This is due to a bug in IDLE that means that the press any key
prompt is non blocking. Running the program in IDLE also means that the clear screen function will not work as intended. To run in terminal simply enter `python battleships.py`
Note you may need to run `python3 battleships.py` on some operating systems, especially on Linux.

If you recive an error stating:

```
Creation of directory `filename` failed
Please create this directory manually and try again.
```

Then please check the file permissions for the path stated and try again. If this does not fix the issue then please create the files manually

Please note that this software has only been tested on Windows and Debian 10 (specifically Kali Linux) so there is a risk of failure on macOS machines. If this occurs then
please submit an issue.

## License

This project is licenced under the terms of the MIT license which can be found in the project root. You should have received a copy of the MIT license with this file. If not please write to [mnickson@sidingsmedia.com](mailto:mnickson@sidingsmedia.com) or visit [https://raw.githubusercontent.com/Computroniks/python-battleships/main/LICENSE](https://raw.githubusercontent.com/Computroniks/python-battleships/main/LICENSE)
