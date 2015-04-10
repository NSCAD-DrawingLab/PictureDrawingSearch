__author__ = "EXPERIMENTER_NAME"

import klibs
from PIL import Image,ImageDraw, ImageFilter
from klibs import Params
from klibs.KLNumpySurface import *
from klibs.KLUtilities import *
import random
import sdl2

Params.screen_x = 1024
Params.screen_y = 640
Params.default_fill_color = (100, 100, 100, 255)

Params.debug_level = 0
Params.collect_demographics = True
Params.practicing = False
Params.eye_tracking = True
Params.eye_tracker_available = False

Params.blocks_per_experiment = 1
Params.trials_per_block = 96
Params.practice_blocks = None
Params.trials_per_practice_block = None

"""
DEFINITIIONS & SHORTHAND THAT SIMPLY CLEANS UP THE READABILITY OF THE CODE BELOW
"""
BG_CIRCLE = 0
BG_SQUARE = 1
FIG_SQUARE = "FIG_SQUARE"
FIG_CIRCLE = "FIG_CIRCLE"
FIG_D = "FIG_D"
FIG_TRIANGLE = "FIG_TRIANGLE"
OR_UP = "ROTATED_0_DEG"
OR_RIGHT = "ROTATED_90_DEG"
OR_DOWN = "ROTATED_180_DEG"
OR_LEFT = "ROTATED_270_DEG"
FULL = "MASK_F"
CENTRAL = "MASK_C"
PERIPHERAL = "MASK_P"
FIX_TOP = (Params.screen_x // 2, Params.screen_y // 4)
FIX_CENTRAL = Params.screen_c
FIX_BOTTOM = (Params.screen_x // 2, 3 * Params.screen_y // 4)
SEARCH_RESPONSE_KEYS = "FGSearch_response"
WHITE = (255, 255, 255, 255)
NEUTRAL_COLOR = Params.default_fill_color
"""
EXPERIMENT FACTORS & 'METAFACTOS' (ie. between-block variations as against between-trial)
"""
Params.exp_meta_factors = {"stim_size": [4, 4, 4], # degrees of visual angle
						   "fixation": [FIX_TOP, FIX_CENTRAL, FIX_BOTTOM]}
						   
Params.exp_factors = [("mask", [FULL, CENTRAL, PERIPHERAL]),
					  ("figure", [FIG_TRIANGLE, FIG_D, FIG_D, FIG_TRIANGLE ]),
					  ("background", [BG_CIRCLE, BG_SQUARE]),
					  ("orientation", [OR_UP, OR_LEFT, OR_RIGHT, OR_DOWN]),
					]

"""
This code defines a  class that 'extends' the basic KLExperiment class.
The experiment itself is actually *run* at the end of this document, after it's been defined.

"""

class FGSearch(klibs.Experiment):
	stim_size = None
	mask_diameter = 10  # degress of visual angle
	search_time = 3  # seconds
	fixation = None  # chosen randomly each trial
	bg_element_size = 0.2  # degrees of visual angle
	bg_element_padding = 0.2  # degrees of visual angle

	neutral_color = Params.default_fill_color
	mask_abs_alpha_region = 0.5
	pseudo_mask = None

	#  trial vars
	timed_out = False

	#  debug vars
	gaze_debug_dot = None

	def __init__(self, *args, **kwargs):
		klibs.Experiment.__init__(self, *args, **kwargs)

	def setup(self):
		pr("@PExperiment.setup() reached", 1)
		Params.key_maps[SEARCH_RESPONSE_KEYS] = klibs.KeyMap(SEARCH_RESPONSE_KEYS, ["z","/"], ["z", "/"], [sdl2.SDLK_z, sdl2.SDLK_SLASH])
		Params.exp_meta_factors['fixation'] = [Params.screen_c,
											   (Params.screen_c[0], Params.screen_y / 4),
											   (Params.screen_c[0], 3 * Params.screen_y / 4)]
		dc_box_size = 50
		# left drift correct box
		dc_top_tl = (0.5 * Params.screen_x - 0.5 * dc_box_size, Params.screen_y / 4 - 0.5 * dc_box_size )
		dc_top_br = (0.5 * Params.screen_x + 0.5 * dc_box_size, Params.screen_y / 4 + 0.5 * dc_box_size)
		self.eyelink.add_gaze_boundary('dc_top_box', [dc_top_tl, dc_top_br])
		# right drift correct box
		dc_bottom_tl = ( 0.5 * Params.screen_y - 0.5 * dc_box_size, 3 * Params.screen_y / 4 - 0.5 * dc_box_size )
		dc_bottom_br = ( 0.5 * Params.screen_y - 0.5 * dc_box_size, 3 * Params.screen_y / 4 + 0.5 * dc_box_size )
		self.eyelink.add_gaze_boundary('dc_bottom_box', [dc_bottom_tl, dc_bottom_br])
		# middle drift correct box
		dc_middle_tl = (Params.screen_x / 2 - 0.5 * dc_box_size, 0.5 * Params.screen_y - 0.5 * dc_box_size)
		dc_middle_br = (Params.screen_x / 2 + 0.5 * dc_box_size, 0.5 * Params.screen_y + 0.5 * dc_box_size)
		self.eyelink.add_gaze_boundary('dc_middle_box', [dc_middle_tl, dc_middle_br])
		gaze_debug_dot = Image.new("RGBA", (5, 5), (0, 0, 0, 0))
		ImageDraw.Draw(gaze_debug_dot , "RGBA").ellipse((0, 0, 5, 5), (255, 0, 0, 255), (0, 0, 0, 255))
		self.gaze_debug_dot = from_aggdraw_context(gaze_debug_dot)
		self.eyelink.setup()
		pr("@BExperiment.setup() exiting", 1)

	def block(self, block_num):
		pr("@PExperiment.block() reached", 1)
		self.stim_size = Params.exp_meta_factors['stim_size'][Params.block_number % 3]
		stim_size_px = deg_to_px(self.stim_size * 0.9)
		padded_stim_size_px = int(1.25 * deg_to_px(self.stim_size))
		tl_x =  Params.screen_x // 2 - stim_size_px // 2
		tl_y =  Params.screen_y // 2 - stim_size_px // 2
		br_x =  Params.screen_x // 2 + stim_size_px // 2
		br_y =  Params.screen_y // 2 + stim_size_px // 2
		self.eyelink.add_gaze_boundary('stim_space',[(tl_x, tl_y), (br_x, br_y)] )
		pseudo_mask = Image.new("RGBA", (padded_stim_size_px, padded_stim_size_px), NEUTRAL_COLOR)
		self.pseudo_mask = from_aggdraw_context(pseudo_mask)
		pr("@BExperiment.block() exiting", 1)

	def trial_prep(self, *args, **kwargs):
		pr("@PExperiment.trial_prep() reached", 1)
		self.database.init_entry('trials')
		self.clear()
		pr("@BExperiment.trial_prep() exiting", 1)

	def trial(self, trial_factors, trial_num):
		"""
		trial_factors: 1 = mask, 2 = figure, 3 = background, 4 = orientation]
		"""
		pr("@PExperiment.trial() reached", 1)
		pr("@T\ttrial_factors: {0}".format(trial_factors[1]), 0)

		texture = self.texture(trial_factors[3])
		if trial_factors[2] != FIG_SQUARE:  # texture already is square, nothing to mask
			texture_mask = self.figure(trial_factors[2], trial_factors[4])
			pr("@T TextureMask: {0},  texture: {1}".format(texture_mask, texture), 2)
			texture.mask(texture_mask, (0, 0))
		"""
		  The next 4 lines would typically belong in the trial_prep() function, but due to lag in rendering the mask &
		  texture surfaces, are executed here instead to ensure that the trial begins without delay after drift
		  correction.
		"""
		self.message("Press any key to advance...", color=WHITE, location="center", font_size=48, flip=False)
		self.listen()
		self.fixation = tuple(random.choice(Params.exp_meta_factors['fixation']))
		self.drift_correct(self.fixation)

		self.eyelink.start(trial_num)
		mask = self.mask(self.mask_diameter, trial_factors[1] == PERIPHERAL)
		resp = self.listen(self.search_time, SEARCH_RESPONSE_KEYS, wait_callback=self.screen_refresh, texture=texture,
						   mask=mask, mask_type=trial_factors[1])
		if resp[0] == TIMEOUT:
			self.clear()
			self.alert("Too slow!", False, 1)
			self.clear()

		#  create readable data as fixation is currently in (x,y) coordinates
		initial_fixation = None
		if self.fixation == FIX_TOP:
			initial_fixation = "TOP"
		elif self.fixation == FIX_CENTRAL:
			initial_fixation = "CENTRAL"
		else:
			initial_fixation = "BOTTOM"


		return {"practicing": trial_factors[0],
				"response": resp[0],
				"rt": float(resp[1]),
				"mask": trial_factors[1],
				"mask_diam": self.stim_size,
				"figure": trial_factors[2],
				"figure_orientation": trial_factors[4],
				"background": trial_factors[3],
				"trial_num": trial_num,
				"block_num": Params.block_number,
				"initial_fixation": initial_fixation}


	def trial_clean_up(self, *args, **kwargs):
		self.fixation = None

	def clean_up(self):
		pass

	def texture(self, texture_figure):
		pr("@PExperiment.texture(texture_figure) reached", 1)
		pr("\t@Ttexture_figure = {0}".format(texture_figure), 2)
		grid_size = deg_to_px(1.1 * self.stim_size)
		dc = aggdraw.Draw("RGBA", (grid_size, grid_size), (0, 0, 0, 0))
		pen = aggdraw.Pen((255, 255, 255), 1.5, 255)
		grid_cell_size = deg_to_px(self.bg_element_size + self.bg_element_padding)
		grid_cell_count = grid_size // grid_cell_size
		pr("\t@TGridSize: {0}, GridCellSize:{1}, GridCellCount: {2}".format(grid_size, grid_cell_size, grid_cell_count), 2)

	 	# Visual Representation of the Texture Rendering Logic
		# <-------G-------->
		#  _______________   ^
		# |       O       |  |    O = element_offset, ie. 1/2 bg_element_padding
		# |     _____     |  |    E = element (ie. circle, square, triangle, etc.)
		# |    |     |    |  |    G = one grid length
		# | O  |  E  |  O |  G
		# |    |_____|    |  |
		# |               |  |
		# |_______O_______|  |
		#                    v

		element_offset = self.bg_element_padding // 2  # so as to apply padding equally on all sides of bg elements
		element = None
		for col in range(0, grid_cell_count):
			for row in range(0, grid_cell_count):
				top = int(row * grid_cell_size + element_offset)
				left = int(col * grid_cell_size + element_offset)
				bottom = int(top + deg_to_px(self.bg_element_size))
				right = int(left + deg_to_px(self.bg_element_size))
				pr("\t@Ttop: {0}, left: {1}, bottom:{2}, right:{3}".format(top, left, bottom, right), 2)
				if texture_figure == BG_CIRCLE: dc.ellipse([left, top, right, bottom], pen)
				if texture_figure == BG_SQUARE: dc.rectangle([left, top, right, bottom], pen)
		pr("@BExperiment.texture() exiting", 1)
		return from_aggdraw_context(dc)

	def figure(self, figure_shape, orientation):
		size = deg_to_px(self.stim_size)
		dc_size = deg_to_px(1.1 * self.stim_size)
		pad = 0.1 * size
		dc = Image.new("RGBA",  (dc_size, dc_size), (0, 0, 0, 0))

		if figure_shape == FIG_CIRCLE:
			ImageDraw.Draw(dc, 'RGBA', ).ellipse((pad, pad, size, size), (WHITE))
		if figure_shape == FIG_TRIANGLE:
			ImageDraw.Draw(dc, "RGBA").polygon((size // 2, 0, size, size, 0, size, size // 2, 0), (WHITE))
		if figure_shape == FIG_D:
			ImageDraw.Draw(dc, "RGBA").ellipse((pad, pad, size, size), (WHITE))
			ImageDraw.Draw(dc, "RGBA").rectangle((pad, pad, size // 2, size), (WHITE))
		if orientation in [OR_RIGHT, OR_LEFT, OR_DOWN] and figure_shape in [FIG_D, FIG_TRIANGLE]:
			pr("\t@TExperiment.figure() -> orientation_reached: TRUE, orientation:{0}, figure_shape:{1}".format(orientation, figure_shape), 1)
			if orientation == OR_RIGHT:
				dc = dc.rotate(90)
			elif orientation == OR_DOWN:
				dc = dc.rotate(180)
			else:
				dc = dc.rotate(270)
		cookie_cutter = from_aggdraw_context(dc)
		dough = aggdraw.Draw('RGBA', (dc_size, dc_size), (0, 0, 0, 0))
		dough.rectangle((0, 0, dc_size, dc_size), aggdraw.Brush((255,255,255), 255))
		dough = from_aggdraw_context(dough)
		dough.mask(cookie_cutter, (0, 0))
		return dough

	def mask(self, diameter, peripheral):
		pr("@PExperiment.mask() reached", 1)
		pr("\t@TExperiment.mask(diameter={0}, peripheral={1})".format(diameter, peripheral, 1))
		diameter = deg_to_px(diameter)
		bg = None
		mask = None

		if peripheral:
			blur_size = int(diameter * 0.1)
			bg_attributes = [int(deg_to_px(self.stim_size * 2)), NEUTRAL_COLOR]
		else:
			blur_size = int(diameter * 0.05)
			bg_attributes = [int(diameter), NEUTRAL_COLOR]

		bg = Image.new("RGBA", (bg_attributes[0], bg_attributes[0]), bg_attributes[1])

		tl = int(0.333 * diameter)
		br = diameter - tl

		if peripheral:
			alpha_mask = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
			alpha_mask_canvas = ImageDraw.Draw(alpha_mask, "RGBA").ellipse((tl, tl, br, br), (WHITE), (255, 0, 0, 255))
			alpha_mask = alpha_mask.filter(ImageFilter.GaussianBlur(blur_size))
			alpha_mask = from_aggdraw_context(alpha_mask)
			mask = from_aggdraw_context(bg)
			tl = mask.width // 2 -  alpha_mask.width // 2
			br = tl
			pr("\t@T p_mask: {0}, a_mask: {3},  tl: {1}, br: {2}".format(mask, tl, br, alpha_mask), 2)
			mask.mask(alpha_mask, (tl,br), True)
		else:
			alpha_mask = Image.new("RGBA", (bg_attributes[0], bg_attributes[0]), (WHITE))
			alpha_mask_canvas = ImageDraw.Draw(alpha_mask, "RGBA").ellipse((tl, tl, br, br), (0, 0, 0, 255), (255, 0, 0, 255))
			alpha_mask = alpha_mask.filter(ImageFilter.GaussianBlur(blur_size))
			alpha_mask = from_aggdraw_context(alpha_mask)
			# bg_canvas = ImageDraw.Draw(bg, "RGBA").ellipse((tl, tl, br, br), NEUTRAL_COLOR, (0, 0, 0, 0))
			# bg = bg.filter(ImageFilter.GaussianBlur(blur_size))
			mask = from_aggdraw_context(bg)
			mask.mask(alpha_mask, (0,0), True)
		pr("@BExperiment.mask() exiting")
		return mask

	def screen_refresh(self, texture, mask, mask_type):
		pr("@P refresh_screen(texture, mask, mask_type) : {0}, {1}, {2}".format(texture, mask, mask_type), 2)
		try:
			position = self.eyelink.gaze()
		except:
			position = mouse_pos()
		self.fill()
		self.blit(texture, 5, 'center')
		if mask_type != FULL:
			if mask_type == PERIPHERAL and self.eyelink.within_boundary('stim_space', position) is False:
				mask = self.pseudo_mask
				position = 'center'
			self.blit(mask, 5, position)
			if Params.debug_level > 0:
				self.blit(self.gaze_debug_dot, 5, mouse_pos())
		self.flip()

app = FGSearch("FGSearch").run()
