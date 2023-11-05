def mdof_simple_model(story_force_dictionary, section_dictionary, drift_limit=0.02):
    '''
    Input:
    - story_force_dictionary - dictionary of story forces, with keys as story elevations and values as story forces
    - section_dictionary - dictionary of core section, with keys as story elevations and values as core dimensions [length, thickness, reinforcement_ratio]
    - drift_limit - drift limit for the building: 0.02 for seismic, 0.0025 for wind
    Output:
    - shear_force_dcr - dictionary of story shear capacity demand/capacity ratio
    - moment_dcr - dictionary of story moment capacity demand/capacity ratio
    - drift_dcr - drift demand/capacity ratio
    '''

    def calculate_shear_diagram(story_force_dictionary):
        '''
        Input: story_force_dictionary - dictionary of story forces, with keys as story elevations and values as story forces
        Output: shear_forces - dictionary of story shear forces
        '''
        # Sort the keys (elevations) in descending order
        sorted_elevations = sorted(story_force_dictionary.keys(), reverse=True)
        
        shear_forces = {}
        cumulative_force = 0

        # Calculate the shear force for each elevation
        for elevation in sorted_elevations:
            cumulative_force += story_force_dictionary[elevation]
            shear_forces[elevation] = cumulative_force

        # Sort the dictionary with keys in ascending order
        shear_forces = dict(sorted(shear_forces.items()))

        return shear_forces

    def calculate_moment_diagram(shear_force_dictionary):
        '''
        Input: shear_force_dictionary - dictionary of shear forces, with keys as story elevations and values as shear forces
        Output: moment_diagram - dictionary of story moments
        '''
        # Get the sorted elevations in descending order
        sorted_elevations = sorted(shear_force_dictionary.keys(), reverse=True)
        
        moments = {}
        cumulative_moment = 0
        prev_elevation = max(sorted_elevations)

        # Calculate the moment for each elevation
        for elevation in sorted_elevations:
            delta_z = prev_elevation - elevation
            cumulative_moment += shear_force_dictionary[prev_elevation] * delta_z
            moments[elevation] = cumulative_moment
            prev_elevation = elevation

        # Sort the dictionary with keys in ascending order
        moments = dict(sorted(moments.items()))

        return moments

    def check_shear_capacity(shear_force_dictionary, section_dictionary):
        '''
        Input: 
        - shear_force_dictionary - dictionary of shear forces, with keys as story elevations and values as shear forces
        - section_dictionary - dictionary of core section, with keys as story elevations and values as core dimensions [length, thickness, reinforcement_ratio]

        Output: shear_capacity_dcr - dictionary of story shear capacity demand/capacity ratio
        '''

        elevations = shear_force_dictionary.keys()

        shear_capacity = {}
        shear_capacity_dcr = {}

        # Calculate the shear capacity for each elevation
        # wall openings are ignored, same wall length and thickness in both directions
        # shear capacity of the flange is ignored
        # Assume phi * 8sqrt(f'c) and f'c = 6,000 psi
        for z in elevations:
            core_length = section_dictionary[z][0]
            core_thickness = section_dictionary[z][1]

            core_shear_area = 2 * 0.8 * core_length * core_thickness * 144 # in^2
            core_concrete_strength = 6000 # psi

            shear_capacity[z] = 0.75 * 8 * (core_concrete_strength ** 0.5) * core_shear_area / 1000 # kips
            dcr = shear_force_dictionary[z] / shear_capacity[z]
            
            shear_capacity_dcr[z]= round(dcr, 2)      

        return shear_capacity_dcr


    def check_moment_capacity(moment_dictionary, section_dictionary):
        '''
        Input : 
        - moment_dictionary - dictionary of moments, with keys as story elevations and values as moments
        - section_dictionary - dictionary of core section, with keys as story elevations and values as core dimensions [length, thickness, reinforcement_ratio]
        
        Output: moment_capacity_dcr - dictionary of story moment capacity demand/capacity
        '''

        elevations = moment_dictionary.keys()

        moment_capacity = {}
        moment_capacity_dcr = {}

        # Calculate the moment capacity for each elevation
        # wall openings are ignored, same wall length and thickness in both directions
        # Moment capacity is calculated using the simplified method where web reinforcement is ignored
        for z in elevations:
            core_length = section_dictionary[z][0]
            core_thickness = section_dictionary[z][1]
            core_reinforcement_ratio = section_dictionary[z][2]
            core_flange_area = core_thickness * core_length
        
            flange_reinforcement_area = core_reinforcement_ratio * core_flange_area * 144 # in^2

            core_reinforcement_fy = 60 #ksi

            moment_arm = 0.8 * 0.9 * core_length # jd * core_length = 0.8 x 0.9 x core_length

            moment_capacity[z] = 0.9 * flange_reinforcement_area * core_reinforcement_fy * moment_arm #kip-ft
            dcr = moment_dictionary[z] / moment_capacity[z]

            moment_capacity_dcr[z] = round(dcr, 2)

        return moment_capacity_dcr


    def cantilever_deflection(moment_dictionary, section_dictionary):
        """
        Calculate the cantilever deflection using the moment-area method.
        
        Parameters:
        - curvatures: dict where keys are z elevations and values are curvatures (M/EI).
        
        Returns:
        - dict where keys are z elevations and values are deflections.
        """
        # Sorting the elevations in descending order
        z_values = sorted(moment_dictionary.keys())

        min_elevation = min(z_values)

        # Calculate the curvature for each elevation
        curvatures = {}
        for z in z_values:
            core_length = section_dictionary[z][0]
            core_thickness = section_dictionary[z][1]
            core_flange_area = core_thickness * core_length

            moment_of_inertia = 2 * core_thickness * (core_length - 2 * core_thickness) ** 3 / 12 + 2 * core_flange_area * (core_length - 2*core_thickness) ** 2 / 4
            concrete_modulus_of_elasticity = 57 * (6000)**0.5 # ksi

            cracking_factor = 0.5 # average cracking factor for cracked and uncracked sections

            curvatures[z] = moment_dictionary[z] / (cracking_factor * moment_of_inertia * concrete_modulus_of_elasticity)

        
        theta_values = {}
        u_values = {}
        
        theta_previous = 0
        u_previous = 0
        
        for i in range(len(z_values) - 1):
            z1, z2 = z_values[i], z_values[i+1]
            curvature_avg = (curvatures[z1] + curvatures[z2]) / 2
            
            # Calculate area under curvature graph between z1 and z2 (using average value)
            area = curvature_avg * (z2 - z1)
            
            # Calculate slope using the area under the curvature graph
            theta = theta_previous + area
            
            # Calculate deflection using the average slope between two points and the distance
            u = u_previous + (theta_previous + theta) / 2 * (z2 - z1)
            
            theta_values[z2] = theta
            u_values[z2] = u
            
            theta_previous = theta
            u_previous = u

        u_values[min_elevation] = 0

        u_values = dict(sorted(u_values.items()))

        return u_values


    def drift_check(deflection_dictionary, drift_limit):
        """
        Check the deflection of the cantilever.
        
        Parameters:
        - deflection_dictionary: dict where keys are z elevations and values are deflections.    
        Returns:
        - deflection_check: True if deflection is less than 0.002 * story_height.
        """

        building_height = max(deflection_dictionary.keys())

        max_deflection = max(deflection_dictionary.values())

        roof_drift = max_deflection / building_height

        drift_dcr = roof_drift / drift_limit

        return drift_dcr

    # calculate shear forces over building height
    shear_forces = calculate_shear_diagram(story_force_dictionary)
    
    # calculate moments over building height
    moments = calculate_moment_diagram(shear_forces)

    # check shear capacity
    shear_force_dcr = check_shear_capacity(shear_forces, section_dictionary)
    
    # check moment capacity
    moment_dcr = check_moment_capacity(moments, section_dictionary)

    # calculate story displacements
    lateral_displacement = cantilever_deflection(moments, section_dictionary)

    # check deflection
    drift_dcr = drift_check(lateral_displacement, drift_limit)

    return {'shear_dcr':shear_force_dcr, 'moment_dcr':moment_dcr, 'drift_dcr':drift_dcr}
     

if __name__ == "__main__":

    section_dictionary = {0: [20, 1, 0.01], 10: [20, 1, 0.01], 20: [20, 1, 0.01], 30: [20, 1, 0.01], 40: [20, 1, 0.01]}
    test_story_forces = {0: 0, 10: 100, 20: 200, 30: 300, 40: 400}    


    print(mdof_simple_model(test_story_forces, section_dictionary, 0.02))