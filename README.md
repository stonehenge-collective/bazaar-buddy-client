# Motivation for Bazaar Buddy
I got tired of alt-tabbing to howbazaar to look up item upgrades and enchants and monster health, boards, and skills over and over every run.

# What Bazaar Buddy does
When you hover over an item, event, or monster in game, Bazaar Buddy shows you information about what you're hovering, including item upgrade paths and enchantment effects, event options, and monster health, boards, and skills - all the information you could get from howbazaar, mobalytics, or the wiki. It's completely free and open source, runs entirely locally, does not require an account, and collects no data.

# How to use Bazaar Buddy

There are **two** supported ways to get Bazaar Buddy running on your machine. Choose the one that suits you best.

---

## 1. Download a Pre-built Release (No Coding Required)

|            | **Windows** | **macOS** |
|------------|-------------|-----------|
| **Download** | 1. Visit the project’s [GitHub Releases](https://github.com/stonehenge-collective/bazaar-buddy-client/releases) page. 2. Grab the latest `BazaarBuddy.exe`. | 1. Visit the [GitHub Releases](https://github.com/stonehenge-collective/bazaar-buddy-client/releases) page. 2. Download `BazaarBuddy-mac.zip` and unzip it (you’ll get `BazaarBuddy.app`). |
| **First-run (unsigned binary)** | 1. Double-click the downloaded `.exe`. 2. Windows SmartScreen will pop up → click **“More info”** → **“Run anyway.”** 3. If Windows still blocks it, right-click the file → **Properties** → check **“Unblock,”** then run it again. | 1. Move `BazaarBuddy.app` to **Applications** (optional, but tidy). 2. Control-click **BazaarBuddy.app** → **Open**. Gatekeeper warns it’s from an unidentified developer → click **Open**. macOS remembers your choice; future launches work normally. |
| **That’s it!** | A Bazaar Buddy icon appears in your taskbar/system-tray. Hover an item in-game and watch the overlay pop up. | The app’s icon shows up in the Dock and menu bar. Hover an item in-game to see the overlay. |

---

## 2. Run from Source (For Developers & Power Users)

> **Why run from source?**  
> • You want to help develop Bazaar Buddy  
> • You don’t trust unsigned binaries  
> • You prefer using the very latest commit

### Prerequisites

* **Git** installed (or just download the ZIP of the repo)  
* **Python 3.13**
* Ability to install/compile Python packages  

> **Tip:** On macOS, install Python via `brew install python@3.13`.  
> On Windows, grab the official installer from https://www.python.org/downloads/release/python-3133/ and **check “Add python.exe to PATH.”**

### Step-by-step

|            | **Windows** | **macOS / Linux** |
|------------|-------------|-------------------|
| **Clone & enter repo** | powershell:```git clone https://github.com/stonehenge-collective/bazaar-buddy-client.git; cd bazaar-buddy-client``` | bash:```git clone https://github.com/stonehenge-collective/bazaar-buddy-client.git && cd bazaar-buddy-client``` |
| **Create & activate virtual env (recommended)** | ```python -m venv venv; Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force; .\venv\Scripts\activate``` | ```python3 -m venv venv && source venv/bin/activate``` |
| **Install dependencies** | ```pip install -r windows_requirements.txt``` | ```pip install -r mac_requirements.txt``` |
| **Run Bazaar Buddy** | ```python main.py``` | ```python main.py``` |

The overlay window will launch; keep it running while you play **The Bazaar**.

### Security prompts when running from source

* **Windows:** You may get a “Windows Defender SmartScreen” prompt for Python on first launch—choose **“Run anyway.”**
* **macOS:** The first time you run `python main.py`, macOS may warn that “python” was downloaded from the internet. Go to **System Settings → Privacy & Security** and click **“Allow Anyway.”** Re-run the command.

## Having Trouble or want to contribute?

* **Join our Discord:** <https://discord.gg/xyakvUqN> – we’re happy to help!  

# How Bazaar Buddy works
Bazaar Buddy takes screenshots of The Bazaar's window, uses AI to extract text from those screenshots, looks that text up in a list of Bazaar terms, and displays information about what it finds in a window on your screen.

# What Bazaar Buddy doesn't do
## Mod the game
Bazaar Buddy interacts with the game ONLY via screenshots of The Bazaar's window. It does not modify The Bazaar at all, intercept network traffic, or inspect or modify private log files. It only looks at the same thing you do: The Bazaar's display.

## Look at other windows on your computer
Bazaar Buddy only captures screenshots of The Bazaar; it doesn't look at any other windows on your computer. Bazaar Buddy will _never_ be able to see passwords or other sensitive information on your screen.

## Give a competitive advantage
Bazaar Buddy shows only free, publicly available Bazaar data, which most players are already getting from howbazaar. It doesn't simulate battles, predict whether you'll beat a monster, or give any player/run specific information.

## Leave your computer at all
Bazaar Buddy runs entirely locally. It doesn't make any network calls or otherwise use the internet.

# FAQ
## Will I get banned for using Bazaar Buddy?
Bazaar Buddy makes it easier to do something you're already doing: reading text on your screen, looking it up on howbazaar, and reading the description. It doesn't mod The Bazaar or interact with it in any way other than reading its screen. It doesn't give any competitive advantage outside of what howbazaar is already providing. It only does things you're already allowed to do with your computer: look at the screen, read text off of it, and look that text up. 

There's no way Reynad could know that you're using Bazaar Buddy, because it operates entirely outside of The Bazaar. Bazaar Buddy uses only free, publicly available Bazaar data, gathered from public websites like <https://www.howbazaar.gg/>, <https://mobalytics.gg/the-bazaar/>, and <https://thebazaar.wiki.gg/>.

## What's the long term plan for Bazaar Buddy?
If Reynad doesn't immediately shut us down, we plan to collect statistics on how player choices correlate with outcomes and then to sell access to advanced statistics via a subscription model. We will never offer features which provide an in-game advantage, like simulated monster fights or board arrangement optimizers. We will make it very clear if/when we add data collection to the client, and there will always be an open source option which does not collect any data.
