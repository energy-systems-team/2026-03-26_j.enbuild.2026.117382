import pandas as pd
import numpy as np
import flats
from flats import Building
from flats import Flat
from flats import PV_system
import os

def save_building_info(buildings, out_file='default.xlsx'):
    """
    Save building information to an Excel file.

    Args:
        buildings (list): List of Building objects containing flat information.
        out_file (str): Path to the output Excel file.
    """
    # Initialize total consumption Series
    tot_cons = pd.Series(index=[building.name for building in buildings], name='Total_consumption (kWh)')

    # Loop through all buildings
    for building in buildings:
        tot_cons[building.name] = building.get_total_consumption().sum() # Fill the total consumption column
        # Create a DataFrame for flat listing
        flat_listing = pd.DataFrame(index=[flat.name for flat in building.flats], columns=['Flat_type', 'HashInt', 'Default_contract'])
            
        # Loop through all flats in the building
        for flat in building.flats:
            flat_listing.loc[flat.name, 'Flat_type'] = flat.name.split('_')[0] # Extract flat type from the name
            flat_listing.loc[flat.name, 'HashInt'] = flat.name.split('_')[1] # Extract hashint from the name
            flat_listing.loc[flat.name, 'Default_contract'] = flat.purchase_contract # Get the default contract type of the flat            
            
        # Save the flat listing to the Excel file
        if not os.path.exists(out_file):
            flat_listing.to_excel(out_file, sheet_name=building.name) # If the file does not exist, create it
        else:
            with pd.ExcelWriter(out_file, mode='a') as writer:
                flat_listing.to_excel(writer, sheet_name=building.name)
            
    with pd.ExcelWriter(out_file, mode='a') as writer:
        tot_cons.to_excel(writer, sheet_name='Total_consumption') # Save the total consumption Series to the Excel file

def read_buildings(building_info, flat_info, n_flats, sheets, cons_path_start):
    """
    Read building and flat information from Excel files.

    Args:
        building_info (str): Path to the Excel file containing building information.
        flat_info (str): Path to the Excel file containing flat information.
        n_flats (int): Number of flats in each building.
        sheets (list): List of sheet names to read from the Excel files.
        cons_path_start (str): Path to the directory containing consumption files.

    Returns:
        tuple: A tuple containing a DataFrame with building information and a DataFrame with flat information.
    """
    buildings = []
    for sheet in sheets:
        b_info = pd.read_excel(building_info, sheet_name=sheet, index_col=0)
        building = Building(sheet) # Create a new building object
        cons_file = '' # Initialize

        for flat in b_info.index:
            flat_type = b_info.loc[flat, 'Flat_type'] # Get the flat type from the building info
            hash_int = b_info.loc[flat, 'HashInt'] # Get the hash integer from the building info
            def_contract = b_info.loc[flat, 'Default_contract'] # Get the default contract type from the building info
        # Download the correct consumption file, skip if same file is used
            if cons_file != flat_info.loc[flat_type, 'Cons_file']:
                cons_file = flat_info.loc[flat_type, 'Cons_file']
                flat_cons_all = pd.read_excel(cons_path_start + cons_file, index_col=0)             
            
            flat_cons = flat_cons_all.loc[:,hash_int] # Takes the first free consumption profile
            flat_current = Flat(flat, flat_cons) # Object for the current flat
            flat_current.area = flat_info.loc[flat_type, 'Area'] # Area of the flat
            flat_current.add_purchase_contract(def_contract) # Add the default purchase contract to the flat

            building.add_flat(flat_current)          
            
        building.area = 0 # Initialize area of the building
        for flat in building.flats: # Go through all flats in the building
            building.area += flat.area # Add the area of the flat to the building area
        buildings.append(building) # Add the building to the list of buildings

    return buildings

