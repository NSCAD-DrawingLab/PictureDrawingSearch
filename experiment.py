__author__ = "EXPERIMENTER_NAME"

import klibs
from klibs import Params
from klibs.KLNumpySurface import *
import random
Params.screen_x = 2560
Params.screen_y = 1440
# Params.default_fill_color = (125, 125, 125, 255)

Params.collect_demographics = True
Params.practicing = True
Params.eye_tracking = True
Params.eye_tracker_available = False
Params.instructions = False

Params.blocks_per_experiment = 1
Params.trials_per_block = 96
Params.practice_blocks = None
Params.trials_per_practice_block = None
Params.exp_meta_factors = { "stim_size": [10, 8, 4], # degrees of visual angle
							"fixation": []}
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
Params.exp_factors = [("mask", [FULL, CENTRAL, PERIPHERAL]),
					  ("figure", [FIG_SQUARE, FIG_CIRCLE, FIG_D, FIG_TRIANGLE ]),
					  ("background", [BG_CIRCLE, BG_SQUARE]),
					  ("orientation", [OR_UP, OR_DOWN, OR_LEFT, OR_RIGHT]),
					]


class RGBCLI:
	col = {"@P": '\033[95m', # purple
		   "@B": '\033[94m', # blue
		   "@R": '\033[91m', # red
		   "@T": '\033[1m',  # teal
		   "@E": '\033[0m'   # return to normal
	}

	def pr(self, str):
		for col in self.col:
			str = str.replace(col, self.col[col])
		print "{0}{1}".format(str, self.col["@E"])


def pr(str):
	rgb = RGBCLI()
	rgb.pr(str)


class FGSearch(klibs.Experiment):
	stim_size = None
	bg_element_size = 0.2  # degrees of visual angle
	bg_element_padding = 0.2  # degrees of visual angle

	def __init__(self, *args, **kwargs):
		klibs.Experiment.__init__(self, *args, **kwargs)


	def setup(self):
		pr("@PExperiment.setup() reached")
		Params.key_maps['FGSearch_response'] = klibs.KeyMap('FGSearch_response', [], [], [])
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
		pr("@BExperiment.setup() exiting")


	def block(self, block_num):
		pr("@PExperiment.block() reached")
		# dv = degrees of vis. angle,
		self.stim_size = int(str(Params.exp_meta_factors['stim_size'][Params.block_number % 3]).replace("vd", " "))
		pr("@BExperiment.block() exiting")

	def trial_prep(self, *args, **kwargs):
		pr("@PExperiment.trial_prep() reached")
		self.database.init_entry('trials')
		self.message("Press any key to advance...", color=(255, 255, 255, 255), location="center", font_size=48,
					 flip=False)
		self.listen()
		self.drift_correct(tuple(Params.exp_meta_factors['fixation'][Params.trial_number % 3]))
		pr("@BExperiment.trial_prep() exiting")

	def trial(self, trial_factors, trial_num):
		"""
		trial_factors: 0 = mask, 1 = figure, 2 = background, 3 = orientation, 4 = fixation]
		"""
		pr("@PExperiment.trial() reached")
		pr("@T\ttrial_factors: {0}".format(trial_factors))

		self.eyelink.start(trial_num)
		bg = self.texture(trial_factors[2])
		self.fill()
		self.blit(bg, 5, 'center')
		# self.blit(mask, 5, 'center')
		# self.flip()

		# upd = {"bg": bg, "mask": mask}
		try:
			resp = self.listen(3)
		except:
			self.timed_out = True
		stim_parts = trial_factors[2].split("_") # this is the name of the bg  ie. "circle_of_squares"

		if self.timed_out:
			data = {"practicing": -1,
					"response": -1,
					"rt": float(-1),
					"metacondition": ",".join(self.METACOND),
					"mask": trial_factors[3],
					"mask_diam": self.stim_size,
					"form": bg[0],
					"material": bg[1],
					"trial_num": trial_num,
					"block_num": Params.block_number,
					"initial_fixation": 'not_tracking'}
		else:
			data = {"practicing": trial_factors[0],
					"response": resp[0],
					"rt": float(resp[1]),
					"metacondition": ",".join(self.METACOND),
					"mask": trial_factors[3],
					"mask_diam": self.stim_size,
					"form": bg[0],
					"material": bg[1],
					"trial_num": trial_num,
					"block_num": Params.block_number,
					"initial_fixation": trial_factors[1]}
			return data
		return {}

	def refreshScreen(self, bg, mask):
		gaze = self.eyelink.gaze()
		if gaze:
			self.fill()
			self.blit(bg, 5, Params.screen_c)
			self.blit(mask, 5, gaze)
			self.flip()

	def trial_clean_up(self, *args, **kwargs):
		pass

	def clean_up(self):
		pass

	def texture(self, type):
		dc_side_length = deg_to_px(self.stim_size)
		dc = aggdraw.Draw("RGBA", [dc_side_length, dc_side_length], (0, 0, 0, 0))
		pen = aggdraw.Pen((255, 255, 255), 255, 1)
		grid_size = dc_side_length // deg_to_px(self.bg_element_size + self.bg_element_padding)


	 	# Visual Representation of the Texture Rendering Logic
		# <-------G--------->
		#  _______________   ^
		# |       O       |  |    O = element_offset, ie. 1/2 bg_elemen_padding
		# |     _____     |  |    E = element (ie. circle, square, triangle, etc.)
		# |    |     |    |  |    G = one grid length
		# | O  |  E  |  O |  G
		# |    |_____|    |  |
		# |               |  |
		# |_______O_______|  |
		#                    v

		element_offset = self.bg_element_padding // 2  # so as to apply padding equally on all sides of bg elements
		element = None
		for col in range(0, grid_size):
			for row in range(0, grid_size):
				top = row * grid_size + element_offset
				left = col * grid_size + element_offset
				bottom = top + deg_to_px(self.bg_element_size)
				right = left + deg_to_px(self.bg_element_size)
				if type == BG_CIRCLE: dc.ellipse([left, top, right, bottom], pen)
				if type == BG_SQUARE: dc.rectangle([left, top, right, bottom], pen)
		return from_aggdraw_context(dc)



