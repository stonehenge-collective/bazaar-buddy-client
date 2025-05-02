# Motivation for Bazaar Buddy
I got tired of alt-tabbing to howbazaar to look up item upgrades and enchants and monster health, boards, and skills over and over every run.

# What Bazaar Buddy does
When you hover over an item, event, or monster in game, Bazaar Buddy shows you information about what you're hovering, including item upgrade paths and enchantment effects, event options, and monster health, boards, and skills - all the information you could get from howbazaar, mobalytics, or the wiki. It's completely free and open source, runs entirely locally, does not require an account, and collects no data.

# How to get Bazaar Buddy
Bazaar Buddy's source code is hosted on a public GitHub repository, which includes instructions on how to run it: <https://github.com/stonehenge-collective/bazaar-buddy-client>. We also have a Discord server for support and feature suggestions: <https://discord.gg/xyakvUqN>.

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
