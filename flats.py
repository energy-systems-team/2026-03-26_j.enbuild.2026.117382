import numpy as np
import pandas as pd

# This file defines Classes needed for the high-rise PV study
# Lats edit: 5.6.2025 by Sami Jouttijärvi

class Flat:
    # Class represents a single flat. It must have at least a name and consumption profile
    # Consumption as kWh/h

    # Initial, compulsory properties
    def __init__(self, name, consumption):        
        self.name = name
        self.consumption = consumption
    
    # Prints the annual sum of the given attribute
    def print_sum(self, att):
        if hasattr(self, att):
            prof = getattr(self, att)
            print(f"The flat {self.name} has annual {att} of {np.round(np.sum(prof),0)} kWh")
        else:
            print(f"Invalid attribute!")

    # Adds electricity purchase contract to the flat, 'Fixed' or 'Spot'
    def add_purchase_contract(self, contract_type):
        self.purchase_contract = contract_type

    def add_monitoring(self, name_monitoring):
        # Adds a PV monitoring series to the flat
        setattr(self, name_monitoring, pd.Series(index=self.consumption.index, data=np.zeros(len(self.consumption)), name=name_monitoring))


class PV_system:
    # Class represents a PV system. It must have at least a name and production profile
    # Production as kWh/h

    # Initial, compulsory parameters
    def __init__(self, name, production):
        self.name = name
        self.production = production

    # Prints the annual PV production
    def print_production(self):
        print(f"The annual production of PV system {self.name} is {np.round(self.production,0)} kWh.")


class Building:
    # Class represents a building. It must have a name

    def __init__(self, name):
        self.name = name
        self.flats = [] # Flats as empty list
        self.PV_systems = [] # PV systems as empty list

    # Adds one Flat-object to building
    def add_flat(self, flat):
        self.flats.append(flat)

    # Adds one PV_system-object to building
    def add_PV(self, PV_system):
        self.PV_systems.append(PV_system)

    # Removes one Flat-object from the building
    def remove_flat(self, name):
        # name: the Flat.name attribute of the flat to be removed
        for flat in self.flats: # Go through all flats
            if flat.name == name: # Check if name matches
                self.flats.remove(flat) # Does the removal
                print(f"{name} has been removed.") # Print info
                return # Terminate function
        print(f"{name} does not exist.") # Error message if incorrect input

    # Removes one PV_system-object from the building
    def remove_PV(self, name):
        # name: the PV_system.name attribute of the flat to be removed
        for PV_system in self.PV_systems: # Go through all PV-systems
            if PV_system.name == name: # Check if name matches
                self.PV_systems.remove(PV_system) # Does the removal
                print(f"{name} has been removed.") # Print info
                return # Terminate function
        print(f"{name} does not exist.") # Error message if incorrect input

    # Returns the total consumption of the building as time series
    def get_total_consumption(self):
        tot_cons = pd.Series([]) # Initialize
        for flat in self.flats: # Go thorugh all flats
            if tot_cons.empty: # First flat
                tot_cons = flat.consumption.copy()
            else: # Other flats
                tot_cons += flat.consumption.copy()
        return tot_cons
    
    # Returns the total PV production of the building as time series
    def get_total_production(self):
        tot_prod = pd.Series([]) # Initialize
        for PV_system in self.PV_systems: # Go thoruhg all PV systems
            if tot_prod.empty: # First system
                tot_prod = PV_system.production.copy()
            else: # Other systems
                tot_prod += PV_system.production.copy()
        return tot_prod