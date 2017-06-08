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


"""
DEFINITIONS & SHORTHAND THAT CLEAN UP THE READABILITY OF THE CODE BELOW
"""
#  Fixation positions calculated in PictureDrawingSearch.__init__() based on current screen dimensions

CENTRAL    = "central"
PERIPHERAL = "peripheral"

BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)
NEUTRAL_COLOR = P.default_fill_color
TRANSPARENT = (0, 0, 0, 0)
RGBA = "RGBA"

"""
EXPERIMENT FACTORS & 'METAFACTORS' (ie. between-block variations as against between-trial)
"""

"""
This code defines a  class that 'extends' the basic KLExperiment class.
The experiment itself is actually *run* at the end of this document, after it's been defined.
"""

class PictureDrawingSearch(klibs.Experiment):
    stim_size = 12  # degrees of visual angle
    stim_pad = 0.8 # degrees of visual angle
    mask_blur_width = 4  # pixels
    maximum_mask_size = 0  # automatically set at run time, do not change
    search_time = 30  # seconds
    fixation = None  # chosen randomly each trial
    bg_element_size = 0.8  # degrees of visual angle
    bg_element_pad = 0.6  # degrees of visual angle

    neutral_color = P.default_fill_color
    pseudo_mask = None
    trial_start_msg = None

    #  trial vars
    timed_out = False

    masks = {}

    # dynamic trial vars
    mask = None
    mask_label = None

    def __init__(self, *args, **kwargs):
        super(PictureDrawingSearch, self).__init__(*args, **kwargs)

    def setup(self):
        
        # Stimulus sizes
        
        self.stim_pad = deg_to_px(self.stim_pad)
        padded_stim_size_px = deg_to_px(self.stim_size) + self.stim_pad + 1
        self.txtm.add_style('q_and_a', 48, WHITE)
        
        # Initialize keymap for recording responses
        
        self.keymap = KeyMap("FGSearch_response", ["z","/"], ["circle", "square"], [sdl2.SDLK_z, sdl2.SDLK_SLASH])
        
        # Load in images
        
        img_dir = os.path.join(P.image_dir, "arrangements")
        img_names = next(os.walk(img_dir))[2]
        
        self.images = []
        for img_name in img_names:
            if not img_name.startswith('.'):
                img = ns(os.path.join(img_dir, img_name))
                self.images.append([img_name, img.render()])
        
        # Generate masks, stimuli, and fixations for the experiment
        
        self.__generate_masks()
        self.__generate_fixations()

        pseudo_mask = Image.new(RGBA, (padded_stim_size_px, padded_stim_size_px), NEUTRAL_COLOR)
        self.pseudo_mask = aggdraw_to_numpy_surface(pseudo_mask)
        self.trial_start_msg = message("Press any key to advance...", 'default', blit_txt=False)

    def __generate_masks(self):
        smaller_than_screen = True
        while smaller_than_screen:
            self.maximum_mask_size += 1
            new_max_mask_px = deg_to_px(self.maximum_mask_size) + deg_to_px(self.stim_size) // 2 + self.stim_pad // 2
            if new_max_mask_px > P.screen_y:
                smaller_than_screen = False
                self.maximum_mask_size -= 1
        for size in self.trial_factory.exp_factors[2][1]:
            if size > self.maximum_mask_size:
                e_str = "The maximum mask size this monitor can support is {0} degrees.".format(self.maximum_mask_size)
                raise ValueError(e_str)
        clear()
        message("Rendering masks...", "q_and_a", location=P.screen_c, registration=5, flip_screen=True)
        self.masks = {}
        for size in self.trial_factory.exp_factors[2][1]:
            pump()
            self.masks["{0}_{1}".format(CENTRAL, size)] = self.mask(size, CENTRAL).render()
            self.masks["{0}_{1}".format(PERIPHERAL, size)] = self.mask(size, PERIPHERAL).render()

    def __generate_fixations(self):
        
        # Locations
        self.fixation_top     = (P.screen_x / 2,  1 * P.screen_y / 4)
        self.fixation_central = (P.screen_x / 2,  2 * P.screen_y / 4)
        self.fixation_bottom  = (P.screen_x / 2,  3 * P.screen_y / 4)
        self.exp_meta_factors = {"fixation": [self.fixation_top, self.fixation_central, self.fixation_bottom]}
        
        dc_box_size = 50 # Size of drift correct bounds in pixels
        dc_bounds   = dc_box_size / 2
        
        # top drift correct box
        dc_top_tl     = (self.fixation_top[0] - dc_bounds, self.fixation_top[1] - dc_bounds)
        dc_top_br     = (self.fixation_top[0] + dc_bounds, self.fixation_top[1] + dc_bounds)
        self.el.add_boundary('dc_top_box', [dc_top_tl, dc_top_br], RECT_BOUNDARY)
        # central drift correct box
        dc_central_tl = (self.fixation_central[0] - dc_bounds, self.fixation_central[1] - dc_bounds)
        dc_central_br = (self.fixation_central[0] + dc_bounds, self.fixation_central[1] + dc_bounds)
        self.el.add_boundary('dc_central_box', [dc_central_tl, dc_central_br], RECT_BOUNDARY)
        # bottom drift correct box
        dc_bottom_tl  = (self.fixation_bottom[0] - dc_bounds, self.fixation_bottom[1] - dc_bounds)
        dc_bottom_br  = (self.fixation_bottom[0] + dc_bounds, self.fixation_bottom[1] + dc_bounds)
        self.el.add_boundary('dc_bottom_box', [dc_bottom_tl, dc_bottom_br], RECT_BOUNDARY)

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
        clear()
        # choose randomly varying parts of trial
        
        self.fixation = tuple(random.choice(self.exp_meta_factors['fixation']))
        if self.fixation[1] < P.screen_c[1]:
            self.fixation_bounds = "dc_top_box"
        elif self.fixation[1] > P.screen_c[1]:
            self.fixation_bounds = "dc_bottom_box"
        else:
            self.fixation_bounds = "dc_central_box"
            
        # Determine image and image name for trial
        
        self.arrangement = random.choice(self.images)

        # infer which mask to use and retrieve it
        self.mask_label = "{0}_{1}".format(self.mask_type, self.mask_size)
        try:
            self.mask = self.masks[self.mask_label]
        except KeyError as e:
            self.mask = None  # for the no mask condition, easier than creating empty keys in self.masks
        blit(self.trial_start_msg, 5, P.screen_c)
        flip()
        any_key()
        self.el.drift_correct(self.fixation, self.fixation_bounds)

    def trial(self):
        """
        trial_factors: 1 = mask_type, 2 = target_level, 3 = mask_size, 4 = target_shape]
        """
        if P.development_mode:
            print(self.mask_type, self.target_level, self.mask_size, self.target_shape)
        
        self.rc.collect()
        resp = self.rc.keypress_listener.response()
        
        if P.development_mode:
            print(resp)

        # handle timeouts
        if resp[0] == TIMEOUT:
            clear()
            alert("Too slow!", False, 1)
            clear()

        #  create readable data as fixation is currrently in (x,y) coordinates

        if self.fixation == self.fixation_top:
            initial_fixation = "TOP"
        elif self.fixation == self.fixation_central:
            initial_fixation = "CENTRAL"
        else:
            initial_fixation = "BOTTOM"

        return {"trial_num":  P.trial_number,
                "block_num":  P.block_number,
                "practicing": P.practicing,
                "image":      self.arrangement[0],
                "mask_type":  self.mask_type,
                "mask_size":  self.mask_size,
                "response":   resp[0],
                "rt":         float(resp[1]),
                "init_fix":   initial_fixation}

    def trial_clean_up(self):
        self.fixation = None

    def clean_up(self):
        pass
        

    def mask(self, diameter, mask_type):
        MASK_COLOR = NEUTRAL_COLOR
        diameter_deg = diameter
        diameter = deg_to_px(diameter)
        stim_size = deg_to_px(self.stim_size)
        pad =  self.stim_pad  # note, just borrowing this padding value, it's use is not related to the stimuli at all

        if mask_type == PERIPHERAL:
            # Create maskable space hack:
            #   Minimize the size of the peripheral mask by simply painting the screen a neutral color any time
            #   the peripheral mask would only be revealing a neutral color.
            r = diameter // 2 + stim_size // 2
            scx =  P.screen_c[0]
            scy =  P.screen_c[1]
            self.el.add_boundary("{0}_{1}".format(mask_type, diameter_deg), [(scx - r, scy - r), (scx + r, scy + r)], RECT_BOUNDARY)


            # Create solid background
            bg_size = diameter + pad + 2 * stim_size
            bg = Image.new(RGBA, (bg_size, bg_size), MASK_COLOR)


            # Create an alpha mask
            tl = pad // 2 + stim_size
            br = bg_size - tl
            alpha_mask = Image.new(RGBA, (bg_size, bg_size), TRANSPARENT)
            ImageDraw.Draw(alpha_mask, RGBA).ellipse((tl, tl, br, br), WHITE, MASK_COLOR)
            alpha_mask = alpha_mask.filter( ImageFilter.GaussianBlur(self.mask_blur_width) )
            alpha_mask = aggdraw_to_numpy_surface(alpha_mask)
            print(bg_size, tl, br)

            # render mask
            mask = aggdraw_to_numpy_surface(bg)
            mask.mask(alpha_mask)

        if mask_type == CENTRAL:
            # Create solid background
            bg_size = diameter + pad
            bg = Image.new(RGBA, (bg_size, bg_size), MASK_COLOR)
            tl = pad // 2
            br = bg_size - tl

            # Create an alpha mask
            alpha_mask = Image.new(RGBA, (bg_size, bg_size), WHITE)
            ImageDraw.Draw(alpha_mask, RGBA).ellipse((tl, tl, br, br), BLACK)
            alpha_mask = aggdraw_to_numpy_surface(alpha_mask.filter(ImageFilter.GaussianBlur(self.mask_blur_width)))

            # render mask
            mask = aggdraw_to_numpy_surface(bg)
            mask.mask(alpha_mask, grey_scale=True)

        return mask

    def screen_refresh(self):
        position = self.el.gaze()
        fill()
        blit(self.arrangement[1], 5, P.screen_c)
        if self.mask_type == PERIPHERAL and not self.el.within_boundary(self.mask_label, EL_GAZE_POS):
            clear()
        elif not position:
            clear()
        else:
            if self.mask is not None:
                blit(self.mask, 5, position)
        flip()

