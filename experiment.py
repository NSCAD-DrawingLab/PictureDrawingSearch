__author__ = "EXPERIMENTER_NAME"

import klibs
from PIL import Image,ImageDraw, ImageFilter
from klibs import Params
from klibs.KLNumpySurface import *
from klibs.KLUtilities import *
import random
import sdl2

Params.screen_x = 1400
Params.screen_y = 900
Params.default_fill_color = (100, 100, 100, 255)

Params.debug_level = 5
Params.collect_demographics = True
Params.practicing = True
Params.eye_tracking = True
Params.eye_tracker_available = False
Params.instructions = False

Params.blocks_per_experiment = 1
Params.trials_per_block = 96
Params.practice_blocks = None
Params.trials_per_practice_block = None

"""

DEFINITIIONS & SHORTHAND THAT SIMPLY CLEANS UP THE READABILITY OF THE CODE BELOW

"""
BG_CIRCLE = 0
BG_SQUARE = 1
FIG_SQUARE = "FIG_S"
FIG_CIRCLE = "FIG_C"
FIG_D = "FIG_D"
FIG_TRIANGLE = "FIG_T"
OR_UP = "ORI_U"
OR_DOWN = "ORI_D"
OR_LEFT = "ORI_D"
OR_RIGHT = "ORI_D"
FULL = "MASK_F"
CENTRAL = "MASK_C"
PERIPHERAL = "MASK_P"
FIX_TOP = (Params.screen_x // 2, Params.screen_y // 4)
FIX_CENTRAL = Params.screen_c
FiX_BOTTOM = (Params.screen_x // 2, 3 * Params.screen_y // 4)
SEARCH_RESPONSE_KEYS = "FGSearch_response"
"""
EXPERIMENT FACTORS & 'METAFACTOS' (ie. between-block variations as against between-trial)
"""
Params.exp_meta_factors = {"stim_size": [10, 8, 4], # degrees of visual angle
						   "fixation": [FIX_TOP, FIX_CENTRAL, FiX_BOTTOM]}
Params.exp_factors = [("mask", [FULL, CENTRAL, PERIPHERAL]),
					  ("figure", [FIG_SQUARE, FIG_CIRCLE, FIG_D, FIG_TRIANGLE ]),
					  ("background", [BG_CIRCLE, BG_SQUARE]),
					  ("orientation", [OR_UP, OR_DOWN, OR_LEFT, OR_RIGHT]),
					]

"""

This code defines a  class that 'extends' the basic KLExperiment class.
The experiment itself is actually *run* at the end of this document, after it's been defined.

"""

class FGSearch(klibs.Experiment):
	stim_size = None
	search_time = 3  # seconds
	fixation = None  # chosen randomly each trial
	bg_element_size = 0.2  # degrees of visual angle
	bg_element_padding = 0.2  # degrees of visual angle

	neutral_color = Params.default_fill_color
	mask_abs_alpha_region = 0.5

	# trial vars
	timed_out = False

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
		pr("@BExperiment.setup() exiting", 1)


	def block(self, block_num):
		pr("@PExperiment.block() reached", 1)
		# dv = degrees of vis. angle,
		self.stim_size = Params.exp_meta_factors['stim_size'][Params.block_number % 3]
		pr("@BExperiment.block() exiting", 1)

	def trial_prep(self, *args, **kwargs):
		pr("@PExperiment.trial_prep() reached", 1)
		self.database.init_entry('trials')
		self.clear()
		self.message("Press any key to advance...", color=(255, 255, 255, 255), location="center", font_size=48,
					 flip=False)
		self.listen()
		self.fixation = tuple(random.choice(Params.exp_meta_factors['fixation']))

		self.drift_correct(self.fixation)
		pr("@BExperiment.trial_prep() exiting", 1)

	def trial(self, trial_factors, trial_num):
		"""
		trial_factors: 1 = mask, 2 = figure, 3 = background, 4 = orientation]
		"""
		pr("@PExperiment.trial() reached", 1)
		pr("@T\ttrial_factors: {0}".format(trial_factors[1]), 1)
		self.eyelink.start(trial_num)
		texture = self.texture(trial_factors[3])
		if trial_factors[2] != FIG_SQUARE:  # texture already is square, nothing to mask
			texture_mask = self.figure(trial_factors[2])
			pr("@T TextureMask: {0},  texture: {1}".format(texture_mask, texture), 2)
			texture.mask(texture_mask, (0, 0))
		start = now()
		mask = self.mask(5, trial_factors[1])
		resp = self.listen(self.search_time, SEARCH_RESPONSE_KEYS, wait_callback=self.screen_refresh,
						   wait_cb_args={"texture":texture, "mask":mask, "mask_type":trial_factors[1]})

		#  create readable data as fixation is currently in (x,y) coordinates
		initial_fixation = None
		if self.fixation == FIX_TOP:
			initial_fixation = "TOP"
		elif self.fixation == FIX_CENTRAL:
			initial_fixation = "CENTRAL"
		else:
			initial_fixation = "BOTTOM"

		if self.timed_out:
			data = {"practicing": -1,
					"response": -1,
					"rt": float(-1),
					"mask": trial_factors[1],
					"mask_diam": self.stim_size,
					"form": trial_factors[2],
					"material": trial_factors[3],
					"trial_num": trial_num,
					"block_num": Params.block_number,
					"initial_fixation": initial_fixation}
		else:
			data = {"practicing": trial_factors[0],
					"response": resp[0],
					"rt": float(resp[1]),
					"mask": trial_factors[1],
					"mask_diam": self.stim_size,
					"form": trial_factors[2],
					"material": trial_factors[3],
					"trial_num": trial_num,
					"block_num": Params.block_number,
					"initial_fixation": initial_fixation}
		return data

	def screen_refresh(self, texture, mask, mask_type):
		pr("@P refresh_screen(texture, mask, mask_type) : {0}, {1}, {2}".format(texture, mask, mask_type), -1)
		try:
			gaze = self.eyelink.gaze()
		except:
			gaze = mouse_pos()
		self.fill()
		self.blit(texture, 5, 'center')
		if mask_type == PERIPHERAL:
			self.blit(mask, 7, (0,0))
		elif mask_type == CENTRAL:
			self.blit(mask, 5, gaze)
		self.flip()

		return False

	def trial_clean_up(self, *args, **kwargs):
		self.fixation = None

	def clean_up(self):
		pass

	def texture(self, texture_figure):
		pr("@P Experiment.texture(texture_figure) reached\n\t@Ttexture_figure = {0}".format(texture_figure), 1)
		grid_size = deg_to_px(1.1 * self.stim_size)
		dc = aggdraw.Draw("RGBA", (grid_size, grid_size), (0, 0, 0, 0))
		pen = aggdraw.Pen((255, 255, 255), 1.5, 255)
		grid_cell_size = deg_to_px(self.bg_element_size + self.bg_element_padding)
		grid_cell_count = grid_size // grid_cell_size
		pr("\t@TGridSize: {0}, GridCellSize:{1}, GridCellCount: {2}".format(grid_size, grid_cell_size, grid_cell_count), 1)

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
				# pr("\t@Ttop: {0}, left: {1}, bottom:{2}, right:{3}".format(top, left, bottom, right))
				if texture_figure == BG_CIRCLE: dc.ellipse([left, top, right, bottom], pen)
				if texture_figure == BG_SQUARE: dc.rectangle([left, top, right, bottom], pen)
		return from_aggdraw_context(dc)

	def figure(self, figure_shape):
		size = deg_to_px(self.stim_size)
		dc_size = deg_to_px(1.1 * self.stim_size)
		pad = 0.1 * size
		dc = aggdraw.Draw('RGBA', (dc_size, dc_size), (0, 0, 0, 0))
		brush = aggdraw.Brush((255, 255, 255), 255)

		if figure_shape == FIG_CIRCLE:
			dc.ellipse((pad, pad, size, size), brush)
		if figure_shape == FIG_TRIANGLE:
			dc.polygon((size // 2, 0, size, size, 0, size, size // 2, 0), brush)
		if figure_shape == FIG_D:
			dc.ellipse((pad, pad, size, size), brush)
			dc.rectangle((pad, pad, size // 2, size), brush)
		cookie_cutter = from_aggdraw_context(dc)
		dough = aggdraw.Draw('RGBA', (dc_size, dc_size), (0, 0, 0, 0))
		dough.rectangle((0, 0, dc_size, dc_size), brush)
		dough = from_aggdraw_context(dough)
		dough.mask(cookie_cutter, (0, 0))
		return dough

	def mask(self, diameter, peripheral=False):
		diameter = deg_to_px(diameter)
		blur_size = int(diameter * 0.333 * 0.333)
		bg = None

		if peripheral:
			bg_x = deg_to_px(Params.screen_x)
			bg_y = deg_to_px(Params.screen_y)
			bg = Image.new("RGBA", (bg_x, bg_y), self.neutral_color)
		else:
			bg_size = deg_to_px(diameter)
			bg = Image.new("RGBA", (bg_size, bg_size), self.neutral_color)

		alpha_mask = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
		tl = int(0.333 * diameter) if peripheral else 0
		br = diameter - tl
		alpha_mask_canvas = ImageDraw.Draw(alpha_mask, "RGBA").ellipse((tl, tl, br, br), (255, 255, 255, 255), (0, 0, 0, 255))
		alpha_mask = alpha_mask.filter(ImageFilter.GaussianBlur(blur_size))

		mask = None
		if peripheral:
			alpha_mask = from_aggdraw_context(alpha_mask)
			mask = from_aggdraw_context(bg)

			tl = mask.width // 2 -  alpha_mask.width // 2
			br = tl
			pr("\t@T p_mask: {0}, a_mask: {3},  tl: {1}, br: {2}".format(mask, tl, br, alpha_mask), 2)
			mask.mask(alpha_mask, (tl,br), True)
		else:
			mask = Image.alpha_composite(bg, alpha_mask)

		return mask

	def to_rgb_str(self, color):
		return "rgb({0}, {1}, {2})".format(color[0], color[1], color[2])


app = FGSearch("FGSearch").run()
