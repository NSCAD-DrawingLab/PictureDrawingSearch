__author__ = "EXPERIMENTER_NAME"

import klibs
from PIL import Image,ImageDraw, ImageFilter
from klibs import Params
from klibs.KLNumpySurface import *
from klibs.KLUtilities import *
import random
import sdl2
import copy


Params.default_fill_color = (100, 100, 100, 255) # TODO: rotate through seasons

Params.debug_level = 3
Params.collect_demographics = False
Params.practicing = True
Params.eye_tracking = True
Params.eye_tracker_available = False

Params.blocks_per_experiment = 4
Params.trials_per_block = 24
Params.practice_blocks_per_experiment = 3
Params.trials_per_practice_block = 3

"""
DEFINITIIONS & SHORTHAND THAT SIMPLY CLEANS UP THE READABILITY OF THE CODE BELOW
"""
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
FIX_TOP = None
FIX_CENTRAL =None
FIX_BOTTOM = None
SEARCH_RESPONSE_KEYS = "FGSearch_response"
BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)
RED = (255, 0, 0, 80)
GREEN = (0, 255, 0, 80)
BLUE = (0, 0, 255, 80)
DARK_GREY= (45, 45, 45, 255)
NEUTRAL_COLOR = Params.default_fill_color
TRANSPARENT = (0, 0, 0, 0)
RGBA = "RGBA"

"""
EXPERIMENT FACTORS & 'METAFACTORS' (ie. between-block variations as against between-trial)
"""

Params.exp_meta_factors = {"fixation": [FIX_TOP, FIX_CENTRAL, FIX_BOTTOM]}

"""
This code defines a  class that 'extends' the basic KLExperiment class.
The experiment itself is actually *run* at the end of this document, after it's been defined.
"""

