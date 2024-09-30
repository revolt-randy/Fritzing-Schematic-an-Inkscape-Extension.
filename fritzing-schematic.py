#!/usr/bin/env python

"""
  fritzing-schematic.py v1.0 
  -for Inkscape v1.2+
    -version history at end of code
"""

"""
Copyright (c) 2024 Randy Blose

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


import sys
#sys.path.append('/usr/share/inkscape/templates') # or another path, as necessary

import inkex
#import simplestyle

from lxml import etree

import tkinter as tk
from tkinter import messagebox
from tkinter import Scrollbar
from tkinter import Canvas
from tkinter import Frame


from inkex.elements import load_svg     # is this even used?


class FritzingSchematic(inkex.EffectExtension):

    # global variables
    inch_scale_factor = 1000        # inch scaling factor - the value used to scale inch values to
                                    # match the documents scale units
    pixel_scale_factor = 10.41667   # pixel scaling factor - the value used to scale pixel values
                                    # to match the document's scale units
    # globals are frowned upon, but these were added in during dev work and just not removed,
    # they are used in very few places and could be hard coded instead

    # user inputs - from fritzing-schematic.inx
    def add_arguments(self, pars):
        #inkex.Effect.__init__(self)
        
        # x size of schematic symbol
        pars.add_argument('--x_size', 
            type = float,
            default = '0.3', 
            help = 'x size')
        
        # y size of schematic symbol
        pars.add_argument('--y_size', 
            type = float,
            default = '0.3', 
            help = 'y size')

        # Define string option - for schematic label
        pars.add_argument('--sch_label', 
            type = str,
            default = 'label',
            help = 'Schematic symbol label')
        
        # number of left side connectors
        pars.add_argument('--left_connectors', 
            type = int,
            default = '0',
            help = 'left connectors')
        
        # number of bottom side connectors
        pars.add_argument('--bottom_connectors', 
            type = int,
            default = '0',
            help = 'bottom connectors')
        
        # number of right side connectors
        pars.add_argument('--right_connectors', 
            type = int,
            default = '0',
            help = 'right connectors')
        
        # number of top side connectors
        pars.add_argument('--top_connectors', 
            type = int,
            default = '0',
            help = 'top connectors')
        
        # pin numbering
        pars.add_argument('--pin_num',
            type = int,
            default = '0',
            help = 'some help')
          
        # pin labelling
        pars.add_argument('--pin_label',
            type = int,
            default = '0',
            help = 'some help')
  
        # connector terminalIDs
        pars.add_argument('--terminal_id',
            type=inkex.Boolean,
            default = 'false',
            help = 'some help')
        
        # here so we can have tabs - but we do not use it directly - else error
        self.arg_parser.add_argument("-none", "--active-tab", 
            type= str, dest="active_tab", default='symbol', # use a legitmate default
            help="Active tab.")
    # end of - def add_arguments(self, pars):


    def effect(self):
    # actual effect starts here - this executes when extension is 'applied'
        
        # define variables/lists needed
        connector_number = 1                # connector number, used for naming connector pins
        result = True                       # error flag
        schematic_pin_num = []              # stores schematic pin numbers
        schematic_pin_label = []            # stores schematic pin labels
        x_offset = 0                        # x offset of schematic symbol from the left of page
        y_offset = 0                        # y offset of schematic symbol from top of page
        connector_pin_attrib = []           # connector pin attribute list - stores values for pin creation
        connector_term_attrib = []          # connector terminalID attribute list - stores values for terminalID creation
        
        svg = self.document.getroot()
        # Again, there are two ways to get the attibutes:
        org_doc_width  = self.svg.get('width')      # not sure what units - they are px
        org_doc_height = self.svg.attrib['height']  # size is in pixels
        #sys.stderr.write(str(org_doc_width) + "    " + str(org_doc_height) + "\n\n" )
        org_doc_viewbox = self.svg.get('viewBox')
        #sys.stderr.write(org_doc_viewbox + "\n\n")
    
        # get user input values
        schematic_width = round(self.options.x_size, 2)         # width of schematic box symbol - trim off extra decimal places
        schematic_height = round(self.options.y_size, 2)        # height of schematic box symbol - trim off extra decimal places
        label_text = self.options.sch_label                     # text for symbol label
        num_left_pins = self.options.left_connectors            # number of connectors on left side of schematic symbol
        num_bottom_pins = self.options.bottom_connectors        # number of connectors on top of schematic symbol
        num_right_pins = self.options.right_connectors          # number of connectors on right of schematic symbol
        num_top_pins = self.options.top_connectors              # number of connectors on top of schematic symbol

        # check if too many pins for size of symbol = user input error 
        result = error_check_params(schematic_width, schematic_height, num_left_pins, num_bottom_pins, num_right_pins, num_top_pins)
        
        if result is False:
            return                          # exit extension
        
        # delete current layer and create a new group named - schematic
        layer = self.svg.get_current_layer()  
        layer.delete()
        group = self.svg.get_current_layer().add(inkex.Group(id="schematic"))
        
        # set up document
        x_offset, y_offset = prep_doc(self, schematic_width, schematic_height, num_left_pins, num_bottom_pins, num_right_pins, num_top_pins)       # set document settings
        
        # create symbol
        create_rect_symbol(self, group, schematic_width, schematic_height, x_offset, y_offset)     # create rectangular symbol
        
        # create symbol label
        create_symbol_label(self, group, schematic_width, schematic_height, x_offset, y_offset, label_text)    # create the label
        
        # create left connector pins
        if num_left_pins > 0:
            # create left pins, pin numbers and pin labels
            result = create_left_pins(self,
                group,
                num_left_pins,
                schematic_width,
                schematic_height,
                x_offset,
                y_offset,
                connector_number,
                schematic_pin_num,
                schematic_pin_label,
                connector_pin_attrib,
                connector_term_attrib)
        
        if result is False:
            sys.stderr.write("\n Invalid pin number/label entry - left side\n\n")
            sys.stderr.write(" extension failed!\n")
            
            error_cleanup(self, group, org_doc_width, org_doc_height, org_doc_viewbox)      # restore inkscape settings changed
            
            return                          # exit extension
        
        connector_number =  num_left_pins + 1     # increment connector_number counter

        # create bottom connector pins
        if num_bottom_pins > 0:
            # create bottom pins, pin numbers and pin labels
            result = create_bottom_pins(self,
                group,
                num_bottom_pins,
                schematic_width,
                schematic_height,
                x_offset,
                y_offset,
                connector_number,
                schematic_pin_num,
                schematic_pin_label,
                connector_pin_attrib,
                connector_term_attrib)
        
        if result is False:
            sys.stderr.write("\n Invalid pin number/label entry - bottom side\n\n")
            sys.stderr.write(" extension failed!\n")
            
            error_cleanup(self, group, org_doc_width, org_doc_height, org_doc_viewbox)      # restore inkscape settings changed
            
            return                          # exit extension
        
        connector_number = num_left_pins + num_bottom_pins + 1      # increment connector_number counter

        # create right connector pins
        if num_right_pins > 0:
            # create right pins, pin numbers and pin labels
            result = create_right_pins(self,
                group,
                num_right_pins,
                schematic_width,
                schematic_height,
                x_offset,
                y_offset,
                connector_number,
                schematic_pin_num,
                schematic_pin_label,
                connector_pin_attrib,
                connector_term_attrib)
        
        if result is False:
            sys.stderr.write("\n Invalid pin number/label entry - right side\n\n")
            sys.stderr.write(" extension failed!\n")
            
            error_cleanup(self, group, org_doc_width, org_doc_height, org_doc_viewbox)      # restore inkscape settings changed
            
            return                          # exit extension
            
        connector_number = num_left_pins + num_bottom_pins + num_right_pins + 1      # increment connector_number counter
        
        # create top connector pins
        if num_top_pins > 0:
            # create top pins, pin numbers and pin labels
            result = create_top_pins(self,
                group,
                num_top_pins,
                schematic_width,
                schematic_height,
                x_offset,
                y_offset,
                connector_number,
                schematic_pin_num,
                schematic_pin_label,
                connector_pin_attrib,
                connector_term_attrib)
        
        if result is False:
            sys.stderr.write("\n Invalid pin number/label entry - top side\n\n")
            sys.stderr.write(" extension failed!\n")
            
            error_cleanup(self, group, org_doc_width, org_doc_height, org_doc_viewbox)      # restore inkscape settings changed
            
            return                          # exit extension

        
        # now create the actual pins in the .svg document
        for index in range(0, len(connector_pin_attrib)):
            create_pin(self, group, connector_pin_attrib[index])
            
            if self.options.terminal_id is True:
                create_terminalID(self, group, connector_term_attrib[index])


        return          # exit extension

    # end of - def effect(self):
    
# end of - class FritzingSchematic(inkex.EffectExtension):


''' functions start here: '''

def prep_doc(self, x_size, y_size, num_left_pins, num_bottom_pins, num_right_pins, num_top_pins):
# adjusts some inkscape settings to match what is needed for fritzing
# inputs:
# x_size - width of schematic symbol
# y_size - height of schematic symbol
# num_left_pins - number of pins on left side of symbol
# num_bottom_pins - number of pins on bottom side of symbol
# num_right_pins - number of pins on right side of symbol
# num_top_pins - number of pins on top side of symbol
# returns:
# x_symbol_offset - location of symbol from left side of document
# y_symbol_offset - location of symbol from top side of document
#
    
    svg = self.document.getroot()

    # calculate document width
    if num_left_pins > 0:           # check for left pins
        x_size = x_size + .105      # add to the value for space for left pins
        x_symbol_offset = 105       # space to offset the symbol from the left side of document
    else:                           # no left pins
        x_size = x_size + .005      # just add space for symbol stroke
        x_symbol_offset = 5       # offset for symbol stroke
        
    if num_right_pins > 0:          # check for right pins
        x_size = x_size + .105      # add to the value for space for right pins
    else:
        x_size = x_size + .005      # add space for symbol stroke
        
    
    viewbox_width = x_size * FritzingSchematic.inch_scale_factor  # get viewBox value
    #x_size = x_size / FritzingSchematic.pixel_scale_factor  # scale down in size to get doc width
    
    # calculate document height
    if num_bottom_pins > 0:         # check for bottom pins
        y_size = y_size + .105      # add to this value for space for the bottom pins
    else:
        y_size = y_size + .005      # no bottom pins, so just add space for stroke of symbol

    if num_top_pins > 0:            # check for top pins
        y_size = y_size + .105      # add to the value for space for the top pins
        y_symbol_offset = 105       # offset from top of document to place symbol
    else:                           # no top pins
        y_size = y_size + .005      # add a little bit of space for pin stroke
        y_symbol_offset = 5         # offset from top of document to place symbol
 
    viewbox_height = y_size * FritzingSchematic.inch_scale_factor  # get viewBox value
    
    svg.set('width', str(x_size)+'in')       # set doc width
    svg.set('height', str(y_size)+'in')      # set doc height
    
    viewbox_value = "0 0 " + str(viewbox_width) + " " + str(viewbox_height) # conver viewBox value to string
    
    svg.set('viewBox', viewbox_value)   # set viewbox value
    
    return x_symbol_offset, y_symbol_offset    
# end of - def prep_doc(self, x_size, y_size, num_left_pins, num_bottom_pins, num_right_pins, num_top_pins):
    
 
def create_rect_symbol(self, group, x_size, y_size, x_offset, y_offset):
# creates a rectanglar box for a schematic symbol
# inputs:
# group - layer (or group) to add symbol to
# x_size - width of schematic symbol
# y_size - height of schematic symbol
# x_offset - space from left edge of document to place symbol
# y_offset - space from top of document to place symbol
# returns:
# nothing
  
    x_size = x_size * FritzingSchematic.inch_scale_factor     # user input in inches, so scale in size
    symbol_width = str(x_size)              # x size of box

    y_size = y_size * FritzingSchematic.inch_scale_factor     # user input in inches, so scale in size
    symbol_height = str(y_size)             # y size of box

    svg = self.document.getroot()
    
    # get offset of where to place symbol
    x_loc = str(x_offset)
    y_loc = str(y_offset)

    # define rect attributes
    attribs = {
    'fill'              : 'none',
    'height'            : symbol_height,
    'width'             : symbol_width,
    'stroke-width'      : '10',
    'stroke'            : '#000000',
    'stroke-linejoin'   : 'round',
    'stroke-linecap'    : 'round',
    'id'                : 'symbol',
    'x'                 : x_loc,
    'y'                 : y_loc}
    
    newObj = etree.SubElement(group, inkex.addNS('rect','svg'), attribs )
    
    return 
# end of - def create_rect_symbol(self, group, x_size, y_size, x_offset, y_offset):


def create_symbol_label(self, group, x_size, y_size, x_offset, y_offset, label_name):
    # create a text label for schematic symbol
    # inputs:
    # group - the group to add the label to
    # x_size - width of schematic symbol
    # y_size - height of schematic symbol
    # x_offset - space from left edge of document to the symbol left edge
    # y_offset - space from top of document to the top of the symbol
    # label_name - name for the symbol label - user input
    # returns:
    # nothing
    #

    svg = self.document.getroot()
    
    # Create text element
    text = etree.Element(inkex.addNS('text','svg'))
    text.text = label_name

    # Set text position
    # center width is x_offset + (x_size / 2)
    x_size = x_size * FritzingSchematic.inch_scale_factor     # user input in inches, so scale in size
    center_width = str( ( ( x_size / 2 ) + x_offset) )      
    text.set('x', center_width)     
    
    
    # center height is y_offset + (y_size / 2)
    y_size = y_size * FritzingSchematic.inch_scale_factor     # user input in inches, so scale in size
    center_height = str( ( y_size / 2 ) + y_offset )       
    text.set('y', center_height)

    # Set text properties
    text.set('font-family', 'Droid Sans')
    text.set('font-size', '60')
    text.set('fill', '#000000')
    text.set('id', 'label')
    text.set('text-anchor', 'middle')

    # Connect elements together.
    group.append(text)

    return
# end of - def create_symbol_label(self, label_name):
   

def create_left_pins(self, group, num_pins, width, height, x_offset, y_offset, connect_num, schematic_pin_num, schematic_pin_label, connector_pin_attrib, connector_term_attrib):
    # create left side pins for schematic symbol
    # inputs:
    # group - the group to add the pins to
    # num_pins - number of pins to create
    # width - size of schematic width in inches - user input
    # height - size of shcematic height in inches - user input
    # x_offset - x location of schematic symbol's left side
    # y_offset - y location of schematic symbol's top side
    # connect_num - the number to start using to name connectors created
    # schematic_pin_num - user defined pin number list
    # schematic_pin_label - user defined pin label list
    # connector_pin_attrib - connector pin attributes - used later to create pins
    # connector_term_attrib - connector terminalID attributes - used to create terminalIDs
    # returns:
    # True if successful user input
    # False if failed user input
    #

    # x location of pin
    x_pos1 = x_offset               # left side of schematic symbol box
    # length of pin...
    x_pos2 = x_pos1 - 100           # should be set to 100, or 0.1 inch

    # y location of pin
    # get y location of top most possible pin position
    y_pos =  y_offset               # top of schematic symbol
    y_pos = y_pos + 100             # add 0.10 inch to position so pin isn't at top of symbol
        
    # attempt to center pin vertically - works so-so
    # determine offset from top most pin position of 
    # where the pins should start at
    temp_height = (height * 10)     # multiply by ten to go from decimal input to whole intger
    
    if num_pins < temp_height:
        temp_offset = temp_height - num_pins
        temp_offset = int((temp_offset / 2))
    else:
        temp_offset = (temp_height)
        
    y_pos = y_pos + ((temp_offset * 100 ) )    

    # check for user input
    if ((self.options.pin_num == 1) or (self.options.pin_label == 1)):           # user defined pin numbers or labels
        user_pin_number_label(self, num_pins, connect_num, schematic_pin_num, schematic_pin_label, "Left")
    
    if (self.options.pin_num == 1):                                 # user defined pin numbers
        if len(schematic_pin_num) < (connect_num - 1 + num_pins):   # check that all pin numbers were entered by user
            return bool(False)                                      # return False - an error on input
            
    else:                                                           # sequential pin numbers
        connect_number = connect_num
        for index in range(num_pins):                               # loop thru and number the pins
            schematic_pin_num.append(connect_number)
            connect_number = connect_number + 1
            
    if (self.options.pin_label == 1):                               # user defined pin labels
        if len(schematic_pin_label) < (connect_num - 1 + num_pins): # check that all pin labels were entered by user
            sys.stderr.write("length of schematic_pin_label = " + str(len( schematic_pin_label)) + "\n")
            sys.stderr.write("schematic_pin_label = " + str(schematic_pin_label) + "\n\n")
            
            return bool(False)                                      # return False - an error on input
            
    else:                                                           # sequential pin labels
        connect_number = connect_num
        for index in range(num_pins):                               # loop thru and label the pins
            schematic_pin_label.append("pin" + str(schematic_pin_num[connect_number - 1] )) # pin label should be text 'pin' + connector number of the pin
            connect_number = connect_number + 1                     # and not this sequentially counting number
    
    # end of check user input
    
    # create the pins, pin numbers, pin labels, and terminalIDs
    for index in range(connect_num, connect_num + num_pins):
        connect_num = schematic_pin_num[index - 1] - 1

        connect_name = "connector" + str(connect_num) + "pin"
        
        pin_attribs = set_pin_attribs(connect_name, x_pos1, x_pos2, y_pos, y_pos)
        
        # add pin_attribs dict to connector_pin_attrib list for pin creation later on
        connector_pin_attrib.append(pin_attribs)
        
        # create pin number/label
        create_pin_number(self, group, (connect_num + 1), x_pos1, x_pos2, y_pos, y_pos)
        create_pin_label(self, group, (schematic_pin_label[index - 1]), (connect_num + 1), x_pos1, x_pos2, y_pos, y_pos)
        
        # terminal ID creation
        if self.options.terminal_id is True:
            terminal_id_name = "connector" + str(connect_num) + "terminal"
            
            id_attribs = set_term_attribs(terminal_id_name, x_pos2 - 5, y_pos - 5)
            
            connector_term_attrib.append(id_attribs)
        
        # first pin created at starting position for pins
        # now figure out location for next pin
        y_pos = y_pos + 100

    # end of create pins, pin numbers, and pin labels
    
        
    return bool(True)
# end of - def create_left_pins(self, group, num_pins, width, height, x_offset, y_offset, connect_num, schematic_pin_num, schematic_pin_label, connector_pin_attrib, connector_term_attrib):


def create_bottom_pins(self, group, num_pins, width, height, x_offset, y_offset, connect_num, schematic_pin_num, schematic_pin_label, connector_pin_attrib, connector_term_attrib):
    # create bottom pins for schematic symbol
    # inputs:
    # group - the group to add the pins to
    # num_pins - number of pins to create
    # width - size of schematic width in inches - user input
    # height - size of shcematic height in inches - user input
    # x_offset - x location of schematic symbol's left side
    # y_offset - y location of schematic symbol's top side
    # connect_num - the number to start using to name connectors created
    # schematic_pin_num - user defined pin numbering list
    # schematic_pin_label - user defined pin label list
    # connector_pin_attrib - connector pin attibutes - used later to create pins
    # connector_term_attrib - connector terminalID attributes - used to create terminalIDs
    # returns:
    # True if successful user input
    # False if failed user input
    #
    
    # get x location of left most pin position
    x_pos = x_offset            # left side of schematic symbol
    x_pos = x_pos + 100         # add 0.10 inch to position

    # determine offset from left most pin position of 
    # where the pins should start at    
    temp_width = (width * 10)     # multiply by ten to go from decimal input to whole intger

    if num_pins <= temp_width:      # schematic symbol wider than # of pins
        temp_offset = temp_width - num_pins     # calculate offset
        temp_offset = int( ( temp_offset / 2 )  )
    else:
        temp_offset = temp_width

    x_pos = x_pos + (temp_offset * 100)           # scale offset  

    # y location of pin
    y_pos1 = y_offset + (height * 1000) 
    # length of pin...
    y_pos2 = y_pos1 + 100    # should be set to 100, or 0.1 inch

    # check for user input
    if ((self.options.pin_num == 1) or (self.options.pin_label == 1)):           # user defined pin numbers or labels
        user_pin_number_label(self, num_pins, connect_num, schematic_pin_num, schematic_pin_label, "Bottom")
        #sys.stderr.write(" user_pin_number_label result = " + str(result) + "\n\n")
    
    if (self.options.pin_num == 1):                                 # user defined pin numbers
        if len(schematic_pin_num) < (connect_num - 1 + num_pins):   # check that all pin numbers were entered by user
            return bool(False)                                      # return False - an error on input
            
    else:                                                           # sequential pin numbers
        connect_number = connect_num
        for index in range(num_pins):                               # loop thru and number the pins
            schematic_pin_num.append(connect_number)
            connect_number = connect_number + 1
            
    if (self.options.pin_label == 1):                               # user defined pin labels
        if len(schematic_pin_label) < (connect_num - 1 + num_pins): # check that all pin labels were entered by user
            return bool(False)                                      # return False - an error on input
            
    else:                                                           # sequential pin labels
        connect_number = connect_num
        for index in range(num_pins):                               # loop thru and label the pins
            schematic_pin_label.append("pin" + str(schematic_pin_num[connect_number - 1] )) # pin label should be text 'pin' + connector number of the pin
            connect_number = connect_number + 1                     # and not this sequentially counting number
    # end of check user input

    # create the pins, pin numbers, and pin labels
    for index in range(connect_num, connect_num + num_pins):
        connect_num = schematic_pin_num[index-1] - 1
        
        connect_name = "connector" + str(connect_num) + "pin"

        pin_attribs = set_pin_attribs(connect_name, x_pos, x_pos, y_pos1, y_pos2)
        # add pin_attribs dict to connector_pin_attrib list for pin creation later on
        connector_pin_attrib.append(pin_attribs)
        
        # create pin number/label
        create_pin_number(self, group, (connect_num + 1), x_pos, x_pos, y_pos1, y_pos2)
        create_pin_label(self, group, (schematic_pin_label[index - 1]), (connect_num + 1), x_pos, x_pos, y_pos1, y_pos2)

        # terminal ID creation
        if self.options.terminal_id is True:
            terminal_id_name = "connector" + str(connect_num) + "terminal"
            
            id_attribs = set_term_attribs(terminal_id_name, x_pos - 5, y_pos2 - 5)
            
            connector_term_attrib.append(id_attribs)
            

        # first pin created at starting position for pins
        # now figure out location for next pin
        x_pos = x_pos + 100
        
    # end of create pins, pin numbers, and pin labels
    
    return True     # return true, all pins created   
# end of - def create_bottom_pins(self, group, num_pins, width, height, x_offset, y_offset, connect_num, schematic_pin_num, schematic_pin_label, connector_pin_attrib, connector_term_attrib):


def create_right_pins(self, group, num_pins, width, height, x_offset, y_offset, connect_num, schematic_pin_num, schematic_pin_label, connector_pin_attrib, connector_term_attrib):
    # create right side pins for schematic symbol
    # inputs:
    # group - the group to add the pins to
    # num_pins - number of pins to create
    # width - size of schematic width in inches - user input
    # height - size of shcematic height in inches - user input
    # x_offset - x location of schematic symbol's left side
    # y_offset - y location of schematic symbol's top side
    # connect_num - the number to start using to name connectors created
    # schematic_pin_num - user defined pin numbering list
    # schematic_pin_label - user defined pin label list
    # connector_pin_attrib - connector pin attibutes - used later to create pins
    # connector_term_attrib - connector terminalID attibutes - used later to create terminalIDs
    # returns:
    # True if successful user input
    # False if failed user input
    #    #

    svg = self.document.getroot()

    # x location of pin
    x_pos1 = x_offset + (width * 1000)   # find right side of schematic symbol
    # length of pin...
    x_pos2 = x_pos1 + 100   # should be set to 100, or 0.1 inch

    # y location of pin
    # get y location of right most possible pin position
    y_pos = y_offset + (height * 1000)      # right side of schematic symbol
    y_pos = y_pos - 100                                    # subtract 0.10 inch to position
    
    # attempt to center pin vertically - works so-so
    # determine offset from left most pin position of 
    # where the pins should start at
    temp_height = (height * 10)     # multiply by ten to go from decimal input to whole intger
    
    if num_pins < temp_height:
        temp_offset = temp_height - num_pins
        temp_offset = int((temp_offset / 2))
    else:
        temp_offset = (temp_height)
        
    y_pos = y_pos - (temp_offset * 100)
    #y1_value = str(y_pos)
    
    #
    if ((self.options.pin_num == 1) or (self.options.pin_label == 1)):           # user defined pin numbers or labels
        result = user_pin_number_label(self, num_pins, connect_num, schematic_pin_num, schematic_pin_label, "Right")
        #sys.stderr.write(" user_pin_number_label result = " + str(result) + "\n\n")
    
    if (self.options.pin_num == 1):                                 # user defined pin numbers
        if len(schematic_pin_num) < (connect_num - 1 + num_pins):   # check that all pin numbers were entered by user
            return bool(False)
    else:                                                           # sequential pin numbers
        connect_number = connect_num
        for index in range(num_pins):
            schematic_pin_num.append(connect_number)
            connect_number = connect_number + 1
            
    if (self.options.pin_label == 1):                               # user defined pin labels
        if len(schematic_pin_label) < (connect_num - 1 + num_pins): # check that all pin labels were entered by user
            return bool(False)
    else:
        connect_number = connect_num
        for index in range(num_pins):
            schematic_pin_label.append("pin" + str(schematic_pin_num[connect_number - 1] )) # pin label should be text 'pin' + connector number of the pin
            connect_number = connect_number + 1                     # and not this sequentially counting number
    #

    
    # create the pins, pin numbers, and pin labels
    for index in range(connect_num, connect_num + num_pins):
        connect_num = schematic_pin_num[index-1] - 1

        connect_name = "connector" + str(connect_num) + "pin"

        pin_attribs = set_pin_attribs(connect_name, x_pos1, x_pos2, y_pos, y_pos)
        
        # add pin_attribs dict to connector_pin_attrib list for pin creation later on
        connector_pin_attrib.append(pin_attribs)
        
        # create pin number/label
        create_pin_number(self, group, (connect_num + 1), x_pos1, x_pos2, y_pos, y_pos)
        create_pin_label(self, group, (schematic_pin_label[index - 1]), (connect_num + 1), x_pos1, x_pos2, y_pos, y_pos)

        # terminal ID creation
        if self.options.terminal_id is True:
            terminal_id_name = "connector" + str(connect_num) + "terminal"
            
            id_attribs = set_term_attribs(terminal_id_name, x_pos2 - 5, y_pos - 5)
            
            connector_term_attrib.append(id_attribs)


        
        # first pin created at starting position for pins
        # now figure out location for next pin
        y_pos = y_pos - 100
        y1_value = str(y_pos)
    # end of create pins, pin numbers, and pin labels    


    return
# end of - def create_right_pins(self, group, num_pins, width, height, x_offset, y_offset, connect_num, schematic_pin_num, schematic_pin_label, connector_pin_attrib, connector_term_attrib):


def create_top_pins(self, group, num_pins, width, height, x_offset, y_offset, connect_num, schematic_pin_num, schematic_pin_label, connector_pin_attrib, connector_term_attrib):
    # create top pins for schematic symbol
    # inputs:
    # group - the group to add the pins to
    # num_pins - number of pins to create
    # width - size of schematic width in inches - user input
    # height - size of shcematic height in inches - user input
    # x_offset - x loc of schematic symbol's left side    
    # y_offset - y location of schematic symbol's top side
    # connect_num - the number to start using to name connectors created
    # schematic_pin_num - user defined pin numbering list
    # schematic_pin_label - user defined pin label list
    # connector_pin_attrib - connector pin attibutes - used later to create pins
    # connector_term_attrib - connector terminalID attributes - used to create terminalIDs
    # returns:
    # True if successful user input
    # False if failed user input
    #

    svg = self.document.getroot()
    
    # x location of pin
    # get x location of right most pin position
    x_pos = x_offset + (width * 1000)
    x_pos = x_pos - 100    # subtract 2.54mm (0.10 inch) to position so pin isn't on edge of symbol

    # determine offset from right most pin position of 
    # where the pins should start at    
    temp_width = (width * 10)     # multiply by ten to go from decimal input to whole intger

    if num_pins <= temp_width:      # schematic symbol wider than # of pins
        temp_offset = temp_width - num_pins     # calculate offset
        temp_offset = int( ( temp_offset / 2 )  )
    else:
        temp_offset = temp_width


    x_pos = x_pos - (temp_offset * 100)           # scale offset
    #x1_value = str(x_pos)   

    # y location of pin
    y_pos1 = y_offset               # find top of schematic symbol
    #y1_value = str(y_pos1)

    # length of pin... 
    y_pos2 = y_pos1 - 100
    #y2_value = str(y_pos2)
    
    #
    if ((self.options.pin_num == 1) or (self.options.pin_label == 1)):           # user defined pin numbers or labels
        result = user_pin_number_label(self, num_pins, connect_num, schematic_pin_num, schematic_pin_label, "Top")
        #sys.stderr.write(" user_pin_number_label result = " + str(result) + "\n\n")
    
    if (self.options.pin_num == 1):                                 # user defined pin numbers
        if len(schematic_pin_num) < (connect_num - 1 + num_pins):   # check that all pin numbers were entered by user
            return bool(False)
    else:                                                           # sequential pin numbers
        connect_number = connect_num
        for index in range(num_pins):
            schematic_pin_num.append(connect_number)
            connect_number = connect_number + 1
            
    if (self.options.pin_label == 1):                               # user defined pin labels
        if len(schematic_pin_label) < (connect_num - 1 + num_pins): # check that all pin labels were entered by user
            return bool(False)
    else:
        connect_number = connect_num
        for index in range(num_pins):
            schematic_pin_label.append("pin" + str(schematic_pin_num[connect_number - 1] )) # pin label should be text 'pin' + connector number of the pin
            connect_number = connect_number + 1                     # and not this sequentially counting number
    #

    # create the pins, pin numbers, and pin labels
    for index in range(connect_num, connect_num + num_pins):
        connect_num = schematic_pin_num[index-1] - 1

        connect_name = "connector" + str(connect_num) + "pin"

        pin_attribs = set_pin_attribs(connect_name, x_pos, x_pos, y_pos1, y_pos2)
        
        # add pin_attribs dict to connector_pin_attrib list for pin creation later on
        connector_pin_attrib.append(pin_attribs)    
        
        # create pin number/label
        create_pin_number(self, group, (connect_num + 1), x_pos, x_pos, y_pos1, y_pos2)
        create_pin_label(self, group, (schematic_pin_label[index - 1]), (connect_num + 1), x_pos, x_pos, y_pos1, y_pos2)

        # terminal ID creation
        if self.options.terminal_id is True:
            terminal_id_name = "connector" + str(connect_num) + "terminal"
            
            id_attribs = set_term_attribs(terminal_id_name, x_pos - 5, y_pos2 - 5)
            
            connector_term_attrib.append(id_attribs)
        
        # first pin created at starting position for pins
        # now figure out location for next pin
        x_pos = x_pos - 100
        x1_value = str(x_pos)
    # end of create pins, pin numbers, and pin labels  

    return
# end of - def create_top_pins(self, group, num_pins, width, height, x_offset, y_offset, connect_num, schematic_pin_num, schematic_pin_label, connector_pin_attrib, connector_term_attrib):


def set_pin_attribs(pin_name, x1_loc, x2_loc, y1_loc, y2_loc):
    # set the attributes for the graphic element that will be the connector pin
    # inputs:
    # pin_name - name used for the connector pin
    # x1_loc - x location of the pin at schematic symbol
    # x2_loc - x location of other end of the pin
    # y1_loc - y location of one end of the pin
    # y2_loc - y location of other end of the pin
    # returns:
    # pin_attribs{} - a dict of strings that conatins the info inkscape needs to create the graphic
    #
    
    # x location of pin
    x1_value = str(x1_loc)
    x2_value = str(x2_loc)
    
    # y location of pin
    y1_value = str(y1_loc)
    y2_value = str(y2_loc)
    
    # define pin attributes
    pin_attribs = {
        'fill'          : 'none',
        'id'            : pin_name,
        'stroke'        : '#555555',
        'stroke-linecap'    : 'round',
        'stroke-width'      : '10',
        'x1'            : x1_value,
        'x2'            : x2_value,
        'y1'            : y1_value,
        'y2'            : y2_value
        }
    
    return pin_attribs
# end of - def set_pin_attribs(pin_name, x1_loc, x2_loc, y1_loc, y2_loc)


def set_term_attribs(term_name, x_loc, y_loc):
    # set the terminal IDs attributes for the grahic element that will be created
    # inputs:
    # term_name - name of the terminal ID
    
    
    
    x_value = str(x_loc)
    y_value = str(y_loc)
    
    # define connector terminal ID attibutes
    id_attribs = {
        'fill'          : 'none',
        'id'            : term_name,
        'height'        : '10',
        'width'         : '10',
        'style'         : 'fill:none;stroke:none;stroke-width:0',
        'x'             : x_value,
        'y'             : y_value
        }
    
    
    return id_attribs
# end of - def set_term_attribs(term_name, x_loc, y_loc):


def create_pin_number(self, group, connect_num, x_pos1, x_pos2, y_pos1, y_pos2):
    # create pin number for connector
    # inputs:
    # group - the group to add the pin number to
    # connect_num - number to use for pin
    # x_pos1 - the x location of the end of the pin by the schematic symbol
    # x_pos2 - the x location of the other end of the pin 
    # y_pos1 - the y location of the end of the pin by the schematic symbol
    # y_pos2 - the y location the the other end of the pin
    # returns:
    # nothing
    #

    # Create text element
    text = etree.Element(inkex.addNS('text','svg'))

    pin_number = str(connect_num)
    text.text = pin_number
    
    # check pin orientation to decide
    # where and how to place pin number
    if y_pos1 == y_pos2:
        # we have a horizontal pin
        if x_pos1 > x_pos2:
            # we have a left side pin
            # calculate pin number location
            x_loc = ( x_pos1 - 30 )     # x location
            y_loc = ( y_pos1 - 20 )         # y location
            
            text.set('x', str(x_loc))      
            text.set('y', str(y_loc))
            text.set('text-anchor', 'end')
            
        else:
            # we have a right side pin
            # calculate pin number location
            x_loc = ( x_pos1 + 30 )     # x location
            y_loc = ( y_pos1 - 20 )     # y location
            
            text.set('x', str(x_loc))      
            text.set('y', str(y_loc))
            text.set('text-anchor', 'start')        
            
    else:
        # we have a vertical pin
        if y_pos1 < y_pos2:
            # we have a bottom pin
            # calculate pin number location
            y_loc = ( y_pos1 + 50 )     # y location
            x_loc = ( x_pos1 - 20 )     # x location
            
            # Set text position    
            text.set('x', str(x_loc))   
            text.set('y', str(y_loc))
            text.set('text-anchor', 'end')
       
        else:
            # we have a top pin
            # calculate pin number location
            y_loc = ( y_pos1 - 30 )     # y location
            x_loc = ( x_pos1 - 20 )     # x location
            
            # Set text position    
            text.set('x', str(x_loc))   
            text.set('y', str(y_loc))
            text.set('text-anchor', 'end')
    
    # create id for the pin number
    pin_num_id = 'pin' + str(connect_num - 1) + 'num'
    # Set text properties
    text.set('font-family', 'Droid Sans')
    text.set('font-size', '35')
    text.set('fill', '#555555')
    text.set('id', pin_num_id)
    
    # Connect elements together.
    group.append(text)


    return
# end of - def create_pin_number(self, group, connect_num, x_pos1, x_pos2, y_pos1, y_pos2):


def create_pin_label(self, group, connect_label, connect_num, x_pos1, x_pos2, y_pos1, y_pos2):
    # create pin label for connector
    # inputs:
    # group - the group to add the pin number to
    # connect_label - text to use for pin label
    # connect_num - connector number
    # x_pos1 - the x location of the end of the pin by the schematic symbol
    # x_pos2 - the x location of the other end of the pin 
    # y_pos1 - the y location of the end of the pin by the schematic symbol
    # y_pos2 - the y location the the other end of the pin
    # returns:
    # nothing
    #
    
    # Create text element
    text = etree.Element(inkex.addNS('text','svg'))

    #pin_label = "pin" + str(connect_num)
    text.text = connect_label
    
    if y_pos1 == y_pos2:
        # we have a horizontal pin
        if x_pos1 > x_pos2:
            # we have a left side pin
            # left side label location 
            
            # calculate pin label location
            x_loc = ( x_pos1 + 20)     # x location of label
            y_loc = y_pos1 + 12        # y location
            
            text.set('x', str(x_loc))      
            text.set('y', str(y_loc))
            text.set('text-anchor', 'start')
            #text.set('dominant-baseline', 'central')
            
        else:
            # we have a right side pin
            # right side label location 
            
            # calculate pin label location
            x_loc = ( x_pos1 - 20 )     # x location of label
            y_loc = ( y_pos1 + 12 )     # y location of label
            
            text.set('x', str(x_loc))      
            text.set('y', str(y_loc))
            text.set('text-anchor', 'end')
            
    else:
        # we have a vertical pin
        if y_pos1 < y_pos2:
            # we have a bottom pin
            # bottom side label location 
            
            # calculate pin label location
            y_loc = ( y_pos1 - 20 )     # y location of label
            x_loc = ( x_pos1 + 12 )     # x location of label
            
            # Set text position    
            text.set('x', '-' + str(y_loc))   
            text.set('y', str(x_loc))
            text.set('text-anchor', 'start')
            text.set('transform', 'rotate (-90)')       # set rotation
        
        else:
            # we have a top pin
            # top side number location shouldn't vary depending upon # of digits
            
            # calculate pin label location
            y_loc = ( y_pos1 + 20 )     # y location of label
            x_loc = ( x_pos1 + 12 )     # x location of label
            
            # Set text position    
            text.set('x', '-' + str(y_loc))   
            text.set('y', str(x_loc))
            text.set('text-anchor', 'end')
            text.set('transform', 'rotate (-90)')       # set rotation       
    
    # create id for the pin label
    pin_label_id = 'pin' + str(connect_num - 1) + 'label'
    
    # Set general text properties
    text.set('font-family', 'Droid Sans')
    text.set('font-size', '49')
    text.set('fill', '#555555')
    text.set('id', pin_label_id)
    #text.set('style', 'font-size:1')
    
    # Connect elements together.
    group.append(text)


    return
# end of - def create_pin_label(self, group, connect_label, connect_num, x_pos1, x_pos2, y_pos1, y_pos2):


def create_pin(self, group, pin_attribs):
    # create the actual pins
    # inputs:
    # group - the group to add the pins to
    # pin_attribs - dictionary containing pin attributes
    # returns:
    # nothing
    #
    
    newObj = etree.SubElement(group, inkex.addNS('line','svg'), pin_attribs )
    
    return
# end of - def create_pin(self, group, pin_attribs):


def create_terminalID(self, group, term_attribs):
    # create the actual terminalIDs
    # inputs:
    # group - the group to add the terminalIDs to
    # term_attribs - dictionary containing terminalID attributes
    # returns:
    # nothing
    #
    
    newObj = etree.SubElement(group, inkex.addNS('rect','svg'), term_attribs )
    
    return
# end of - def create_terminalID(self, group, term_attribs):


def user_pin_number_label(self, num_of_pins, connect_num, schematic_pin_num, schematic_pin_label, side):
    # get user input for pin numbers/labels for side of schematic
    # this function creates a window and awaits user input for pin numbers and/or labels
    #
    # input:
    # num_of_pins - number of pins on left side of symbol
    # connect_num - connector number to start using
    # schematic_pin_num - user input pin numbering list
    # schematic_pin_label - user input pin labels list
    # side - side of schematic symbol - "Left", "Bottom", "Right", "Top"
    # returns:
    # nothing
    #

    result = False      # error flag - True = error, False = no error
    
    #
    # def submit() - function called when user exits window via 'finished' button
    #
    def submit():
        # fetch user input and exit 
        
        pin_num_input = []                  # temporary pin number list
        pin_label_input = []                # temporary pin label list
        
        for index in range(len(pin_num)):
            
            # get user pin number input and check for errors
            if self.options.pin_num == 1:                       # user defined pin numbers
                current_pin_num = pin_num[index].get()
                
                if current_pin_num.isnumeric() is False:        # pin number entry not a number
                    #sys.stderr.write("Pin number entry is not a number. \n")
                    errormsg = "Pin number " + (str(index + connect_num)) + " number entry is invalid."
                    #user_input_error(errormsg)
                    result = True   # set error flag
                    break           # break out of loop and handle input error
    
                else:
                    pin_num_input.append(int(current_pin_num))  # valid pin number entry, add to list
                    #sys.stderr.write(" pin #" + str(index) + " = " + current_pin_num + "\n")
                    result = False  # clear error flag   
        
            # get user pin label input and check for errors
            if self.options.pin_label == 1:                     # user defined pin labels
                current_pin_label = pin_label[index].get()
                
                if current_pin_label == "":                     # check for empty input
                    #sys.stderr.write("Pin Label entry blank. \n")
                    errormsg = "Pin number " + (str(index + connect_num)) + " label entry is invalid."
                    #user_input_error(errormsg)
                    result = True   # set error flag
                    break           # break out of loop and handle input error
                    
                else:
                    pin_label_input.append(current_pin_label)   # add user input to schematic_pin_label list
                    #sys.stderr.write(" pin #" + str(index) + " = " + current_pin_label + "\n")
                    result = False  # clear error flag
                    
        #end - for index in range(len(pin_num)): - loop
        
        # check for UI error
        if result is False:         # no user input error
            # no error - close UI window
            win_root.destroy()          # close the user input window
            
            if self.options.pin_num == 1:                       # user defined pin numbers
                for index in range(0, len(pin_num_input)) :     # copy user input to schematic_pin_num
                    schematic_pin_num.append(pin_num_input[index])
                
            if self.options.pin_label == 1:                     # user defined pin labels
                for index in range(0, len(pin_label_input)) :   # copy user input to schematic_pin_label
                    schematic_pin_label.append(pin_label_input[index])
            #sys.stderr.write(" exit submit function here, no more data to print \n\n")
            
            return
            
        else:                       # user input error
            #errormsg = "Pin number " + (str(index + connect_num)) + " label entry is invalid."
            messagebox.showerror("showerror", "ERROR: \n\n" + errormsg)    
        
        return
    # end of - def submit()
 
    # mousewheel scroll - 
    def on_mousewheel(event, scroll = None):
    
        if sys.platform == 'linux' or sys.platform == 'linux2':     # linux OS
            root_canvas.yview_scroll(int(scroll), "units")
        elif sys.platform == 'darwin':                              # mac OS
            root_canvas.yview_scroll(int(-1 * event.delta), "units")
        else:                                                       # assume win OS
            root_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        #sys.stderr.write(" on_mousewheel \n\n")
        return
    #
    
    #
    # start of code defining input window
    #
    win_root = tk.Tk()
    win_root.title("Schematic symbol pin numbers/labels")
    
    # declare list for storing pin number 
    pin_num = []
    for index in range(num_of_pins):
        pin_num.append(tk.StringVar())      # fill list with tk.StringVar to get user input

    # declare list for storing label         
    pin_label = []
    for index in range(num_of_pins):
        pin_label.append(tk.StringVar())    # fill list with tk.StringVar to get user input

    # window size
    # 400 width 125 height works for 1 connector
    row_height = 31     # height needed for each connector
    win_height = 125 + (( num_of_pins - 1 ) * row_height )  # num_of_pins - 1 : because 125 is height for 1 connector
                                                            # we're just adding more space for more than one connector
    if win_height > 400:
        win_height = 400
    win_size = "400x" + str(win_height)
    
    # window location - center UI window on screen
    screen_width = win_root.winfo_screenwidth()
    screen_height = win_root.winfo_screenheight()
    
    win_x_loc = int((screen_width/2) - (400/2))
    win_y_loc = int((screen_height/2) - (win_height/2))
    
    win_size = win_size + '+' + str(win_x_loc) + '+' + str(win_y_loc)
    
    win_root.geometry(win_size)                 # set window size
    win_root.resizable(0,0)                     # disable scaling of window
    win_root.attributes('-topmost', True)       #Make the window jump above all
    #root.overrideredirect(1)                    # removes window's menu/title bar
    
    
    # scroll bar for UI entry code taken from -
    ### https://www.youtube.com/watch?v=0WafQCaok6g ###
    #
    # create a frame
    root_frame = Frame(win_root)    # create a frame in win_root window
    root_frame.pack(fill = 'both', expand = '1')
    
    # create a canvas
    root_canvas = Canvas(root_frame)
    root_canvas.pack(side = 'left', fill = 'both', expand = '1')

    # add scrollbar to canvas
    v_scrollbar = Scrollbar(root_frame, orient = 'vertical', command = root_canvas.yview)
    v_scrollbar.pack(side = 'right', fill = 'y')
    
    # configure canvas
    root_canvas.configure(yscrollcommand = v_scrollbar.set)
    root_canvas.bind("<Configure>", lambda e: root_canvas.configure(scrollregion = root_canvas.bbox("all")))

    # mousewheel scrollbar binding -
    if sys.platform == 'linux' or sys.platform == 'linux2':     # linux OS - binding
        canvas.bind_all("<Button-4>", fp(_on_mousewheel, scroll=-1))
        canvas.bind_all("<Button-5>", fp(_on_mousewheel, scroll=1))
    else:                                                       # win/mac OS - binding
        root_canvas.bind_all("<MouseWheel>", on_mousewheel)
    #sys.stderr.write(" bind mousewheel \n\n")
    
    
    # add another frame inside the canvas
    UI_frame = Frame(root_canvas)   # this is the frame that will hold all the input elements
    
    # add that frame into a window in the canvas
    root_canvas.create_window((0,0), window = UI_frame, anchor = "nw")
    # end scroll bar code
    
    
    # define UI window in UI_frame
    # display header text in input window
    a = tk.Label(UI_frame, text = side + " side schematic pin numbers/labels:")
    a.grid(row = 1, column = 0, columnspan = 3 )
    a = tk.Label(UI_frame, text = "Pin Number")
    a.grid(row = 2, column = 1)
    a = tk.Label(UI_frame, text = "Pin Label")
    a.grid(row = 2, column = 2)
        
    # display input fields
    for index in range(num_of_pins):
        desc = tk.Label(UI_frame, text = "Pin #" + str(index + connect_num))                        # input field label
        desc.grid(row = (index + 3), column = 0, padx = 10, pady = 5)
        
        if self.options.pin_num == 1:           # user defined pin numbers
            entry_state = 'normal'
            #bgcolor = '#FFFFFF'
        else:
            entry_state = 'disabled'
            #bgcolor = '#000000'     # doesn't appear to work
            
        pin_input = tk.Entry(UI_frame, state = entry_state, textvariable = pin_num[index] )        # pin number input field
        pin_input.grid(row = (index + 3), column = 1, padx = 10, pady = 5)
        
        if self.options.pin_label == 1:         # user defined pin labels
            entry_state = 'normal'
        else:
            entry_state = 'disabled'
            
        label_input = tk.Entry(UI_frame, state = entry_state, textvariable = pin_label[index] )     # pin label input field
        label_input.grid(row = (index + 3), column = 2, padx = 10, pady = 5)
    
    btn = tk.Button(UI_frame, text = "Finished", command = submit)
    btn.grid(row = (num_of_pins + 4), column = 0, columnspan = 3, padx = 10, pady = 10)
    
    # end of code defining UI input window
    
    '''
    def enter_submit(event):
    # handles the enter key event
        
        if (btn['state'] == 'active' ): 
        # need to determine if btn is active or not
        # only call submit if btn is active
            submit()
        
        return
        
    root.bind('<Return>', enter_submit)
    '''
    
    win_root.mainloop()     # enter loop to wait user input
    
    return
# end of - def user_pin_number_label(self, num_of_pins, connect_num, schematic_pin_num, schematic_pin_label, side):


''' this function not used '''
def user_input_error(errmsg):
# open an error window, display error message, and wait for UI
# inputs:
# errmsg - the error message to display in the window
# returns:
# nothing
#

    errwin = tk.Tk()
    errwin.title("Input Error")
    
    errwin.geometry("200x150")
    errwin.attributes('-toolwindow', True)
    
    b = tk.Label(errwin, text = "")
    b.pack()
    a = tk.Label(errwin, text = " Input Error:")
    a.pack()
    c = tk.Label(errwin, text = errmsg)
    c.pack()
    b = tk.Label(errwin, text = "")
    b.pack()

    def submit():
        #sys.stderr.write("error window Submit button clicked\n\n")
        errwin.destroy()
        return
    
    btn = tk.Button(errwin, text = "OK", command = submit)
    btn.pack()
    
    errwin.mainloop()
    
    return
# end of - def user_input_error(errmsg):


def error_cleanup(self, group, org_doc_width, org_doc_height, org_doc_viewbox):
    # error cleanup funtion
    # if UI pin number/label window is closed without clicking the 'finished' button
    # then that is considered an user error - but part of the schematic symbol will be
    # created by the time this error is encountered
    # so this function removes the schematic group already created and
    # resets document & viewbox sizes to the values before script execution
    #
    # inputs:
    # group - the current group to be deleted
    # org_doc_width - original document width, before script run
    # org_doc_height - original document height, before script run
    # returns:
    # nothing
    
    svg = self.document.getroot()
    
    group.delete()      # delete the group we started to create before error
    
    svg.set('width', org_doc_width)         # set doc width
    svg.set('height', org_doc_height )      # set doc height
    
    svg.set('viewBox', org_doc_viewbox)     # set doc viewbox
    ''' the idea here is to set the doc width, height, and viewbox
        back to the values they were before this script starts,
        since those are the only values prep_doc() changes
    '''
    
    
    return
# end of - def error_cleanup(self, group):


def error_check_params(schematic_width, schematic_height, num_left_pins, num_bottom_pins, num_right_pins, num_top_pins):
    # error check user input - check for too many connectors for size of symbol
    # inputs:
    # schematic_width - width of schematic symbol in inches
    # schematic_height - height of schematic symbol in inches
    # num_left_pins - number of pins on left side of symbol
    # num_bottom_pins - number of pins on bottom side of symbol
    # num_right_pins - number of pins on right side of symbol
    # num_top_pins - number of pins on top side of symbol
    # returns:
    # True - valid user input
    # False - invalid user input
    #
    
    symbol_height = schematic_height * 10           # scale up schematic_height by 10 to give us whole numbers
    symbol_width = schematic_width * 10             # scale up schematic_width by 10 to give us whole numbers
    
    if num_left_pins > (symbol_height - 1):
        # too many pins to fit along left of schematic
        # symbol with proper spacing - raise error
        sys.stderr.write("\n Too many connectors on left side of symbol\n\n")
        sys.stderr.write(" - A symbol height of " + str(schematic_height) + " inches can only have ")
        sys.stderr.write(str(int(symbol_height - 1)) + " connectors\n    on the left and right sides.\n\n")
        sys.stderr.write(" extension failed!\n")
        return False
    
    if num_bottom_pins > (symbol_width - 1):
        # too many pins to fit along bottom of schematic
        # symbol with proper spacing - raise error
        sys.stderr.write("\n Too many connectors on bottom side of symbol\n\n")
        sys.stderr.write(" - A symbol width of " + str(schematic_width) + " inches can only have ")
        sys.stderr.write(str(int(symbol_width - 1)) + " connectors\n    on the top and bottom sides.\n\n")
        sys.stderr.write(" extension failed!\n")
        return False

    if num_right_pins > (symbol_height - 1):
        # too many pins to fit along right of schematic
        # symbol with proper spacing - raise error
        sys.stderr.write("\n Too many connectors on right side of symbol\n\n")
        sys.stderr.write(" - A symbol height of " + str(schematic_height) + " inches can only have ")
        sys.stderr.write(str(int(symbol_height - 1)) + " connectors\n    on the left and right sides.\n\n")
        sys.stderr.write(" extension failed!\n")
        return False
    
    if num_top_pins > (symbol_width - 1):
        # too many pins to fit along top of schematic
        # symbol with proper spacing - raise error
        sys.stderr.write("\n Too many connectors on top side of symbol\n\n")
        sys.stderr.write(" - A symbol width of " + str(schematic_width) + " inches can only have ")
        sys.stderr.write(str(int(symbol_width - 1)) + " connectors\n    on the top and bottom sides.\n\n")
        sys.stderr.write(" extension failed!\n")
        return False        
    
    return True
# end of - def error_check_params(schematic_width, schematic_height, num_left_pins, num_bottom_pins, num_right_pins, num_top_pins):

 
''' end of functions '''


if __name__ == '__main__':  # pragma: no cover
    FritzingSchematic().run()


#### Notes and stuff ####
# 6/23/2021 - pin number entry fails if entry is a number followed by a space
# - maybe should check for and remove trailing spaces?

#### version history ####
# v0.1 alpha - for Inkscape v0.91 - created a basic schematic symbol 
#   - only sequential pin numbers and generic labels
#   - not all elements were placed correctly
#
# v0.2 alpha - for Inkscape v1.0 - updated to work with latest version of Inkscape
#   - added user input for pin numbers/labels
#   - placement problems fixed.
#
# v0.3 alpha - fixed document size/viewBox values to be compatible with fritizing
#   - svg is now created with a px scale value of 10.41667 to meet fritzing's requirements
#   - fixed element placement for the new document scale
#   - fixed font size issues
#
# v0.4 alpha - work on UI
#   - updated fritzing-schematic.inx to Inkscape v1.0 standards and improved UI
#   - further corrected placement of elements, font sizes, etc
#   - UI error checking
#
# v0.5 alpha - document size is calculated based on existence of pins per side
#   - silence debug output - only error messages output
#   - connector pins are now created last, so they are the last items in .svg
#
# v0.6 alpha - clean up of code - remove old code used while developing
#   - correct some remarks to reflect current code - still work needs done here
#   - added in creation of terminalIDs
#   - added in a clean up function for failure of script - reloads default inkscape startup
#
# v0.7 alpha - error checking of symbol size and number of connectors now happens at startup
#   - improved clean up function for script failure - should reset to user settings
#   - added scroll bar to user pin number/label entry window & limited size of window
#
# v0.8 alpha - added mit license and copyright info
#   - code cleanup and improved error messages
#   - set max symbol size to 6.5in, 64 connectors per side = 256 max connectors
#
# v0.9 beta - remove more dev code and publish to github
#   - updated .inx file with github url
#
# v1.0 - added in support for mouse scroll wheel
#   - Schematic symbol pin numbers/labels input window now supports mouse scroll wheel
#









