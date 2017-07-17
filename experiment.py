__author__ = "Jon Mulle & Austin Hurst"

import klibs
from klibs.KLConstants import *
from klibs import P
from klibs.KLUtilities import *
from klibs.KLUserInterface import any_key
from klibs.KLGraphics.KLNumpySurface import NumpySurface as ns
from klibs.KLGraphics import aggdraw_to_numpy_surface, fill, flip, blit, clear
from klibs.KLAudio import AudioClip
from klibs.KLCommunication import message, alert
from klibs.KLKeyMap import KeyMap

from PIL import Image, ImageDraw, ImageFilter
import os
import sdl2

# For keeping track of which possible trial factor sets have already been run
from itertools import permutations, product
import csv
import random


"""
DEFINITIONS & SHORTHAND THAT CLEAN UP THE READABILITY OF THE CODE BELOW
"""

CENTRAL    = "central"
PERIPHERAL = "peripheral"

BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)
NEUTRAL_COLOR = P.default_fill_color
TRANSPARENT = 0
OPAQUE = 255


"""
This code defines a  class that 'extends' the basic KLExperiment class.
The experiment itself is actually *run* at the end of this document, after it's been defined.
"""

class PictureDrawingSearch(klibs.Experiment):
    
    mask_blur_width = 32  # pixels
    maximum_mask_size = 0  # automatically set at run time, do not change
    
    image_names = ["image_1.png", "image_2.png", "image_3.png"]
    mask_types  = ["none", "central", "peripheral"]
    masks = {}

    # dynamic trial vars
    mask = None
    mask_label = None
    fixation = None

    def __init__(self, *args, **kwargs):
        super(PictureDrawingSearch, self).__init__(*args, **kwargs)

    def setup(self):
        
        # Generate text and display loading screen
        
        self.txtm.add_style('q_and_a', 48, WHITE)
        self.trial_start_msg = message("Press any key to advance...", 'default', blit_txt=False)
        
        fill()
        message("Loading...", "q_and_a", location=P.screen_c, registration=5)
        flip()
        
        # Load in warning tone indicating time almost up
        
        signal_file = os.path.join(P.resources_dir, "Ping.wav")
        self.warning_signal = AudioClip(signal_file)
        self.warning_onset = 5 # seconds after start of trial
        
        # Initialize keymap for skipping trials (for dev convenience)
        
        self.keymap = KeyMap("skip_trial", ["Del"], ["skipped"], [sdl2.SDLK_DELETE])
        
        # Load in all images in arrangements folder
        
        img_dir = os.path.join(P.image_dir, "arrangements")
        
        self.images = {}
        for img_name in self.image_names:
            img = ns(os.path.join(img_dir, img_name))
            self.images[img_name] = img.render()
                
        # Check which combinations of factors previous participants have done
        # and get a set of factors that hasn't been run yet
        
        self.completed_csv = os.path.join(P.local_dir, "completed.csv")
        self.trial_factors = self.get_trial_factors()
        if P.development_mode:
            print(self.trial_factors)
        
        # Generate masks for the experiment
        
        self.__generate_masks()
        
        self.el.setup()
        

    def __generate_masks(self):
        smaller_than_screen = True
        mask_sizes = [P.central_mask_size, P.peripheral_mask_size]
        while smaller_than_screen:
            self.maximum_mask_size += 1
            new_max_mask_px = deg_to_px(self.maximum_mask_size) + self.mask_blur_width * 4 + 2
            if new_max_mask_px > P.screen_y:
                smaller_than_screen = False
                self.maximum_mask_size -= 1
        for size in mask_sizes:
            if size > self.maximum_mask_size:
                e_str = "The maximum mask size this monitor can support is {0} degrees.".format(self.maximum_mask_size)
                raise ValueError(e_str)
                
        self.masks = {}
        self.masks["central"]    = self.mask(mask_sizes[0], CENTRAL).render()
        self.masks["peripheral"] = self.mask(mask_sizes[1], PERIPHERAL).render()

    def block(self):
        pass
    
    def setup_response_collector(self):

        self.rc.display_callback = self.screen_refresh
        self.rc.terminate_after = [900, TK_S]
        self.rc.uses([RC_KEYPRESS])
        self.rc.keypress_listener.interrupts = True
        self.rc.keypress_listener.key_map = self.keymap
        self.rc.flip = False # Disable flipping on each rc loop, since callback already flips
    
    def trial_prep(self):
        # Clear the screen of stimuli before the trial start
        clear()
        
        # Determine image and image name for trial
        self.image_name  = self.trial_factors[P.trial_number-1][0]
        self.arrangement = self.images[self.image_name]

        # infer which mask to use and retrieve it
        self.mask_type = self.trial_factors[P.trial_number-1][1]
        try:
            self.mask = self.masks[self.mask_type]
        except KeyError as e:
            self.mask = None
            
        # Reset warning signal flag
        self.warning_played = False
        
        # Display trial start message and perform drift correct after keypress
        blit(self.trial_start_msg, 5, P.screen_c)
        flip()
        any_key()
        self.el.drift_correct()

    def trial(self):

        if P.development_mode:
            print(self.image_name, self.mask_type)
        
        self.rc.collect()
        resp = self.rc.keypress_listener.response()

        return {"trial_num":   P.trial_number,
                "block_num":   P.block_number,
                "arrangement": self.image_name,
                "mask_type":   self.mask_type}

    def trial_clean_up(self):
        pass

    def clean_up(self):
        # Give the RA the choice of logging or discarding combination of
        # factors used on last trial
        done_1 = message("Experiment session complete.", 'q_and_a', blit_txt=False)
        done_2 = message("Log trial factor set? (Y/N)", 'q_and_a', blit_txt=False)
        response_made = None
        
        while not response_made:
            fill()
            blit(done_1, 5, (P.screen_c[0], P.screen_c[1] - 40))
            blit(done_2, 5, (P.screen_c[0], P.screen_c[1] + 40))
            flip()
            # There really should be a "get next keypress" function
            for e in pump(True):
                if e.type == sdl2.SDL_KEYDOWN:
                    keypress = e.key.keysym.sym
                    if keypress == sdl2.SDLK_y:
                        response_made = "Y"
                        break
                    elif keypress == sdl2.SDLK_n:
                        response_made = "N"
                        break
                        
        if response_made == "Y":
            with open(self.completed_csv,"a") as f:
                writer = csv.writer(f)
                writer.writerow(sum(self.trial_factors, ()))
        

    def mask(self, diameter, mask_type):
        MASK_COLOR = NEUTRAL_COLOR
        diameter   = deg_to_px(diameter)
        blur_width = self.mask_blur_width
        
        if mask_type != "none":
            
            if mask_type == PERIPHERAL:
                bg_width   = P.screen_x * 2
                bg_height  = P.screen_y * 2
                inner_fill = TRANSPARENT
                outer_fill = OPAQUE
                
            elif mask_type == CENTRAL:
                bg_width   = diameter + blur_width * 4 + 2
                bg_height  = bg_width
                inner_fill = OPAQUE
                outer_fill = TRANSPARENT
                
            # Create solid background
            bg = Image.new('RGB', (bg_width, bg_height), MASK_COLOR[:3])
    
            # Create an alpha mask
            r  = diameter // 2
            x1 = (bg_width  // 2) - r
            y1 = (bg_height // 2) - r
            x2 = (bg_width  // 2) + r
            y2 = (bg_height // 2) + r
            alpha_mask = Image.new('L', (bg_width, bg_height), outer_fill)
            ImageDraw.Draw(alpha_mask).ellipse((x1, y1, x2, y2), fill=inner_fill)
            alpha_mask = alpha_mask.filter( ImageFilter.GaussianBlur(blur_width) )
    
            # Apply mask to background and render
            bg.putalpha(alpha_mask)
            mask = aggdraw_to_numpy_surface(bg)
            
        return mask
        
    def get_trial_factors(self):
        """
        Function allow for counterbalancing the order and combinations of trial
        factors between participants.
        
        """
        
        # Generate full set of possible sets of arrangement/mask combinations
        all_combinations = []
        img_orders  = list(permutations(self.image_names,  3))
        mask_orders = list(permutations(self.mask_types,   3))
    
        for i in list(product(img_orders, mask_orders)):
            combination_ordered = sum( zip(i[0], i[1]), () )
            all_combinations.append(combination_ordered)
    
        # Load csv containing previously run combinations (if it exists)
        completed_combinations = []
        try:
            with open(self.completed_csv,"r") as f:
                completed = csv.reader(f)
                next(completed) # skip over header
                for row in completed:
                    completed_combinations.append(tuple(row))
        except IOError:
            # if completed.csv does not exist, create it and add header
            with open(self.completed_csv,"w+") as f:
                writer = csv.writer(f)
                header = ['1st_image','1st_mask','2nd_image','2nd_mask','3rd_image','3rd_mask']
                writer.writerow(header)
    
        # Determine which factor combinations/orders have been run before and
        # randomly select a factor set that hasn't been done yet
        remaining_combinations = list(set(all_combinations)-set(completed_combinations))
        print "\nRemaining combinations: {0}".format(len(remaining_combinations))
        try:
            i = random.choice(remaining_combinations)
        except IndexError:
            err_str = ("All possible combinations of trial factors have already been run. "
                       "If you wish to run more participants, remove the existing "
                       "'completed.csv' file in the ExpAssets/Local/ directory and launch "
                       "the experiment program again.")
            print(err_str)
            self.quit()
            
        # Group arrangement/mask combinations for each trial into tuples
        factor_set = [ (i[0],i[1]), (i[2],i[3]), (i[4],i[5]) ]
        return factor_set

    def screen_refresh(self):
        if self.evm.trial_time >= self.warning_onset and not self.warning_played:
            self.warning_signal.play()
            self.warning_played = True
        position = self.el.gaze()
        fill()
        blit(self.arrangement, 5, P.screen_c)
        if not position:
            clear()
        else:
            if self.mask is not None:
                blit(self.mask, 5, position)
        flip()

