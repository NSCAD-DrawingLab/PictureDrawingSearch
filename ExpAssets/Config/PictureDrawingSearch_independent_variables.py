__author__ = 'Austin Hurst'
from klibs.KLIndependentVariable import IndependentVariableSet, IndependentVariable


# Initialize object containing project's independant variables

FigureGroundSearch_ind_vars = IndependentVariableSet()


# Define project variables and variable types

FigureGroundSearch_ind_vars.add_variable("mask_type",    str, ["central", "peripheral", "none"])
FigureGroundSearch_ind_vars.add_variable("mask_size",    int, [8, 12, 16])