app = FGSearch("FGSearch").run()




# import os
# os.remove("/Users/jono/Documents/Python/Jon/parafovealactivity/lib/klibs.py")
# os.remove("/Users/jono/Documents/Python/Jon/parafovealactivity/lib/klibs.pyc")
# os.symlink("/Users/jono/Documents/Python/Jon/klib/klibs.py",
# "/Users/jono/Documents/Python/Jon/parafovealactivity/lib/klibs.py")


#
# class PFA(kl.App):
#
# 	def block(self, blockNum):
# 		pass
#
# 	def setup(self):
# 		if self.DEMOGRAPH:
# 			if self.participantId <= 6:
# 				self.METACOND = self.METAFACTORS[self.participantId]
# 			else:
# 				multiples = self.participantId//6
# 				mc = self.participantId - (6*multiples)
# 				self.METACOND = self.METAFACTORS[mc]
# 		else:
# 			self.METACOND = self.METAFACTORS[0]
# 		self.watermark = pygame.image.load("assets/img/keys_watermark.png")
# 		self.driftTarget = pygame.image.load("assets/img/drift.png")
# 		self.asurf = pygame.Surface(self.screenxy, flags=pygame.SRCALPHA)
# 		self.keyMapper('shapes', self.KEYNAMES, self.KEYCODES, self.KEYVALS)
# 		if not self.noTracker:
# 			self.EL.trackerInit()
# 			self.EL.setup()
# 			self.PRACTICING = False
#
# 	def trialPrep(self,t, tnum):
# 		self.sf(self.LM_GREY)
# 		self.sf(self.WHITE, self.asurf)
# 		self.badTrial = False
# 		if self.noTracker:
# 			m = "Press any key to advance..."
# 			self.message(m,location="center", fontSize=48, fullscreen=True, flip=True)
# 			self.listen("*", "*")
# 			time.sleep(0.2)
#
# 	def startGaze(self, loc):
# 		if loc == "center":
# 			pos = self.screenc
# 		elif loc == "top-middle":
# 			pos = (self.screenx//4, self.screeny//2)
# 		elif loc == "bottom-middle":
# 			pos = ((self.screenx*3)//4, self.screeny//2)
# 		return pos
#
# 	def trial(self, t, trialNum=None):
#
#
#
# 	def trialCleanUp(self):
# 		pass
#
# 	def checkBounds(self, gazeStart):
# 		self.bliterate(self.watermark, 5, self.screenc)
# 		self.bliterate(self.driftTarget, 5, gazeStart)
# 		self.flip()
# 		dtx = (self.driftTarget.get_width() // 2) + 50
# 		dty = (self.driftTarget.get_height() // 2) + 50
# 		left = gazeStart[0] - dtx
# 		right = gazeStart[0] + dtx
# 		top = gazeStart[1] - dty
# 		bottom = gazeStart[1] + dtx
#
# 		inBounds = False
# 		while not inBounds:
# 			if self.noTracker:
# 				pygame.event.pump() # if using mouse
# 			gaze = self.EL.gaze(None)
# 			if gaze:
# 				inBounds = self.boundedBy(gaze, left, right, top, bottom)
#
#
#
# 	def codeGen(self):
# 		pass
#
# 	def cleanUp(self):
# 		pass
#
# 	def parseStim(self, stimName):
# 		parts = stimName.split("_")
# 		return [parts[0], parts[1]]

# global app
# el = MyLink()
# app = PFA(el, paramFile="Parameters", paramsDir="lib")
# app.expFactors = app.FACTORS
# # app.db.rebuild()
# app.noTracker = False
# app.expSchema(1, 144, 0, 0)
# if app.DEMOGRAPH:
# 	app.getDemographics()
# if app.INSTRUCT:
# 	app.instructions(app.INSTRUCTIONS)
# if app.EXECUTE:
# 	app.run()
# while True: # exit message hangs in overwatch until command+q is pressed
# 	app.sf()
# 	app.message(app.COMPLETION_MESSAGE, location="center", wrap = True, delimiter="\r")
# 	app.listen('*','*')

