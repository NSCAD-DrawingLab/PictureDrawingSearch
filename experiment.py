__author__ = "Jon Mulle & Austin Hurst"

import klibs
from klibs.KLConstants import *
from klibs import P
from klibs.KLUtilities import *
from klibs.KLUserInterface import any_key, key_pressed, ui_request
from klibs.KLGraphics import fill, flip, blit, clear
from klibs.KLAudio import AudioClip
from klibs.KLCommunication import message, alert
from klibs.KLKeyMap import KeyMap
from klibs.KLTime import CountDown

from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import os
import sdl2

# For keeping track of which possible trial factor sets have already been run
from itertools import permutations, product
import csv
import random
import time

"""
DEFINITIONS & SHORTHAND THAT CLEAN UP THE READABILITY OF THE CODE BELOW
"""

CENTRAL    = "central"
PERIPHERAL = "peripheral"

BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)
RED = (0, 0, 200, 255)
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
    gaze_timeout = 0.1 # 100 ms timeout if gaze off screen
    
    image_names = ["warmup.png", "image_1.png", "image_2.png", "image_3.png"]
    mask_types  = ["none", "central", "peripheral"]
    masks = {}

    # dynamic trial vars
    mask = None
    mask_label = None
    fixation = None

    def __init__(self, *args, **kwargs):
        super(PictureDrawingSearch, self).__init__(*args, **kwargs)

    def setup(self):
        
        # Initialize text styles and display loading screen
        
        self.txtm.add_style('q_and_a', 48, WHITE)
        self.txtm.add_style('instructions', 40, WHITE)
        self.txtm.add_style('warmup', 36, RED)
        
        fill()
        message("Loading...", "q_and_a", location=P.screen_c, registration=5)
        flip()
        
        # Generate text from instructions files
        
        self.trial_start_msg = message("Press any key to advance...", 'default', blit_txt=False)
        
        text_width = int(P.screen_x * 0.80)
        instructions_file_1 = os.path.join(P.resources_dir, "text", "instructions_1.txt")
        instructions_file_2 = os.path.join(P.resources_dir, "text", "instructions_2.txt")
        instructions_file_3 = os.path.join(P.resources_dir, "text", "instructions_3.txt")
        instructions_file_4 = os.path.join(P.resources_dir, "text", "instructions_4.txt")
        instructions_file_5 = os.path.join(P.resources_dir, "text", "instructions_5.txt")
        self.instructions_1 = message(
            open(instructions_file_1).read(), 'instructions', wrap_width=text_width, blit_txt=False
        )
        self.instructions_2 = message(
            open(instructions_file_2).read(), 'instructions', wrap_width=text_width, blit_txt=False
        )
        self.instructions_3 = message(
            open(instructions_file_3).read(), 'instructions', wrap_width=text_width, blit_txt=False
        )
        self.instructions_4 = message(
            open(instructions_file_4).read(), 'instructions', wrap_width=text_width, blit_txt=False
        )
        self.instructions_5 = message(
            open(instructions_file_5).read(), 'instructions', wrap_width=text_width, blit_txt=False
        )
        
        self.warmup_txt = {}
        for tool in ['pencil', 'charcoal', 'smudger', 'eraser']:
            text = "Please test out the {0} tool.".format(tool)
            self.warmup_txt[tool] = message(text, 'warmup', blit_txt=False)
        self.warmup_txt['any'] = message(
            "Please continue drawing with the tool(s) of your choice.", 'warmup', blit_txt=False
        )
        
        # Load in warning tone indicating time almost up
        
        signal_file = os.path.join(P.resources_dir, "audio", "Ping.wav")
        self.warning_signal = AudioClip(signal_file)
        self.first_warning_onset = 540 
        self.second_warning_onset = 840 # seconds after start of trial
        
        # Initialize keymap for skipping trials (for dev convenience)
        
        self.keymap = KeyMap("skip_trial", ["Del"], ["skipped"], [sdl2.SDLK_DELETE])
        
        # Load in all arrangements in images folder
        
        self.images = {}
        for img_name in self.image_names:
            img = Image.open(os.path.join(P.image_dir, img_name))
            img_aspect = img.size[0]/float(img.size[1])
            screen_aspect = P.screen_x/float(P.screen_y)
            if img_aspect > screen_aspect:
                scaled_size = (int(P.screen_y*img_aspect), P.screen_y)
            else:
                scaled_size = (P.screen_x, int(P.screen_x/img_aspect))
            img = img.convert('RGBA').resize(scaled_size, Image.BILINEAR)
            self.images[img_name] = np.asarray(img)
                
        # Check which combinations of factors previous participants have done
        # and get a set of factors that hasn't been run yet
        
        self.completed_csv = os.path.join(P.local_dir, "completed.csv")
        self.trial_factors = self.get_trial_factors()
        if P.development_mode:
            print(self.trial_factors)
        
        # Generate masks for the experiment
        
        self.__generate_masks()
        self.mask_off_time = 600 # seconds, i.e. 10 minutes
        
        # Show experiment instructions, calibrate, and run warm-up image
        
        self.show_instruction(self.instructions_1, 5, P.screen_c)
        self.show_instruction(self.instructions_2, 5, P.screen_c)

        self.el.setup() # After second screen, calibrate on EyeLink
        
        self.show_instruction(self.instructions_3, 5, P.screen_c)
        
        self.warm_up()
        
        self.show_instruction(self.instructions_4, 5, P.screen_c)
        
        self.show_instruction(self.instructions_5, 5, P.screen_c)

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
        self.masks["central"]    = self.render_mask(mask_sizes[0], CENTRAL)
        self.masks["peripheral"] = self.render_mask(mask_sizes[1], PERIPHERAL)

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
        self.first_warning_played = False
        self.second_warning_played = False
        
        #Reset gaze offscreen flag
        self.gaze_offscreen = time.time()
        
        # Display trial start message and perform drift correct after keypress
        blit(self.trial_start_msg, 5, P.screen_c)
        flip()
        any_key()
        self.el.drift_correct()


    def trial(self):

        if P.development_mode:
            print(self.image_name, self.mask_type)

        trial_countdown = CountDown(900) # 15 minutes
        while trial_countdown.remaining() > 0:
            q = pump(True)
            if key_pressed(sdl2.SDLK_DELETE, queue=q):
                # press 'Del' to skip trial
                break
            elif key_pressed(sdl2.SDLK_ESCAPE, queue=q):
                # Press 'escape' to pause and calibrate
                trial_countdown.pause()
                self.el.calibrate()
                self.el.drift_correct()
                self.el.start(P.trial_number)
                trial_countdown.resume()
                continue
            
            if trial_countdown.elapsed() >= self.first_warning_onset and not self.first_warning_played:
                self.warning_signal.play()
                self.first_warning_played = True
            if trial_countdown.elapsed() >= self.second_warning_onset and not self.second_warning_played:
                self.warning_signal.play()
                self.second_warning_played = True

            pos = self.el.gaze()
            fill()
            if int(pos[0]) != -32768: # if gaze not lost
                self.gaze_offscreen = time.time()
            if (pos[0] < 0) or (pos[0] > P.screen_x) or (pos[1] < 0) or (pos[1] > P.screen_y):
                pass
            elif (time.time() - self.gaze_offscreen) < self.gaze_timeout:
                blit(self.arrangement, 5, P.screen_c)
                if self.mask is not None and trial_countdown.elapsed() < self.mask_off_time:
                    blit(self.mask, 5, pos)
            flip()
        
        #self.rc.collect()
        
        #resp = self.rc.keypress_listener.response()

        return {
            "trial_num":   P.trial_number,
            "block_num":   P.block_number,
            "arrangement": self.image_name,
            "mask_type":   self.mask_type
        }

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
            q = pump(True)
            if key_pressed(sdl2.SDLK_y, queue=q):
                response_made = "Y"
                break
            elif key_pressed(sdl2.SDLK_n, queue=q):
                response_made = "N"
                break
                        
        if response_made == "Y":
            with open(self.completed_csv,"a") as f:
                writer = csv.writer(f)
                writer.writerow(sum(self.trial_factors, ()))
        

    def render_mask(self, diameter, mask_type):
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
            mask = np.asarray(bg)
            
        return mask
        
    def get_trial_factors(self):
        """
        Function allow for counterbalancing the order and combinations of trial
        factors between participants.
        
        """
        
        # Generate full set of possible sets of arrangement/mask combinations,
        # excluding warmup arrangement
        all_combinations = []
        img_orders  = list(permutations(self.image_names[1:], 3))
        mask_orders = list(permutations(self.mask_types, 3))
    
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
        
    def show_instruction(self, instruction, registration, location):
        fill()
        blit(instruction, registration, location)
        flip()
        smart_sleep(500)
        any_key()
  
    def warm_up(self):
        warmup_timer = CountDown(600, start=True)
        self.first_signal_played = False
        self.second_signal_played = False
        self.third_signal_played = False
        self.fourth_signal_played = False
        while warmup_timer.counting():
            if key_pressed(sdl2.SDLK_DELETE):
                break
            
            t = warmup_timer.elapsed()
            if t < 60:
                tool = 'pencil'
            elif 60 <= t < 120:
            	if not self.first_signal_played:
            		self.warning_signal.play()
            		self.first_signal_played = True
                tool = 'charcoal'
            elif 120 <= t < 180:
            	if not self.second_signal_played:
            		self.warning_signal.play()
            		self.second_signal_played = True
                tool = 'smudger'
            elif 180 <= t < 240:
            	if not self.third_signal_played:
            		self.warning_signal.play()
            		self.third_signal_played = True
                tool = 'eraser'
            else:
                if not self.fourth_signal_played:
            		self.warning_signal.play()
            		self.fourth_signal_played = True
                tool = 'any'
                
            fill()
            blit(self.images['warmup.png'], 5, P.screen_c)
            blit(self.warmup_txt[tool], 1, (30, P.screen_y-30))
            flip()

    def screen_refresh(self):
        if self.evm.trial_time >= self.first_warning_onset and not self.first_warning_played:
            self.warning_signal.play()
            self.first_warning_played = True
        if self.evm.trial_time >= self.second_warning_onset and not self.second_warning_played:
            self.warning_signal.play()
            self.second_warning_played = True
        pos = self.el.gaze()
        fill()
        if int(pos[0]) != -32768: # if gaze not lost
            self.gaze_offscreen = time.time()
        if (pos[0] < 0) or (pos[0] > P.screen_x) or (pos[1] < 0) or (pos[1] > P.screen_y):
            pass
        elif (time.time() - self.gaze_offscreen) < self.gaze_timeout:
            blit(self.arrangement, 5, P.screen_c)
            if self.mask is not None and self.evm.trial_time < self.mask_off_time:
                blit(self.mask, 5, pos)
        flip()
