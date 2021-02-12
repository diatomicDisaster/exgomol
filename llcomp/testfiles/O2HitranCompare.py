from ExGoMol.linelist import Linelist, MergedLinelist, exomol_to_linelist, \
    hitran_to_linelist, file_to_linelist
from ExGoMol.data import y_as_fx, compare_dataframes, print_linelist
import numpy as np
import matplotlib.pyplot as plt

exomolList = exomol_to_linelist(
    states_file="O2XabQM.states",
    trans_file="O2XabQM.trans"
)

hitranList = hitran_to_linelist(
    "O2HitranLines.csv"
)

hitranList.filter_data(["transition_moment_key", "==", "q"])
compareList = MergedLinelist(compare_dataframes(exomolList.dataframe, hitranList.dataframe))
print_linelist(compareList, cols=[
    "einstein_coefficient_L", "einstein_coefficient_R",
    "transition_wavenumber_L", "transition_wavenumber_R",
    "vibrational_f", "vibrational_i",
    "angmom_total_f", "angmom_total_i",
    "electronic_state_f", "electronic_state_i"
])

ein_diff = compareList.diff("einstein_coefficient")
print(np.average(ein_diff))
plt.ion()
plt.plot(compareList.dataframe["einstein_coefficient_L"], ein_diff/compareList.dataframe["einstein_coefficient_L"])
plt.show()

while input("Stop? ") not in ["Y", "y"]:
    continue