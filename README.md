# Fritzing-Schematic-an-Inkscape-Extension.

An Inkscape extension to help automate the creation of schematic symbols for use with Fritzing EDA software. 
Requires Inkscape v1.0 or above.

## Installation:
Copy the two files, ‘fritzing-schematic.inx’ and ‘fritzing-schematic.py’ to Inkscape’s extensions directory. Please search how to install an Inkscape extension for your OS, it's a simple process.

## Usage:
Create a new Inkscape document. The extension is launched from Inkscape ‘Extensions’ menu as ‘Fritzing’ → ‘Fritzing-Schematic…’. Upon launching the extension, you will be presented a new window with various user settings.

### User Inputs:
The ‘Schematic Symbol’ tab allows the user to enter the size of the symbol (in inches) and the label for the symbol.

The ‘Schematic Connectors’ tab has 3 groups of settings relating to the schematic symbol’s connectors.

Schematic diagram connectors: This is where the number of connectors for each	side of the symbol is set.

Connector Pin Number/Label options: This controls how the schematic pin numbers and labels are created.

Pin Numbering: has two options – Sequential or User Defined. 
	- Sequential pin numbering starts at the top-most left side connector, and increases pin numbering of each pin in a counterclockwise direction.
	- User Defined pin numbering is for manually entering pin numbers. This	option will open additional UI windows for manually assigning pin numbers.

		Pin Labels: has two options – Generic or User Defined.
		- Generic pin labels creates a pin label of ‘pin’ + the pin number. (pin1, pin2, pin3, etc)
		- User Defined pin labels is for manually entering pin labels. This option
		will open additional UI windows for manually entering pin labels.

  Connector terminalIDs: Creates connector terminal points at the outer edge
	of each connector pin.

Clicking the ‘Apply’ button will start the extension. If a ‘user defined’ option was selected, additional windows will open for user input of values. When all user input is completed, the schematic symbol is created. From here, further user artwork can be created...

The resulting Inkscape document should be saved as a plain SVG file.  To do this, from Inkscape’s file menu, choose ‘Save As…’ option. Once the filename is set, the ‘Save as type’ option needs to be set to ‘plain SVG’ to save the file without extra Inkscape data.