def create_buildings(n_buildings, flat_info, n_flats, cons_path_start, method='first', \
                     prob_fixed=0, prob_ufn=0, save_info=False, out_file='default.xlsx'):

    """
    Create a list of buildings with their respective flats.

    Args:
        n_buildings (int): Number of buildings to create.
        flat_info (list): List containing information about flats.
        n_flats (int): Number of flats in each building.
        cons_path_start (str): Path to the directory containing consumption files.
        method (str): Method to use for selecting flats ('random', 'specific' or 'first').
        prob_fixed (float): Probability of choosing a fixed price electricity contract.

    Returns:
        list: A list of buildings, each containing a list of flats.
    """
    buildings = []

    for jj in range(n_buildings):
        building = Building('Building_' + str(jj+1)) # Create a new building object
        j=0
        cons_file = '' # Initialize

        for flat in flat_info.index:
        # Download the correct consumption file, skip if same file is used
            if cons_file != flat_info.loc[flat,'Cons_file']:
                cons_file = flat_info.loc[flat,'Cons_file']
                flat_cons_all = pd.read_excel(cons_path_start + cons_file, index_col=0)
                if method == 'random':
                    flat_cons_all = flat_cons_all.sample(frac=1, axis=1)
                i=0

            ii=i # Start from the first unused consumption profile
            # Create Flat-objects to represent individual flats for the particular type
            for k in range(ii, ii+n_flats[j]):
                flat_cons = flat_cons_all.iloc[:,k] # Takes the first free consumption profile
                i+=1 # Mark the consumption profile used        
                flat_name = flat + '_' + str(flat_cons.name) # Name: Flat_type + hash_int (from VSV)
                flat_current = Flat(flat_name, flat_cons) # Object for the current flat
                flat_current.area = flat_info.loc[flat, 'Area'] # Area of the flat

                ran = np.random.rand() # Random number for choosing the electricity coontract
                if ran < prob_fixed: # If the random number is smaller than the probability of fixed price
                    flat_current.add_purchase_contract('Fixed')
                elif ran < (prob_fixed + prob_ufn): # If the random number is smaller than the sum of probabilities of fixed and UFN
                    flat_current.add_purchase_contract('UFN')
                # Otherwise, use spot price contract
                else:
                    flat_current.add_purchase_contract('Spot')

                building.add_flat(flat_current)          
            j+=1 # Next flat type

        building.area = 0 # Initialize area of the building
        for flat in building.flats: # Go through all flats in the building
            building.area += flat.area # Add the area of the flat to the building area
        buildings.append(building) # Add the building to the list of buildings

    if save_info: # If save_info is True, save the building information to a file
        save_building_info(buildings, out_file) # Save the building information to an Excel file
            
    return buildings  # Return the list of buildings with their flats

