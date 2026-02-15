# Guitar Pedal

A digital guitar effects pedal built with a Raspberry Pi 4 and an Electrosmith Daisy. The Pi handles the UI and controls via a 3.5" touchscreen LCD, while the Daisy handles real-time audio DSP.

## Hardware

- Raspberry Pi 4 (4GB)
- Electrosmith Daisy (audio DSP)
- MHS35 3.5" GPIO touchscreen (480x320)
- USB to SATA adapter (for SSD boot, optional)

## Features

### Implemented
- **Idle Screen** - Animated waveform display with floating particles and pulsing title
- **Touch Menu** - Scrollable menu with tap selection
- **Spotify Integration** - Now playing screen with album art, track info, progress bar, and playback controls (play/pause, skip, previous)
- **Visualiser** - Split-screen oscilloscope showing input signal (blue) and effect chain output (green) as real-time waveforms
- **Mock Signal** - 440Hz sine wave generator for testing without Daisy hardware
- **Effect Chain** - Passthrough skeleton that effects will plug into
- **Auto-start** - App launches automatically on boot

### Planned
- **Effects** - Select and configure individual effects (overdrive, delay, reverb, chorus, fuzz)
- **Tuner** - Built-in chromatic guitar tuner
- **Presets** - Save and load effect configurations
- **MIDI Support** - Control effects via MIDI foot controller

## Project Structure

```
guitar-pedal/
├── pi/                          # Python - Raspberry Pi UI
│   ├── main.py                  # App entry point and main loop
│   ├── .env                     # Spotify credentials (not in git)
│   ├── spotify_auth.py          # Spotify login helper script
│   ├── ui/
│   │   ├── idle_screen.py       # Idle waveform animation
│   │   ├── menu.py              # Main menu with touch support
│   │   ├── spotify_screen.py    # Spotify now playing screen
│   │   ├── visualiser.py        # Split-screen signal oscilloscope
│   │   ├── tuner.py             # Tuner display (planned)
│   │   └── parameter_control.py # Effect parameter UI (planned)
│   ├── effects/
│   │   ├── effect_chain.py      # Ordered effect processing pipeline
│   │   └── presets.py           # Preset save/load (planned)
│   ├── comms/
│   │   ├── spotify_client.py    # Spotify API client
│   │   ├── mock_signal.py       # Fake signal source for testing
│   │   └── serial_comms.py      # Pi <-> Daisy communication (planned)
│   └── assets/                  # Animations, icons, fonts
├── daisy/                       # C++ - Electrosmith Daisy DSP
│   ├── src/
│   │   ├── main.cpp             # Daisy entry point (planned)
│   │   ├── effects/             # Effect implementations (planned)
│   │   │   ├── overdrive.cpp/h
│   │   │   ├── delay.cpp/h
│   │   │   ├── reverb.cpp/h
│   │   │   ├── chorus.cpp/h
│   │   │   ├── fuzz.cpp/h
│   │   │   └── effect_chain.cpp/h
│   │   ├── tuner/               # Pitch detection (planned)
│   │   ├── midi/                # MIDI handler (planned)
│   │   └── comms/               # Serial comms to Pi (planned)
│   ├── lib/                     # Daisy libraries
│   └── Makefile
└── docs/
    └── wiring.md                # Wiring documentation
```

## Setup

### Prerequisites
- Raspberry Pi 4 with Raspberry Pi OS (64-bit)
- MHS35 LCD display with drivers installed
- Python 3 with pygame, numpy, spotipy, python-dotenv, requests, Pillow

### Installation

1. Clone the repo:
   ```
   git clone git@github.com:QueenEM/guitar-pedal.git
   cd guitar-pedal
   ```

2. Install Python dependencies:
   ```
   pip3 install pygame numpy spotipy python-dotenv requests Pillow
   ```

3. Create a `.env` file in the `pi/` directory:
   ```
   SPOTIFY_CLIENT_ID=your_client_id
   SPOTIFY_CLIENT_SECRET=your_client_secret
   ```

4. Authenticate Spotify:
   ```
   cd pi
   python3 spotify_auth.py
   ```
   Follow the instructions to log in via your browser.

5. Run the app:
   ```
   cd pi
   DISPLAY=:0 python3 main.py
   ```

### Auto-start on Boot
The app is configured to auto-start via `~/.config/autostart/guitar-pedal.desktop`.

## Tech Stack

- **Pi UI**: Python, pygame, numpy
- **Audio DSP**: C++, Electrosmith Daisy SDK
- **Communication**: Serial over USB (Pi <-> Daisy)
- **Spotify**: spotipy (Spotify Web API)
