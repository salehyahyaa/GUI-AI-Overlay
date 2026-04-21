# GUI AI Overlay

Racycast inspired macOS overlay triggered by global hotkey that provides an instant AI interface to eliminate context switching/searching and accelerate research.


## Motivation
Over the years I noticed the keyboard is in most cases faster than a mouse. I found it repetitive to need to exit out a tab to search something or even ask AI. Now instead of using your mouse to enter a new tab or switch windows, this process is much more snappier. By pressing <cmd+shift+space>, the GUI pops up where you can paste or type a prompt and immediately get a response. You can copy it and press <cmd+w> to close it, all without breaking your flow.  


## IMPORTANT
You can fully customize the hotkey. It does not need to be <cmd+shift+space>. See the Hotkey Customization section below.  


## Overview
This project runs as a lightweight macOS accessory application. It listens for a global hotkey and toggles a floating overlay panel. The user enters a query, which is sent to an LLM asynchronously, and the response is rendered directly in the UI.  


## Features
- Global hotkey activation  
- Floating always-on-top overlay panel  
- Asynchronous LLM requests with non-blocking UI  
- Instant response rendering  
- Minimal system footprint (no dock icon)  


## Project Structure
```
GUI-AI-Overlay/
├── src/
│   ├── GUI/
│   │   └── overlay.py
│   ├── LLM/
│   │   ├── client.py
│   │   ├── settings.py
│   │   └── prompts.py
│   ├── core/
│   │   └── customKey.py
│   └── main.py
├── .gitignore
├── README.md
├── LICENSE
├── requirements.txt
├── .env
```


## Installation
Clone the repository:
```
git clone https://github.com/salehyahyaa/GUI-AI-Overlay.git
cd GUI-AI-Overlay
```

Create your virtual environment:
```
python3 -m venv venv
```

Activate the virtual environment:
```
source venv/bin/activate
```

Install dependencies:
```
pip install -r requirements.txt
```

Create a `.env` file in the root directory:
```
OPENAI_API_KEY=your_api_key_here
```

To get your OpenAI API key:
- Go to https://platform.openai.com  
- Sign in or create an account  
- Navigate to API Keys  
- Generate a new key and paste it into your `.env` file  

Modify system prompts in:
```
src/LLM/prompts.py
```
to control how the model responds.  


## Flow
1. User presses the global hotkey  
2. Overlay appears centered on screen  
3. User enters a query  
4. Request is sent to the LLM in the background  
5. Response is rendered in the overlay  


## Usage
Run the application:
```
python src/main.py
```

Press:
```
<cmd+shift+space>
```
to toggle the overlay.  


## Hotkey Customization
Open:
```
src/core/customKey.py
```

Modify this line:
```
keyboard.HotKey.parse('<cmd>+<shift>+<space>')
```

Replace it with your desired key combination.  


## Acknowledgments
- Built using PyObjC for macOS UI  
- Uses OpenAI for language model interaction  
- Inspired by Raycast’s workflow