def share_electricity(building, df_price):
    """
    Share electricity among flats in a building.

    Args:
        building (Building): The building object containing flats.
        df_price (pd.DataFrame): DataFrame containing electricity price information.

    Returns:
        building (Building): The building object with updated electricity data, including the intra-building trade.
    """
    elec_sell = 0
    elec_buy = 0
    n_max_iter = 22

    intra_price = df_price['Intra-building price (€/kWh)']  # Intra-building trade price

    # Go through all hours of year
    for i in range(len(building.get_total_production())):
        prod_available = 0
        prod_requested = 0
        flats_surplus = []
        flats_deficit = []

        join_fixed = (intra_price.iloc[i] <= df_price['Purchase fixed (€/kWh)'].iloc[i]) # Check if the intra-building price is higher than the fixed price
        join_ufn = (intra_price.iloc[i] <= df_price['Purchase ufn (€/kWh)'].iloc[i]) # Check if the intra-building price is higher than the UFN price

        # Go through all flats in the building
        for flat in building.flats:
            flat.diff = flat.production.iloc[i] - flat.consumption.iloc[i]  # Calculate the difference between production and consumption
            if flat.diff > 0:  # If production exceeds consumption, mark production available
                prod_available += flat.diff
                flats_surplus.append(flat)
            elif flat.diff < 0:  # If consumption exceeds production, mark production requested
                # Check if the flat is willing to join the intra-building trade (exclude cases when purchasing from the grid is cheaper)
                if flat.purchase_contract.lower() == 'spot' or (flat.purchase_contract.lower() == 'fixed' and join_fixed) or (flat.purchase_contract.lower() == 'ufn' and join_ufn):
                    prod_requested += abs(flat.diff)
                    flats_deficit.append(flat)

        # Share electricity only if there is both available and requested production
        if (prod_available != 0 and prod_requested != 0):
            n_iter = 0

            # If there is more production available than requested
            if prod_available >= prod_requested:
                for flat in flats_deficit: # All deficit flats are fully supplied
                    elec_buy_flat = (flat.consumption.iloc[i] - flat.production.iloc[i])
                    elec_buy += elec_buy_flat
                    flat.production.iloc[i] += elec_buy_flat
                    flat = fill_flat_monitoring(flat, i, elec_buy_flat, intra_price.iloc[i])   

                while True:
                    n_iter += 1
                    elec_sell_temp = 0
                    for flat in flats_surplus: # Distribute the requested production among surplus flats
                        max_share = prod_requested * flat.area / sum(flat.area for flat in flats_surplus)

                        if max_share > (flat.production.iloc[i] - flat.consumption.iloc[i]): # If the max share is more than the surplus of the flat, the flat sells all its surplus
                            elec_sell_flat = (flat.production.iloc[i] - flat.consumption.iloc[i])
                            flats_surplus.remove(flat)
                        else:
                            elec_sell_flat = max_share # Otherwise, the flat sells its max share

                        flat.production.iloc[i] -= elec_sell_flat
                        elec_sell_temp += elec_sell_flat
                        flat = fill_flat_monitoring(flat, i, -elec_sell_flat, intra_price.iloc[i])

                    prod_requested -= elec_sell_temp
                    elec_sell += elec_sell_temp
                    if flats_surplus == [] or (n_iter > n_max_iter):
                        break
                   

            else: # If there is more production requested than available
                for flat in flats_surplus: # All surplus flats sell all their surplus
                    elec_sell_flat = (flat.production.iloc[i] - flat.consumption.iloc[i])
                    elec_sell += elec_sell_flat  
                    flat.production.iloc[i] -= elec_sell_flat
                    flat = fill_flat_monitoring(flat, i, -elec_sell_flat, intra_price.iloc[i])

                while True:
                    n_iter += 1
                    elec_buy_temp = 0
                    for flat in flats_deficit: # Distribute the available intra-building production among deficit flats
                        max_share = prod_available * flat.area / sum(flat.area for flat in flats_deficit)

                        if max_share > (flat.consumption.iloc[i] - flat.production.iloc[i]): # If the max share is more than the deficit of the flat, the flat buys all its deficit from intra-building trade
                            elec_buy_flat = (flat.consumption.iloc[i] - flat.production.iloc[i])
                            flats_deficit.remove(flat)
                        else:
                            elec_buy_flat = max_share # Otherwise, the flat buys its max share
                        
                        flat.production.iloc[i] += elec_buy_flat
                        elec_buy_temp += elec_buy_flat
                        flat = fill_flat_monitoring(flat, i, elec_buy_flat, intra_price.iloc[i])

                    prod_available -= elec_buy_temp
                    elec_buy += elec_buy_temp
                    if flats_deficit == [] or n_iter > n_max_iter: # Exit if all deficit flats are supplied or max iterations reached
                        break
                    
    building.sell = elec_sell
    building.buy = elec_buy
    return building


def calc_pv_value(production, consumption, purchase_fixed, purchase_ufn, purchase_spot, sell_price, out_column_names, contract_type):
    #Calculate the value of a PV system based on its production and consumption profiles.
    # Initialize
    pv_coll = pd.DataFrame(index=purchase_spot.index, columns=out_column_names)
    pv_coll_val = pv_coll.copy()
    filter = (production.values > consumption.values) # If PV production higher than consumption
    # Calculate the self-consumed and surplus productions
    pv_coll['SC'] = production # Start: self-consumption = production
    pv_coll.loc[filter,'SC'] = consumption[filter] # Self-consumption set to consumption if production > consumption
    pv_coll['sur'] = production - pv_coll['SC'] # Calculates the surplus production

    if contract_type.lower() == 'fixed': # If the first flat has fixed price, use it
        pv_coll_val['SC'] = pv_coll['SC'] * purchase_fixed # Savings (not buying electricity)
        p_consumption = np.sum(consumption * purchase_fixed) # Consumption at fixed price
    elif contract_type.lower() == 'spot': # Otherwise use spot price
        pv_coll_val['SC'] = pv_coll['SC'] * purchase_spot
        p_consumption = np.sum(consumption * purchase_spot)
    elif contract_type.lower() == 'ufn': # If the first flat has UFN contract, use it
        pv_coll_val['SC'] = pv_coll['SC'] * purchase_ufn # Savings (not buying electricity)
        p_consumption = np.sum(consumption * purchase_ufn)
    else:
        raise ValueError("Unknown contract type: {}".format(contract_type))
    
    # Calculate the value of surplus production
    pv_coll_val['sur'] = pv_coll['sur'] * sell_price # Revenue (selling electricity)
    el_bill = p_consumption - np.sum(pv_coll_val['SC']) - np.sum(pv_coll_val['sur']) # Electricity bill without PV
    
    return pv_coll, pv_coll_val, el_bill


