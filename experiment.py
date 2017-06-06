__author__ = "Jon Mulle & Austin Hurst"

import klibs
from klibs.KLConstants import *
from klibs import P
from klibs.KLUtilities import *
from klibs.KLUserInterface import any_key
from klibs.KLGraphics import aggdraw_to_numpy_surface, fill, flip, blit, clear
#from klibs.KLNumpySurface import *
from klibs.KLCommunication import message, alert
from klibs.KLKeyMap import KeyMap

from PIL import Image, ImageDraw, ImageFilter
import random
import sdl2


"""
DEFINITIONS & SHORTHAND THAT CLEAN UP THE READABILITY OF THE CODE BELOW
"""
#  Fixation positions calculated in FigureGroundSearch.__init__() based on current screen dimensions

CIRCLE = "circle"
SQUARE = "square"
LOCAL = "local"
GLOBAL = "global"
OR_UP = "ROTATED_0_DEG"
OR_RIGHT = "ROTATED_90_DEG"
OR_DOWN = "ROTATED_180_DEG"
OR_LEFT = "ROTATED_270_DEG"
CENTRAL = "central"
PERIPHERAL = "peripheral"
SEARCH_RESPONSE_KEYS = "FGSearch_response"
BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)
RED = (255, 0, 0, 80)
GREEN = (0, 255, 0, 80)
BLUE = (0, 0, 255, 80)
DARK_GREY= (45, 45, 45, 255)
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