class FGSearch(klibs.Experiment):
	stim_size = 4  # degrees of visual angle
	stim_pad = 0.4 # degrees of visual angle
	mask_blur_width = 4  # pixels
	maximum_mask_size = 0  # automatically set at run time, do not change
	search_time = 30  # seconds
	fixation = None  # chosen randomly each trial
	bg_element_size = 0.4  # degrees of visual angle
	bg_element_pad = 0.3  # degrees of visual angle
	orientations = [0, 90, 180, 270]

	neutral_color = Params.default_fill_color
	pseudo_mask = None

	#  trial vars
	timed_out = False

	textures = {}
	figures = {}
	stimuli = {}
	masks = {}

	#  debug vars
	gaze_debug_dot = None

	def __init__(self, *args, **kwargs):
		# klibs.Experiment.__init__(self, *args, **kwargs)

		super(FGSearch, self).__init__(*args, **kwargs)

		FIX_TOP = (Params.screen_x // 2, Params.screen_y // 4)
		FIX_CENTRAL = Params.screen_c
		FIX_BOTTOM = (Params.screen_x // 2, 3 * Params.screen_y // 4)


	def setup(self):
		pr("@PExperiment.setup() reached", 2)
		self.stim_pad = deg_to_px(self.stim_pad)
		# self.__generate_masks()
		# self.__generate_stimuli()
		# self.__generate_fixations()

		Params.key_maps[SEARCH_RESPONSE_KEYS] = klibs.KeyMap(SEARCH_RESPONSE_KEYS, ["z","/"], ["circle", "square"], [sdl2.SDLK_z, sdl2.SDLK_SLASH])

		# debugging dot for gaze coordinates
		gaze_debug_dot = Image.new(RGBA, (5, 5), TRANSPARENT)
		ImageDraw.Draw(gaze_debug_dot , RGBA).ellipse((0, 0, 5, 5), RED, BLACK)
		self.gaze_debug_dot = from_aggdraw_context(gaze_debug_dot)

		padded_stim_size_px = deg_to_px(self.stim_size) + self.stim_pad + 1
		pseudo_mask = Image.new(RGBA, (padded_stim_size_px, padded_stim_size_px), NEUTRAL_COLOR)
		self.pseudo_mask = from_aggdraw_context(pseudo_mask)
		self.collect_demographics()
		self.eyelink.setup()
		pr("@BExperiment.setup() exiting", 2)

	def __generate_masks(self):
		max_mask_px = 0
		smaller_than_screen = True
		while smaller_than_screen:
			self.maximum_mask_size += 1
			new_max_mask_px = deg_to_px(self.maximum_mask_size) + deg_to_px(self.stim_size) // 2 + self.stim_pad // 2
			if new_max_mask_px > Params.screen_y:
				smaller_than_screen = False
				self.maximum_mask_size -= 1
			else:
				max_mask_px = new_max_mask_px
		for size in self.trial_factory.exp_parameters[1][1]:
			if size > self.maximum_mask_size:
				e_str = "The maximum mask size this monitor can support is {0} degrees.".format(self.maximum_mask_size)
				raise ValueError(e_str)
		pr("\t@R self.maximum_mask_size: {0} or: {1}".format(self.maximum_mask_size,
															 deg_to_px(self.maximum_mask_size) + deg_to_px(
																 self.stim_size) // 2 + self.stim_pad // 2))
		self.clear()
		self.message("Rendering masks...", font_size=48, location=Params.screen_c, registration=5, flip=True)
		self.masks = {}
		for size in self.trial_factory.exp_parameters[1][1]:
			pump()
			self.masks["{0}_{1}".format(CENTRAL, size)] = self.mask(size, CENTRAL)
			self.masks["{0}_{1}".format(PERIPHERAL, size)] = self.mask(size, PERIPHERAL)

	def __generate_stimuli(self):
		self.clear()
		self.message("Generating stimuli...", font_size=48, location=Params.screen_c, registration=5, flip=True)
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
			self.stimuli["{0}_{1}".format(fig_text, texture_text)] = stim

	def __generate_fixations(self):
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

	def block(self, block_num):
		pr("@PExperiment.block() reached", 2)
		pr("@BExperiment.block() exiting", 2)

	def trial_prep(self, *args, **kwargs):
		pr("@PExperiment.trial_prep() reached", 2)
		self.clear()
		pr("@BExperiment.trial_prep() exiting", 2)

	def trial(self, trial_num, trial_factors):
		"""
		trial_factors: 1 = mask_type, 2 = mask_size, 3 = target_level, 4 = target_shape]
		"""
		pr("@PExperiment.trial() reached, @Ttrial_factors: {0}".format(trial_factors), 0)

		# choose randomly varying parts of trial
		orientation = random.choice(self.orientations)
		self.fixation = tuple(random.choice(Params.exp_meta_factors['fixation']))

		# infer which mask & stim to use and retrieve them
		figure = trial_factors[4] if trial_factors[3] == LOCAL else False
		stim_label = None
		if figure:
			stim_label = "{0}_D_{1}".format(trial_factors[4], orientation)
		else:
			stim_label = "D_{0}_{1}".format(orientation, trial_factors[4])
		stim = self.stimuli[stim_label]
		mask_label = "{0}_{1}".format(trial_factors[1], trial_factors[2])
		try:
			mask = self.masks[mask_label]
		except KeyError:
			mask = None  # for the no mask condition, easier than creating empty keys in self.masks

		# start the trial
		self.message("Press any key to advance...", color=WHITE, location="center", font_size=48, flip=False)
		self.listen()
		self.drift_correct(self.fixation)
		self.eyelink.start(trial_num)
		resp = self.listen(self.search_time, SEARCH_RESPONSE_KEYS, wait_callback=self.screen_refresh, stim=stim,
						   mask=mask, mask_type=trial_factors[1], gaze_boundary=mask_label)

		# handle timeouts
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
				"mask_type": trial_factors[1],
				"mask_size": trial_factors[2],
				"local": trial_factors[4] if trial_factors[3] == LOCAL else "D",
				"global": trial_factors[4] if trial_factors[3] == GLOBAL else "D",
				"d_orientation": orientation,
				"trial_num": trial_num,
				"block_num": Params.block_number,
				"initial_fixation": initial_fixation}

	def trial_clean_up(self, *args, **kwargs):
		self.fixation = None

	def clean_up(self):
		pass

	def texture(self, texture_figure, orientation=None):
		pr("@PExperiment.texture(texture_figure) reached", 2)
		pr("\t@Ttexture_figure = {0}, orientation = {1}".format(texture_figure, orientation), 2)
		grid_size = (deg_to_px(self.stim_size) + self.stim_pad) * 2
		stim_offset = self.stim_pad // 2
		dc = Image.new(RGBA, (grid_size, grid_size), TRANSPARENT)
		stroke_width = 2  #px
		grid_cell_size = deg_to_px(self.bg_element_size + self.bg_element_pad)
		grid_cell_count = grid_size // grid_cell_size
		stim_offset += (grid_size % grid_cell_size) // 2  # split grid_size %% cells over pad
		pr("\t@TGridSize: {0}, GridCellSize:{1}, GridCellCount: {2}".format(grid_size // 2, grid_cell_size // 2, grid_cell_count), 1)

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
		element = None
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
				pr("\t@Ttop_out: {0}, left_out: {1}, bottom_out:{2}, right_out:{3}".format(top_out, left_out, bottom_out, right_out), 2)
				if texture_figure == CIRCLE:
					ImageDraw.Draw(dc, RGBA).ellipse((left_out, top_out, right_out, bottom_out), WHITE)
					ImageDraw.Draw(dc, RGBA).ellipse((left_in, top_in, right_in, bottom_in), NEUTRAL_COLOR)
				elif texture_figure == SQUARE:
					ImageDraw.Draw(dc, RGBA).rectangle((left_out, top_out, right_out, bottom_out), WHITE)
					ImageDraw.Draw(dc, RGBA).rectangle((left_in, top_in, right_in, bottom_in), NEUTRAL_COLOR)
				elif texture_figure is False:
					pr("\t@Rtexture_figure was FALSE", 2)
					half_el_width = int(0.5 * deg_to_px(self.bg_element_size))
					rect_right = right_out - half_el_width
					rect_right_in = right_out - half_el_width - stroke_width
					ImageDraw.Draw(dc, RGBA, ).ellipse((left_out, top_out, right_out, bottom_out), WHITE)
					ImageDraw.Draw(dc, RGBA, ).ellipse((left_in, top_in, right_in, bottom_in), NEUTRAL_COLOR)
					ImageDraw.Draw(dc, RGBA, ).rectangle((left_out, top_out, rect_right, bottom_out), WHITE)
					ImageDraw.Draw(dc, RGBA, ).rectangle((left_in, top_in, rect_right, bottom_in), NEUTRAL_COLOR)
		dc = dc.resize((grid_size // 2, grid_size // 2), Image.ANTIALIAS)
		dc = dc.rotate(orientation)
		pr("@BExperiment.texture() exiting", 2)
		return from_aggdraw_context(dc)

	def figure(self, figure_shape, orientation):
		pr("@PExperiment.figure() reached, @Tfigure_shape: {0}, orientation: {1}".format(figure_shape, orientation), 0)
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
		cookie_cutter = from_aggdraw_context(dc.resize((dc_size // 2, dc_size // 2), Image.ANTIALIAS))
		dough = Image.new(RGBA,  (dc_size // 2, dc_size // 2), WHITE)
		ImageDraw.Draw(dough, RGBA).rectangle((0, 0, dc_size // 2, dc_size // 2), WHITE)
		dough = from_aggdraw_context(dough)
		dough.mask(cookie_cutter, (0, 0))
		pr("@PExperiment.mask() exiting", 1)
		return dough

	def mask(self, diameter, mask_type):
		pr("@PExperiment.mask() reached", 2)
		pr("\t@TExperiment.mask(diameter={0}, peripheral={1})".format(diameter, mask_type, 2))
		MASK_COLOR = NEUTRAL_COLOR
		diameter_deg = diameter
		diameter = deg_to_px(diameter)
		stim_size = deg_to_px(self.stim_size)
		pad =  self.stim_pad  # note, just borrowing this padding value, it's use is not related to the stimuli at all

		if mask_type == PERIPHERAL:
			# Create maskable space hack:
			# 	Minimize the size of the peripheral mask by simply painting the screen a neutral color any time
			# 	the peripheral mask would only be revealing a neutral color.
			r = diameter // 2 + stim_size // 2
			scx =  Params.screen_c[0]
			scy =  Params.screen_c[1]
			self.eyelink.add_gaze_boundary("{0}_{1}".format(mask_type, diameter_deg), [(scx - r, scy - r), (scx + r, scy + r)])


			# Create solid background
			bg_size = diameter + pad + 2 * stim_size
			bg = Image.new(RGBA, (bg_size, bg_size), MASK_COLOR)
			pr("\t@Tbg_size (PERIPHERAL): {0}".format(bg_size), 2)

			# Create an alpha mask
			tl = pad // 2 + stim_size
			br = bg_size - tl
			alpha_mask = Image.new(RGBA, (bg_size, bg_size), TRANSPARENT)
			ImageDraw.Draw(alpha_mask, RGBA).ellipse((tl, tl, br, br), WHITE, MASK_COLOR)
			alpha_mask = alpha_mask.filter( ImageFilter.GaussianBlur(self.mask_blur_width) )
			alpha_mask = from_aggdraw_context(alpha_mask)

			# render mask
			mask = from_aggdraw_context(bg)
			mask.mask(alpha_mask, (0, 0), True)

		if mask_type == CENTRAL:
			# Create solid background
			bg_size = diameter + pad
			bg = Image.new(RGBA, (bg_size, bg_size), MASK_COLOR)
			tl = pad // 2
			br = bg_size - tl
			pr("\t@Tbg_size (CENTRAL): {0}".format(bg_size), 2)

			# Create an alpha mask
			alpha_mask = Image.new(RGBA, (bg_size, bg_size), WHITE)
			ImageDraw.Draw(alpha_mask, RGBA).ellipse((tl, tl, br, br), BLACK)
			alpha_mask = alpha_mask.filter(ImageFilter.GaussianBlur(self.mask_blur_width))
			alpha_mask = from_aggdraw_context(alpha_mask)
			pr("\t@T alpha_mask.width: {0}, alpha_mask.height{1}".format(alpha_mask.width, alpha_mask.height), 2)

			# render mask
			mask = from_aggdraw_context(bg)
			mask.mask(alpha_mask, (0,0), True)
		pr("@BExperiment.mask() exiting", 2)
		return mask

	def screen_refresh(self, stim, mask, mask_type, gaze_boundary=False):
		pr("@P refresh_screen(texture, mask, mask_type) : {0}, {1}, {2}".format(stim, mask, mask_type), 2)
		position = self.eyelink.gaze() if Params.eye_tracker_available else mouse_pos()
		self.fill()
		self.blit(stim, 5, 'center')
		if (mask_type == PERIPHERAL and self.eyelink.within_boundary(gaze_boundary, position) is False) or not position:
			self.clear()
		else:
			if mask is not None:
				self.blit(mask, 5, position)
			if Params.debug_level > 0:
					self.blit(self.gaze_debug_dot, 5, mouse_pos())
		self.flip()

# app = FGSearch("FGSearch").run()
app = FGSearch("FGSearch", 27, export=[True, True])
# app = FGSearch("FGSearch", 27).run()
