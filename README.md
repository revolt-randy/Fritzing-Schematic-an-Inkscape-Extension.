# Fritzing-Schematic-an-Inkscape-Extension.

An Inkscape extension to help automate the creation of schematic symbols for use with Fritzing EDA software.  This extension will create a rectangular schematic symbol with user specified number of connectors per side of the symbol. Once finished, the resulting .SVG will have the correct scale, element hierarchy/attributes, and naming covnetions required for use in Fritzing.

All connectors created will be correctly named ‘connectorXpin’, where ‘X’ is the schematic connector number – 1. So schematic pin #1 will be named ‘connector0pin’, and schematic pin #5 will be named ‘connector4pin’. Optionally created terminalId’s will follow the same naming convention and be named ‘connector0terminal’ and ‘connector4terminal’. 

Requires Inkscape v1.2 or above.

## Downloading:
Look above for the green button labeled - 'Code'. Selecting that button will bring up a popup menu with an option - 'Download ZIP', selecting that option will start a download of a .zip file that contains all three files in this repository. 

## Installation:
The .zip file will contain two files, ‘fritzing-schematic.inx’ and ‘fritzing-schematic.py’. These files need to be copied to Inkscape’s extensions directory. Please search how to install an Inkscape extension for your OS, it's a simple process. Alternatively, if you know where Inkscape's externsions directory is, you could un-zip all files to this directory.

## Usage:
Create a new Inkscape document. The extension is launched from Inkscape ‘Extensions’ menu as ‘Fritzing’ → ‘Fritzing-Schematic…’. Upon launching the extension, you will be presented a new window with various user settings.

### User Inputs:
The **Schematic Symbol** tab allows the user to enter the size of the symbol (in inches) and the label for the symbol.

The **Schematic Connectors** tab has 3 groups of settings relating to the schematic symbol’s connectors.

- Schematic diagram connectors: Defines number of connectors for each side of the symbol is set.

- Connector Pin Number/Label options: Controls how the schematic pin numbers and labels are created.
  - Sequential pin numbering starts at the top-most left side connector, and increases pin numbering of each pin in a counterclockwise direction.
  - Generic pin labels creates a pin label of ‘pin’ + the pin number. (pin1, pin2, pin3, etc)
  - User Defined pin numbers/labels is for manually entering pin numbers/labels. 

- Connector terminalIDs: Creates connector terminal points at the outer edge of each connector pin.


Clicking the **Apply** button will start the extension. If a ‘user defined’ option was selected, additional windows will open for user input of values. Once finished, a schematic symbol is created. From here, the symbol can be further refined as desired in Inkscape... 

The resulting Inkscape document should be saved as a plain SVG file.  To do this, from Inkscape’s file menu, choose ‘Save As…’ option. Once the filename is set, the ‘Save as type’ option needs to be set to ‘plain SVG’ to save the file without extra Inkscape data.