def add_flat_level_monitoring(building, names_monitoring):
    """
    Add a flat-level monitoring series to each flat in the building.

    Args:
        building (Building): The building object containing flats.
        name_monitoring (str): The name of the monitoring series to be added.
    """
    for flat in building.flats:
        for name_monitoring in names_monitoring:
            flat.add_monitoring(name_monitoring)
            
    return building

def fill_flat_monitoring(flat, i, amount, price='None'):
    """ Fill the flat's monitoring series with the given amount and price.
    Args:    
        flat (Flat): The flat object to fill monitoring data.
        i (int): The index for the monitoring series.
        amount (float): The amount to fill in the monitoring series.
        price (float, optional): The price associated with the amount. Defaults to 'None'."""
    
    if hasattr(flat, 'pv_monitoring'):
        flat.pv_monitoring.iloc[i] += amount
    if hasattr(flat, 'value_monitoring'):
        flat.value_monitoring.iloc[i] += price*amount # '/100' to convert cents to euros
    return flat

def calculate_traded_electricity(building):
    """
    Calculate the total traded electricity in a building.

    Args:
        building (Building): The building object containing flats.

    Returns:
        df_return (pd.DataFrame): DataFrame with total electricity bought and sold for each flat."""
    df_return = pd.DataFrame(index=[flat.name for flat in building.flats])
    for flat in building.flats:
        if hasattr(flat, 'pv_monitoring'):
            df_return.loc[flat.name, 'PV_bought'] = np.sum(flat.pv_monitoring[flat.pv_monitoring > 0])
            df_return.loc[flat.name, 'PV_sold'] = -np.sum(flat.pv_monitoring[flat.pv_monitoring < 0])
        if hasattr(flat, 'value_monitoring'):
            df_return.loc[flat.name, 'value_bought'] = np.sum(flat.value_monitoring[flat.pv_monitoring > 0])
            df_return.loc[flat.name, 'value_sold'] = -np.sum(flat.value_monitoring[flat.pv_monitoring < 0])
    checksum = df_return.sum(axis=0)
    df_return.loc['Checksum'] = checksum # Add a checksum row to the DataFrame
    return df_return

def revise_profile_name(r_name, f_name, method='Sami'):

    """
    Revise the profile names based on the method used.
    Args:
        r_name (str): The name of the roof profile.
        f_name (str): The name of the facade profile.
        method (str): The method used for naming ('Sami' or 'Magda_shading').
    Returns:
        str: The revised system name based on the method and profile names.
    """
    # NOTE: This function identfies the system profiles based on their names. Make sure that the names are consistent.
    # Current naming methods for the files with identifier '2025-07-01_'
    
    r_name_s = r_name  # Default to the original name
    f_name_s = f_name  # Default to the original name
    orient_r = 'south' # Default orientation for roof
    orient_f = 'south'

    if method == 'Sami': # Sami's method
        
        if r_name.__contains__('MPV_12'):
            r_name_s = 'MPV_12'
        elif r_name.__contains__('MPV_45'):
            r_name_s = 'MPV_45'

        if f_name.__contains__('MPV_Facade'):
            f_name_s = 'MPV_facade'
        elif f_name.__contains__('VBPV_large_F'):
            f_name_s = 'VBPV_large'
        elif (f_name.__contains__('VBPV_small')):
            f_name_s = 'VBPV_small'
        elif (f_name.__contains__('VBPV_hybrid')):
            f_name_s = 'VBPV_hybrid'


    elif method == 'Magda_shading': # 'Magda's method (for shading scenarios)

        if r_name.__contains__('MPV_12'):
            r_name_s = 'MPV_12'
        elif r_name.__contains__('MPV_45'):
            r_name_s = 'MPV_45'
            
        if r_name.__contains__('35deg'):
            orient_r = '35deg'

        
        if (f_name.__contains__('facade') & f_name.__contains__('_monofacial')):
            f_name_s = 'MPV_facade'
        elif (f_name.__contains__('_bifacial')):
            if (f_name.__contains__('large_facade')):
                f_name_s = 'VBPV_large'
            elif (f_name.__contains__('small_panels')):
                f_name_s = 'VBPV_small'
            elif (f_name.__contains__('small_and_large')):
                f_name_s = 'VBPV_hybrid'

        if f_name.__contains__('35deg'):
            orient_f = '35deg'
    
    # Reject if the orientations do not match
    if orient_r == orient_f:
        system_name = orient_r + '_' + r_name_s + '_' + f_name_s
        return system_name
    
    else:
        return 'Error: Orientations do not match!'