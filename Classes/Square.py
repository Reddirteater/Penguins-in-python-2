import random
import string
from os.path import isfile, join, realpath, abspath, dirname
from imp import load_source

from tkinter import Tk, Frame, BOTH, StringVar, Label, Button, Menu
from PIL import Image, ImageTk

import constants
import maps

class Square(constants.correction):
    def debug_click(self, event):
        DEBUG_MODE = True
        row = int(event.y/constants.grid_size)
        column = int(event.x/constants.grid_size)
        s = self.app.screen.grid[row][column]
        
        if DEBUG_MODE:
            o = string.Template('Clicked {x:$column, y:$row}').substitute({'column':column, 'row': row})
            print(o)
            print("Type: " + s.square_type)
            print("Passable: " +str(s.passable))
            print("Occupied: " + str(s.occupied))
            print("Has Tux: " + str(s.has_tux))
            print("Has Wall: " + str(s.has_wall))
            print("Has Fish: " + str(s.has_fish))
            print(str(self.sprites))

        action = self.app.action
        if action is not None:
            print(action)
            # def remove_feature(self, feature, app, make_passable=True):
            if action == "destroy wall":
            	s.remove_feature(feature="wall", app=self.app)
            elif action == "catch fish":
            	print("in catch routine")
            	for fish in self.app.screen.fishes:
	                if fish.row == s.row and fish.column == s.column:
	                    fish.destroy()
	                    del fish
	                    self.app.inventory["fish"]["qty"]+=10
	                    self.app.update_inventory()
	                    print("caught fish")
            self.app.screen.canvas.configure(cursor="")
            self.app.action = None
            # self.app.config(cursor = "arrow black black")


    def __init__(self, row, column, canvas, app, g=constants.grid_size, square_type='grass'):
        if canvas is not None:
            self.canvas = canvas
            self.passable=True
            if square_type == 'grass':
                fill='green'
            elif square_type == 'water':
                fill='blue'
                self.passable = False
            elif square_type == 'snow':
                fill='white'
            elif square_type == 'sand':
                fill = 'yellow'
            self.representation = canvas.create_rectangle(
                (column*g)+5, 
                (row*g)+5, 
                ((column+1)*g)+5, 
                ((row+1)*g)+5,
                fill=fill)
            self.canvas.bind("<Button-1>", self.debug_click)
            self.canvas.bind("<Control-Button-1>", app.edit_square)
        self.square_type = square_type
        self.row=row
        self.column=column
        self.app = app
        self.occupied=False
        self.has_tree = False
        self.has_rock = False
        self.has_tux = False
        self.has_wall = False
        self.has_fish = False
        self.sprites={}
        self.has_bridge = {}
        for direction in constants.DIRECTIONS:
            self.has_bridge[direction.val] = False
    
    def add_feature(self, feature, app, required_type="grass", passable=True):
        g = constants.grid_size
        img = Image.open("sprites/Tiles/sm_"+feature+".gif")
        img.thumbnail((g,g))
        name = feature+"_sprite"
        # print name
        if name not in app.sprite_images:
            app.sprite_images[feature+"_sprite"] = ImageTk.PhotoImage(img)
        prop = "has_" + feature
        if (self.square_type == required_type and not self.occupied):
                self.sprites[feature+"_sprite"] = app.screen.canvas.create_image(((self.column+0.5)*g)+5, ((self.row+0.5)*g)+5, image=app.sprite_images[feature+"_sprite"])                    
                self[prop]=True
                self.passable = passable
        # print str(self)

    def remove_feature(self, feature, app, make_passable=True):
        # print "Remove Feature"
        # g = constants.grid_size
        name = feature+"_sprite"
        # print name
        prop = "has_" + feature
        # grid[i][j]
        touching_wall = app.screen.neighbor_has(feature="tux", i=self.row, j=self.column)
        # print "Touching Wall:"
        # print touching_wall
        # print ""
        if (touching_wall and self[prop]):
                self[prop] = False
                self.passable = make_passable
                self.app.screen.canvas.delete(self.sprites[feature+"_sprite"])
    
    def add_bridge(self, direction):
        # add appropriate sprite
        sprite_suffix = ''
        if direction in [constants.NORTH, constants.SOUTH]:
            sprite = 'sm_bridge_NS.gif'
            sprite_suffix = '_NS'
        elif direction in [constants.EAST, constants.WEST]:
            sprite = 'sm_bridge_EW.gif'
            sprite_suffix = '_EW'
        else:
            raise Exception("invalid direction")
        sprite = 'sprites/Tiles/' + sprite
        sprite_image = Image.open(sprite)
        try:
            a = self.app.sprite_images["bridge_sprite" + sprite_suffix]
            if a is None:
                raise KeyError()
        except KeyError:
            self.app.sprite_images["bridge_sprite" + sprite_suffix] = sprite_image
        self.sprites["bridge_sprite"] = self.app.screen.canvas.create_image(((self.column+0.5)*g)+5, ((self.row+0.5)*g)+5, image=self.app.sprite_images["bridge_sprite" + sprite_suffix])                    

        # make passable in only that direction
        self.has_bridge[direction.val] = True
        self.has_bridge[(~direction).val] = True

    def neighbor_is(self, direction=None, allowed_types=["grass"], allowed_features=None, forbidden_types=None, forbidden_features=None, passable=True, occupied=False):
        if direction is None:
            return False

        delta = maps.move(direction, 1)

        try:
            neighbor = self.app.screen.grid[self.row + delta["y"]][self.column + delta["x"]]
        except IndexError:
            # Neighbor doesn't exist
            # print("Neighbor doesn't exist")
            return False

        # Must be one of the allowed types unless None
        if allowed_types is not None and neighbor.square_type not in allowed_types:
            return False

        # Must not be one of the forbidden types
        if forbidden_types is not None and neighbor.square_type in forbidden_types:
            return False

        # Must have at least one of the allowed features unless None:
        # If passed as a list, must have all features in the list
        if allowed_features is not None:
            for feature in allowed_features:
                if isinstance(feature, list):
                    required_features = feature
                else:
                    required_features = [feature]
                for required_feature in required_features:
                    if neighbor["has_" + required_feature] == False:
                        return False

        # May not have any of the forbidden features unless None:
        # If passed as a list, have that specific combination
        forbidden = True

        if forbidden_features is not None:
            for feature in forbidden_features:
                if isinstance(feature, list):
                    required_features = feature
                else:
                    required_features = [feature]
                forbidden = True
                for required_feature in required_features:
                    v = neighbor["has_" + required_feature] 
                    forbidden = forbidden and v
                if forbidden:
                    return False

        if passable != neighbor.passable or occupied != neighbor.occupied:
            return False

        # Finally
        return True

    def neighbor_has_tux(self, direction):
        if direction is None:
            return self.has_tux

        delta = maps.move(direction, 1)
        try:
            neighbor = self.app.screen.grid[self.row + delta["y"]][self.column + delta["x"]]
        except IndexError:
            # Neighbor doesn't exist
            # print("Neighbor doesn't exist")
            return False

        return neighbor.has_tux        