class FigureGroundSearch(klibs.Experiment):
    stim_size = 12  # degrees of visual angle
    stim_pad = 0.8 # degrees of visual angle
    mask_blur_width = 4  # pixels
    maximum_mask_size = 0  # automatically set at run time, do not change
    search_time = 30  # seconds
    fixation = None  # chosen randomly each trial
    bg_element_size = 0.8  # degrees of visual angle
    bg_element_pad = 0.6  # degrees of visual angle
    orientations = [0, 90, 180, 270]

    neutral_color = P.default_fill_color
    pseudo_mask = None
    trial_start_msg = None

    #  trial vars
    timed_out = False

    textures = {}
    figures = {}
    stimuli = {}
    masks = {}

    #  debug vars
    gaze_debug_dot = None

    # dynamic trial vars
    mask = None
    mask_label = None
    figure = None
    orientation = None

    def __init__(self, *args, **kwargs):
        super(FigureGroundSearch, self).__init__(*args, **kwargs)

    def setup(self):
        
        self.fixation_top = (P.screen_x // 2, P.screen_y // 4)
        self.fixation_central = P.screen_c
        self.fixation_bottom = (P.screen_x // 2, 3 * P.screen_y // 4)
        self.exp_meta_factors = {"fixation": [self.fixation_top, self.fixation_central, self.fixation_bottom]}
        
        self.txtm.add_style('q_and_a', 48, WHITE)
        self.stim_pad = deg_to_px(self.stim_pad)
        self.__generate_masks()
        self.__generate_stimuli()
        self.__generate_fixations()

        self.keymap = KeyMap(SEARCH_RESPONSE_KEYS, ["z","/"], ["circle", "square"], [sdl2.SDLK_z, sdl2.SDLK_SLASH])

        # debugging dot for gaze coordinates
        gaze_debug_dot = Image.new(RGBA, (5, 5), TRANSPARENT)
        ImageDraw.Draw(gaze_debug_dot , RGBA).ellipse((0, 0, 5, 5), RED, BLACK)
        self.gaze_debug_dot = aggdraw_to_numpy_surface(gaze_debug_dot)

        padded_stim_size_px = deg_to_px(self.stim_size) + self.stim_pad + 1
        pseudo_mask = Image.new(RGBA, (padded_stim_size_px, padded_stim_size_px), NEUTRAL_COLOR)
        self.trial_start_msg = message("Press any key to advance...", 'default', blit_txt=False)
        self.pseudo_mask = aggdraw_to_numpy_surface(pseudo_mask)
        self.el.setup()

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

    def __generate_stimuli(self):
        clear()
        message("Generating stimuli...","q_and_a", location=P.screen_c, registration=5, flip_screen=True)
        stimuli_labels = [[(False, 0), (CIRCLE, 0)], [(False, 90), (CIRCLE, 0)], [(False, 180), (CIRCLE, 0)],
                          [(False, 270), (CIRCLE, 0)],
                          [(False, 0), (SQUARE, 0)], [(False, 90), (SQUARE, 0)], [(False, 180), (SQUARE, 0)],
                          [(False, 270), (SQUARE, 0)],
                          [(CIRCLE, 0), (False, 0)], [(CIRCLE, 0), (False, 90)], [(CIRCLE, 0), (False, 180)],
                          [(CIRCLE, 0), (False, 270)],
                          [(SQUARE, 0), (False, 0)], [(SQUARE, 0), (False, 90)], [(SQUARE, 0), (False, 180)],
                          [(SQUARE, 0), (False, 270)]]

        for sl in stimuli_labels:
            stim = self.texture(sl[1][0], sl[1][1])
            figure = self.figure(sl[0][0], sl[0][1])
            stim.mask(figure, (0, 0))
            fig_text = sl[0][0] if sl[0][0] in (CIRCLE, SQUARE) else "D_%s" % sl[0][1]
            texture_text = sl[1][0] if sl[1][0] in (CIRCLE, SQUARE) else "D_%s" % sl[1][1]
            self.stimuli["{0}_{1}".format(fig_text, texture_text)] = stim.render()

    def __generate_fixations(self):
        self.exp_meta_factors['fixation'] = [P.screen_c,
                                               (P.screen_c[0], int(P.screen_y * 0.25)),
                                               (P.screen_c[0], int(P.screen_y * 0.75))]
        dc_box_size = 50
        # left drift correct box
        dc_top_tl = (int(0.5 * P.screen_x - 0.5 * dc_box_size), int(0.25 * P.screen_y - 0.5 * dc_box_size))
        dc_top_br = (int(0.5 * P.screen_x + 0.5 * dc_box_size), int(0.25 * P.screen_y + 0.5 * dc_box_size))
        self.el.add_boundary('dc_top_box', [dc_top_tl, dc_top_br], RECT_BOUNDARY)
        # right drift correct box
        dc_bottom_tl = (int(0.5 * P.screen_x - 0.5 * dc_box_size), int(0.75 * P.screen_y - 0.5 * dc_box_size))
        dc_bottom_br = (int(0.5 * P.screen_x + 0.5 * dc_box_size), int(0.75 * P.screen_y + 0.5 * dc_box_size))
        self.el.add_boundary('dc_bottom_box', [dc_bottom_tl, dc_bottom_br], RECT_BOUNDARY)
        # middle drift correct box
        dc_middle_tl = (int(0.5 * P.screen_x - 0.5 * dc_box_size), int(0.5 * P.screen_y - 0.5 * dc_box_size))
        dc_middle_br = (int(0.5 * P.screen_x + 0.5 * dc_box_size), int(0.5 * P.screen_y + 0.5 * dc_box_size))
        self.el.add_boundary('dc_middle_box', [dc_middle_tl, dc_middle_br], RECT_BOUNDARY)

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
        self.orientation = random.choice(self.orientations)
        self.fixation = tuple(random.choice(self.exp_meta_factors['fixation']))
        if self.fixation[1] < P.screen_c[1]:
            self.fixation_bounds = "dc_top_box"
        elif self.fixation[1] > P.screen_c[1]:
            self.fixation_bounds = "dc_bottom_box"
        else:
            self.fixation_bounds = "dc_middle_box"

        # infer which mask & stim to use and retrieve them
        self.figure = self.target_shape if self.target_level == LOCAL else False

        if self.figure:
            stim_label = "{0}_D_{1}".format(self.target_shape, self.orientation)
        else:
            stim_label = "D_{0}_{1}".format(self.orientation, self.target_shape)
        self.figure = self.stimuli[stim_label]
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
        trial_factors: 1 = mask_type, 2 = mask_size, 3 = target_level, 4 = target_shape]
        """

        print(self.mask_type, self.target_level, self.mask_size, self.target_shape)
        self.rc.collect()
        resp = self.rc.keypress_listener.response()
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

        return {"practicing": P.practicing,
                "response": resp[0],
                "rt": float(resp[1]),
                "mask_type": self.mask_type,
                "mask_size": self.mask_size,
                "local": self.target_shape if self.target_level == LOCAL else "D",
                "global": self.target_shape if self.target_level == GLOBAL else "D",
                "d_orientation": self.orientation,
                "trial_num": P.trial_number,
                "block_num": P.block_number,
                "initial_fixation": initial_fixation}

    def trial_clean_up(self):
        self.fixation = None

    def clean_up(self):
        pass

    def texture(self, texture_figure, orientation=None):
        grid_size = (deg_to_px(self.stim_size) + self.stim_pad) * 2
        stim_offset = self.stim_pad // 2
        dc = Image.new(RGBA, (grid_size, grid_size), TRANSPARENT)
        stroke_width = 2  #px
        grid_cell_size = deg_to_px(self.bg_element_size + self.bg_element_pad)
        grid_cell_count = grid_size // grid_cell_size
        stim_offset += (grid_size % grid_cell_size) // 2  # split grid_size %% cells over pad


        # Visual Representation of the Texture Rendering Logic
        # <-------G-------->
        #  _______________   ^
        # |       O       |  |    O = element_offset, ie. 1/2 bg_element_padding
        # |     _____     |  |    E = element (ie. circle, square, D, etc.)
        # |    |     |    |  |    G = one grid length
        # | O  |  E  |  O |  G
        # |    |_____|    |  |
        # |               |  |
        # |_______O_______|  |
        #                    v

        element_offset = self.bg_element_pad // 2  # so as to apply padding equally on all sides of bg elements
        for col in range(0, grid_cell_count):
            for row in range(0, grid_cell_count):
                pump()
                top_out = int(row * grid_cell_size + element_offset + stim_offset)
                top_in = top_out + stroke_width  # ie. top_inner
                left_out = int(col * grid_cell_size + element_offset + stim_offset)
                left_in = left_out+ stroke_width
                bottom_out = int(top_out + deg_to_px(self.bg_element_size))
                bottom_in = bottom_out - stroke_width
                right_out = int(left_out + deg_to_px(self.bg_element_size))
                right_in = right_out - stroke_width

                if texture_figure == CIRCLE:
                    ImageDraw.Draw(dc, RGBA).ellipse((left_out, top_out, right_out, bottom_out), WHITE)
                    ImageDraw.Draw(dc, RGBA).ellipse((left_in, top_in, right_in, bottom_in), NEUTRAL_COLOR)
                elif texture_figure == SQUARE:
                    ImageDraw.Draw(dc, RGBA).rectangle((left_out, top_out, right_out, bottom_out), WHITE)
                    ImageDraw.Draw(dc, RGBA).rectangle((left_in, top_in, right_in, bottom_in), NEUTRAL_COLOR)
                elif texture_figure is False:

                    half_el_width = int(0.5 * deg_to_px(self.bg_element_size))
                    rect_right = right_out - half_el_width
                    ImageDraw.Draw(dc, RGBA, ).ellipse((left_out, top_out, right_out, bottom_out), WHITE)
                    ImageDraw.Draw(dc, RGBA, ).ellipse((left_in, top_in, right_in, bottom_in), NEUTRAL_COLOR)
                    ImageDraw.Draw(dc, RGBA, ).rectangle((left_out, top_out, rect_right, bottom_out), WHITE)
                    ImageDraw.Draw(dc, RGBA, ).rectangle((left_in, top_in, rect_right, bottom_in), NEUTRAL_COLOR)
        dc = dc.resize((grid_size // 2, grid_size // 2), Image.ANTIALIAS)
        dc = dc.rotate(orientation)

        return aggdraw_to_numpy_surface(dc)

    def figure(self, figure_shape, orientation):

        stim_size_px = deg_to_px(self.stim_size)
        half_pad = self.stim_pad
        pad = 2 * self.stim_pad
        tl_fig = pad
        br_fig = 2 * stim_size_px
        rect_right = br_fig - stim_size_px
        dc_size = (stim_size_px + half_pad) * 2
        dc = Image.new(RGBA,  (dc_size, dc_size), TRANSPARENT)

        if figure_shape == CIRCLE:
            ImageDraw.Draw(dc, RGBA).ellipse((tl_fig, tl_fig, br_fig, br_fig), WHITE)
        if figure_shape == SQUARE:
            ImageDraw.Draw(dc, RGBA).rectangle((tl_fig, tl_fig, br_fig, br_fig), WHITE)
        if figure_shape is False:
            ImageDraw.Draw(dc, RGBA).ellipse((tl_fig, tl_fig, br_fig, br_fig), WHITE)
            ImageDraw.Draw(dc, RGBA).rectangle((tl_fig, tl_fig, rect_right, br_fig), WHITE)
        if orientation > 0: dc = dc.rotate(orientation)
        cookie_cutter = aggdraw_to_numpy_surface(dc.resize((dc_size // 2, dc_size // 2), Image.ANTIALIAS))
        dough = Image.new(RGBA,  (dc_size // 2, dc_size // 2), WHITE)
        ImageDraw.Draw(dough, RGBA).rectangle((0, 0, dc_size // 2, dc_size // 2), WHITE)
        dough = aggdraw_to_numpy_surface(dough)
        dough.mask(cookie_cutter, (0, 0))

        return dough

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
        blit(self.figure, 5, P.screen_c)
        if self.mask_type == PERIPHERAL and not self.el.within_boundary(self.mask_label, EL_GAZE_POS):
            clear()
        elif not position:
            clear()
        else:
            if self.mask is not None:
                blit(self.mask, 5, position)
            #if not P.eye_tracker_available:
            #   blit(self.gaze_debug_dot, 5, mouse_pos())
        flip()

