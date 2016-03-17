# KlibsTesting Param overrides
#
# Any param that is commented out by default is either deprecated or else not yet implemented--don't uncomment or use
#
#########################################
# Available Hardware
#########################################
eye_tracker_available = True
eye_tracking = True
labjack_available = True
labjacking = False
#
#########################################
# Environment Aesthetic Defaults
#########################################
default_fill_color = (45, 45, 45, 255)
default_color = (255, 255, 255, 255)
default_response_color = default_color
default_input_color = default_color
default_font_size = 28
default_font_name = 'Frutiger'
default_timeout_message = "Too slow!"
#
#########################################
# EyeLink Sensitivities
#########################################
saccadic_velocity_threshold = 20
saccadic_acceleration_threshold = 5000
saccadic_motion_threshold = 0.15
#
fixation_size = 1,  # deg of visual angle
box_size = 1,  # deg of visual angle
cue_size = 1,  # deg of visual angle
cue_back_size = 1,  # deg of visual angle
#
#########################################
# Experiment Structure
#########################################
collect_demographics = True
practicing = False
trials_per_block = 24
trials_per_practice_block = 0
blocks_per_experiment = 6
practice_blocks_per_experiment = 0
trials_per_participant = 0
#
#########################################
# Development Mode Settings
#########################################
dm_suppress_debug_pane = False
dm_auto_threshold = True

# PROJECT-SPECIFIC VARS
fixation_top = [None, None]
fixation_central = [None, None]
fixation_bottom = [None, None]
exp_meta_factors = {"fixation": [fixation_top, fixation_central, fixation_bottom]}