__author__ = "Jon Mulle & Austin Hurst"

import klibs
from klibs.KLConstants import *
from klibs import P
from klibs.KLUtilities import *
from klibs.KLUserInterface import any_key
from klibs.KLGraphics.KLNumpySurface import NumpySurface as ns
from klibs.KLGraphics import aggdraw_to_numpy_surface, fill, flip, blit, clear
from klibs.KLCommunication import message, alert
from klibs.KLKeyMap import KeyMap

import os
from PIL import Image, ImageDraw, ImageFilter
import random
import sdl2
import time


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
    mask_blur_width = 4  # pixels
    maximum_mask_size = 0  # automatically set at run time, do not change
    search_time = 120  # seconds

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
        
        # Initialize keymap for recording responses
        
        self.keymap = KeyMap("FGSearch_response", ["z","/"], ["circle", "square"], [sdl2.SDLK_z, sdl2.SDLK_SLASH])
        
        # Load in all images in arrangements folder
        
        img_dir = os.path.join(P.image_dir, "arrangements")
        img_names = next(os.walk(img_dir))[2]
        
        self.images = []
        for img_name in img_names:
            if not img_name.startswith('.'):
                img = ns(os.path.join(img_dir, img_name))
                self.images.append([img_name, img.render()])
        
        # Generate masks for the experiment
        
        self.__generate_masks()
        
        self.el.setup()
        

    def __generate_masks(self):
        smaller_than_screen = True
        while smaller_than_screen:
            self.maximum_mask_size += 1
            new_max_mask_px = deg_to_px(self.maximum_mask_size) + self.mask_blur_width * 4 + 2
            if new_max_mask_px > P.screen_y:
                smaller_than_screen = False
                self.maximum_mask_size -= 1
        for size in self.trial_factory.exp_factors[0][1]:
            if size > self.maximum_mask_size:
                e_str = "The maximum mask size this monitor can support is {0} degrees.".format(self.maximum_mask_size)
                raise ValueError(e_str)
                
        self.masks = {}
        for size in self.trial_factory.exp_factors[0][1]:
            pump()
            self.masks["{0}_{1}".format(CENTRAL, size)] = self.mask(size, CENTRAL).render()
            self.masks["{0}_{1}".format(PERIPHERAL, size)] = self.mask(size, PERIPHERAL).render()

    def block(self):
        pass
    
    def setup_response_collector(self):
        self.rc.display_callback = self.screen_refresh
        self.rc.terminate_after = [self.search_time, TK_S]
        self.rc.uses([RC_KEYPRESS])
        self.rc.keypress_listener.interrupts = True
        self.rc.keypress_listener.key_map = self.keymap
        self.rc.flip = False # Disable flipping on each rc loop, since callback already flips
    
    def trial_prep(self):
        # Clear the screen of stimuli before the trial start
        clear()
        
        # Determine image and image name for trial
        self.arrangement = random.choice(self.images)

        # infer which mask to use and retrieve it
        self.mask_label = "{0}_{1}".format(self.mask_type, self.mask_size)
        try:
            self.mask = self.masks[self.mask_label]
        except KeyError as e:
            self.mask = None
        
        # Display trial start message and perform drift correct after keypress
        blit(self.trial_start_msg, 5, P.screen_c)
        flip()
        any_key()
        self.el.drift_correct()

    def trial(self):

        if P.development_mode:
            print(self.mask_type, self.mask_size)
        
        self.rc.collect()
        resp = self.rc.keypress_listener.response()
        
        if P.development_mode:
            print(resp)     

        return {"trial_num":  P.trial_number,
                "block_num":  P.block_number,
                "image":      self.arrangement[0],
                "mask_type":  self.mask_type,
                "mask_size":  self.mask_size,
                "response":   resp[0],
                "rt":         float(resp[1])}

    def trial_clean_up(self):
        pass

    def clean_up(self):
        pass
        

    def mask(self, diameter, mask_type):
        MASK_COLOR = NEUTRAL_COLOR
        diameter = deg_to_px(diameter)
        blur_width = self.mask_blur_width
        
        if mask_type != "none":
            
            if mask_type == PERIPHERAL:
                bg_width  = P.screen_x * 2
                bg_height = P.screen_y * 2
                inner_fill = TRANSPARENT
                outer_fill = OPAQUE
                
            elif mask_type == CENTRAL:
                bg_width  = diameter + blur_width * 4 + 2
                bg_height = bg_width
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

    def screen_refresh(self):
        position = self.el.gaze()
        fill()
        blit(self.arrangement[1], 5, P.screen_c)
        if not position:
            clear()
        else:
            if self.mask is not None:
                blit(self.mask, 5, position)
        flip()

