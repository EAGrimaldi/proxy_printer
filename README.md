# proxy_printer
 
A tool for quickly printing cost-effective proxies of Magic The Gathering cards in bulk. Intended for use in only in unsanctioned settings, such as "kitchen table magic" or private testing.

Takes as input a single user specified file listing the desired proxies. Produces as output a single `.pdf` file containing images of the desired proxies. Images in the output file are tiled in order to minimally waste paper.

# input format (basic details)

The input file should be a `.txt` file.

The tool should be compatible with deck list formats typically used by MTGA, MTGO, MTGGoldfish, Moxfield, etc.

Each line should contain a single card name, optionally preceded by a desired number of copies. ***Do not include set codes or collector numbers at this time.***

Input card names must ***exactly match official card names***. Official card names are available in the official [Gatherer](https://gatherer.wizards.com/Pages/Default.aspx) database or the third-party [Scryfall](https://scryfall.com/) database (which also provides excellent search tools).

Double Faced Cards must be written as either `Front Face // Back Face` or simply `Front Face`. Do not write separate entries for the back faces of DFCs, the tool automatically generates proxies for both faces of DFCs.

As an example, these blocks are equivalent:

```
Delver of Secrets // Insectile Aberration
Delver of Secrets // Insectile Aberration
Delver of Secrets // Insectile Aberration
Delver of Secrets // Insectile Aberration
```

```
4 Delver of Secrets
```

Finally, the tool automatically ignores a small number of terms commonly included in automatically generated deck list files. Stuff like `Main Deck`, `Sideboard`, `Commander`, `Companion`, etc.

# TODO

- implement black-and-white printer-friendly "simplified" card mode (the whole reason I wanted to make this tool to begin with lol)
- implement support for MTGO deck files as input 
- implement artwork selection via set codes and collector numbers.
