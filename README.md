# 2026-03-26_j.enbuild.2026.117382
Codes used in doi: j.enbuild.2026.117382

Codes for the particular research article.
Note: as the .ipynb file reads the input data manually, user is responsible for inserting correct source data files for the code to run properly.
This requires edits to the .ipynb files

econ_run_clean.ipynb
- Defines the studied scenarios
- Selects the input data
- Creates (or downloads) the modelled buildings (consumption data needs to be added)
- Runs the economic analysis

flats.py
- Defines classes Flat, Building, and PV_system

funcs.py
- Functions needed in .ipynb files

plotting_multi_story.ipynb
- Creates figures for manuscript
- Also additional figures for manual inspection of the data sets

read_pvsyst.ipynb
- Reads the PV profiles generated with PVsyst and exports them as Excel files
- Modify to match your syntax
