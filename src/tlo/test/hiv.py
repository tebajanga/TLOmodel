"""
Following the skeleton method for HIV
"""

# import any methods from other modules, e.g. for parameter definitions
from tlo import DateOffset, Module, Parameter, Property, Types
from tlo.events import PopulationScopeEventMixin, RegularEvent


import numpy as np
import pandas as pd


class HIV(Module):
    """Models HIV incidence, treatment and AIDS-mortality.

    Methods required:
    * `read_parameters(data_folder)`
    * `initialise_population(population)`
    * `initialise_simulation(sim)`
    * `on_birth(mother, child)`
    """

    # Here we declare parameters for this module. Each parameter has a name, data type,
    # and longer description.
    PARAMETERS = {
        'prob_infant_fast_progressor': Parameter(
            Types.LIST,
            'Probabilities that infants are fast or slow progressors'),
        'infant_progression_category': Parameter(
            Types.CATEGORICAL,
            'Classification of infants into fast or slow progressors'),
        'exp_rate_mort_infant_fast_progressor': Parameter(
            Types.REAL,
            'Exponential rate parameter for mortality in infants fast progressors'),
        'weibull_scale_mort_infant_slow_progressor': Parameter(
            Types.REAL,
            'Weibull scale parameter for mortality in infants slow progressors'),
        'weibull_shape_mort_infant_slow_progressor': Parameter(
            Types.REAL,
            'weibull shape parameter for mortality in infants slow progressors'),
        'weibull_shape_mort_adult': Parameter(
            Types.REAL,
            'Weibull shape parameter for mortality in adults'),
        'proportion_high_sexual_risk_male' : Parameter(
            Types.REAL,
            'proportion of men who have high sexual risk behaviour'),
        'proportion_high_sexual_risk_female': Parameter(
            Types.REAL,
            'proportion of women who have high sexual risk behaviour'),
        'rr_HIV_high_sexual_risk': Parameter(
            Types.REAL,
            'relative risk of acquiring HIV with high risk sexual behaviour'),
        'proportion_on_ART_infectious': Parameter(
            Types.REAL,
            'proportion of people on ART contributing to transmission as not virally suppressed'),
    }


    # Next we declare the properties of individuals that this module provides.
    # Again each has a name, type and description. In addition, properties may be marked
    # as optional if they can be undefined for a given individual.
    PROPERTIES = {
        'has_HIV': Property(Types.BOOL, 'HIV status'),
        'date_HIV_infection': Property(Types.DATE, 'Date acquired HIV infection'),
        'date_AIDS_death': Property(Types.DATE, 'Projected time of AIDS death if untreated'),
        'on_ART': Property(Types.BOOL, 'Currently on ART'),
        'ART_mortality' : Property(Types.REAL, 'Mortality rates whilst on ART'),
        'sexual_risk_group' : Property(Types.CATEGORICAL, 'Sexual risk group, high or low'),
    }

    def read_parameters(self, data_folder):
        """Read parameter values from file, if required.
        :param data_folder: path of a folder supplied to the Simulation containing data files.
          Typically modules would read a particular file within here.
        """

        params = self.parameters  # To save typing!
        params['prob_infant_fast_progressor'] = [0.36, 1-0.36]
        params['infant_progression_category'] = ['FAST', 'SLOW']
        params['exp_rate_mort_infant_fast_progressor'] = 1.08
        params['weibull_scale_mort_infant_slow_progressor'] = 16
        params['weibull_shape_mort_infant_slow_progressor'] = 2.7
        params['weibull_shape_mort_adult'] = 2
        params['proportion_high_sexual_risk_male'] = 0.0913
        params['proportion_high_sexual_risk_female'] = 0.0095
        params['rr_HIV_high_sexual_risk'] = 2
        params['proportion_on_ART_infectious'] = 0.2


    def initialise_population(self, population):
        """Set our property values for the initial population.

        This method is called by the simulation when creating the initial population, and is
        responsible for assigning initial values, for every individual, of those properties
        'owned' by this module, i.e. those declared in the PROPERTIES dictionary above.

        :param population: the population of individuals
        """
        raise NotImplementedError

    def initialise_simulation(self, sim):
        """Get ready for simulation start.

        This method is called just before the main simulation loop begins, and after all
        modules have read their parameters and the initial population has been created.
        It is a good place to add initial events to the event queue.
        """
        raise NotImplementedError

    def on_birth(self, mother, child):
        """Initialise our properties for a newborn individual.

        This is called by the simulation whenever a new person is born.

        :param mother: the mother for this child
        :param child: the new child
        """
        raise NotImplementedError





# read in data files #
# use function read.parameters in class HIV to do this?
file_path = 'Q:\Thanzi la Onse\HIV\Method_HIV.xlsx'

HIV_prev = pd.read_excel(file_path, sheet_name='prevalence2018', header=0)  # July 1st estimates not full year

HIV_ART = pd.read_excel(file_path, sheet_name='ART2009_2021', header=0)

ART_totals = pd.read_excel(file_path, sheet_name='aggregate_number_ART', header=0)

HIV_death = pd.read_excel(file_path, sheet_name='deaths2009_2021', header=0)

HIV_inc = pd.read_excel(file_path, sheet_name='incidence2009_2021', header=0)

ad_mort = pd.read_excel(file_path, sheet_name='mortality_rates', header=0)

paed_mortART = pd.read_excel(file_path, sheet_name='paediatric_mortality_rates', header=0)

CD4_base_M = pd.read_excel(file_path, sheet_name='CD4_distribution2018', header=0)

age_distr = pd.read_excel(file_path, sheet_name='age_distribution2018', header=0)

inds = pd.read_csv('Q:/Thanzi la Onse/HIV/initial_pop_dataframe2018.csv')
p = inds.shape[0]  # number of rows in pop (# individuals)

# # index data files #
sim_size = int(100)

timestep = 0.25  # run in 3 months time-steps so adjust all rates

start_time = 2009  # not needed if starting from 2018
current_time = 2018


# untreated HIV mortality rates - annual, adults
def log_scale(a0):
    age_scale = 2.55 - 0.025 * (a0 - 30)
    return age_scale


# Process functions

# NOTE new parameter names in class HIV
# assign high risk to M/F over 15 years
def high_risk_inds(inds):
    tmp = inds.index[(inds.sex == 'M') & (inds.age >= 15)]
    tmp2 = np.random.choice(tmp, size=int(round((high_risk_M * len(tmp)))), replace=False)

    tmp3 = inds.index[(inds.sex == 'F') & (inds.age >= 15)]
    tmp4 = np.random.choice(tmp3, size=int(round((high_risk_F * len(tmp3)))), replace=False)

    high_risk_index = np.concatenate([tmp2, tmp4])

    inds.loc[high_risk_index, 'risk'] = RR_HIV_high_risk

    return inds


# assign infected status using UNAIDS prevalence 2018 by age
# randomly allocate time since infection according to CD4 distributions from spectrum
# should do this separately for infants using CD4%
# then could include the infant fast progressors
# currently infant fast progressors will always have time to death shorter than time infected
def prevalence_inds(inds, current_time):
    CD_times = [current_time - 3.2, current_time - 7.8, current_time - 11.0, current_time - 13.9]
    prob_CD4 = [0.34, 0.31, 0.27, 0.08]

    for i in range(0, 81):
        # male
        # scale high/low-risk probabilities to sum to 1 for each sub-group
        prob_i = inds['risk'][(inds.age == i) & (inds.sex == 'M')] / \
                 np.sum(inds['risk'][(inds.age == i) & (inds.sex == 'M')])

        # sample from uninfected population using prevalence from UNAIDS
        tmp5 = np.random.choice(inds.index[(inds.age == i) & (inds.sex == 'M')],
                                size=int((HIV_prev['prevalence'][(HIV_prev.year == 2018) & (HIV_prev.sex == 'M') &
                                                                 (HIV_prev.age == i)]) / sim_size), replace=False,
                                p=prob_i)

        inds.loc[tmp5, 'status'] = 'I'  # change status to infected

        inds.loc[tmp5, 'timeInf'] = np.random.choice(CD_times, size=len(tmp5),
                                                     replace=True, p=prob_CD4)

        # female
        # scale high/low-risk probabilities to sum to 1 for each sub-group
        prob_i = inds['risk'][(inds.age == i) & (inds.sex == 'F')] / \
                 np.sum(inds['risk'][(inds.age == i) & (inds.sex == 'F')])

        # sample from uninfected population using prevalence from UNAIDS
        tmp6 = np.random.choice(inds.index[(inds.age == i) & (inds.sex == 'F')],
                                size=int((HIV_prev['prevalence'][(HIV_prev.year == 2018) & (HIV_prev.sex == 'F') &
                                                                 (HIV_prev.age == i)]) / sim_size),
                                replace=False, p=prob_i)

        inds.loc[tmp6, 'status'] = 'I'  # change status to infected

        inds.loc[tmp6, 'timeInf'] = np.random.choice(CD_times, size=len(tmp6),
                                                     replace=True, p=prob_CD4)

    # check time infected is less than time alive (especially for infants)
    tmp = inds.index[(pd.notna(inds.timeInf)) & ((current_time - inds.timeInf) > inds.age)]
    tmp2 = current_time - inds.loc[tmp, 'age']
    inds.loc[tmp, 'timeInf'] = tmp2  # replace with year of birth

    return inds


# initial number on ART ordered by longest duration of infection
# ART numbers are divided by sim_size
def initART_inds(inds, current_time):

    # select data for baseline year 2018
    hiv_art_f = HIV_ART['ART'][(HIV_ART.Year == 2018) & (HIV_ART.Sex == 'F')]  # returns vector ordered by age
    hiv_art_m = HIV_ART['ART'][(HIV_ART.Year == 2018) & (HIV_ART.Sex == 'M')]

    for i in range(0, 81):

        # male
        subgroup = inds[(inds.age == i) & (inds.status == 'I') & (inds.sex == 'M')]  # select each age-group
        subgroup.sort_values(by='timeInf', ascending=False, na_position='last')  # order by longest time infected
        art_slots = int(hiv_art_m.iloc[i] / sim_size)
        tmp = subgroup.id[0:art_slots]
        inds.loc[tmp, 'treat'] = 1
        inds.loc[tmp, 'timeTreated'] = current_time

        # female
        subgroup2 = inds[(inds.age == i) & (inds.status == 'I') & (inds.sex == 'F')]  # select each age-group
        subgroup2.sort_values(by='timeInf', ascending=False, na_position='last')  # order by longest time infected
        art_slots2 = int(hiv_art_f.iloc[i] / sim_size)
        tmp2 = subgroup2.id[0:art_slots2]
        inds.loc[tmp2, 'treat'] = 1
        inds.loc[tmp2, 'timeTreated'] = current_time

    return inds


def get_index(age_low, age_high, status, treated, current_time,
              length_treatment_low, length_treatment_high,
              optarg1=None, optarg2=None, optarg3=None):

    # optargs not needed for infant mortality rates (yet)
    # optarg1 = time from treatment start to death lower bound
    # optarg2 = time from treatment start to death upper bound
    # optarg3 = sex

    if optarg1 != None:

        index = inds.index[(inds.age >= age_low) & (inds.age < age_high) & (inds.sex == optarg3) &
                           (inds.status == status) & (inds.treat == treated) &
                           ((current_time - inds.timeTreated) > length_treatment_low) &
                           ((current_time - inds.timeTreated) <= length_treatment_high) &
                           (inds.timeDeath - inds.timeTreated >= optarg1) &
                           (inds.timeDeath - inds.timeTreated < optarg2)]
    else:
        index = inds.index[(inds.age >= age_low) & (inds.age < age_high) &
                           (inds.status == status) & (inds.treat == treated) &
                           ((current_time - inds.timeTreated) > length_treatment_low) &
                           ((current_time - inds.timeTreated) <= length_treatment_high)]

    return index

# assign mortality rates for those on ART
def ART_mort_inds(inds, current_time):

    # INFANTS
    # treated infant mortality averaged over all CD4%
    # could stratify by early / late treatment

    # infants 0-6 months on treatment
    # age < 1
    inds.loc[get_index(0, 1, 'I', 1, current_time, 0, 0.5), 'mortality'] = \
        paed_mortART['paed_mort'][(paed_mortART.time_on_ART == '0_6months') & (paed_mortART.age == '0')]

    # age 1-2
    inds.loc[get_index(1, 3, 'I', 1, current_time, 0, 0.5), 'mortality'] = \
        paed_mortART['paed_mort'][(paed_mortART.time_on_ART == '0_6months') & (paed_mortART.age == '1_2')]

    # age 3-4
    inds.loc[get_index(3, 5, 'I', 1, current_time, 0, 0.5), 'mortality'] = \
        paed_mortART['paed_mort'][(paed_mortART.time_on_ART == '0_6months') & (paed_mortART.age == '3_4')]

    # infants 7-12 months on treatment by age
    # age < 1
    inds.loc[get_index(0, 1, 'I', 1, current_time, 0.5, 1), 'mortality'] = \
        paed_mortART['paed_mort'][(paed_mortART.time_on_ART == '7_12months') & (paed_mortART.age == '0')]

    # age 1-2
    inds.loc[get_index(1, 3, 'I', 1, current_time, 0.5, 1), 'mortality'] = \
        paed_mortART['paed_mort'][(paed_mortART.time_on_ART == '7_12months') & (paed_mortART.age == '1_2')]

    # age 3-4
    inds.loc[get_index(3, 5, 'I', 1, current_time, 0.5, 1), 'mortality'] = \
        paed_mortART['paed_mort'][(paed_mortART.time_on_ART == '7_12months') & (paed_mortART.age == '3_4')]

    # infants >12 months on treatment by age
    # age < 1
    inds.loc[get_index(0, 1, 'I', 1, current_time, 1, np.Inf), 'mortality'] = \
        paed_mortART['paed_mort'][(paed_mortART.time_on_ART == '12months') & (paed_mortART.age == '0')]

    # age 1-2
    inds.loc[get_index(1, 3, 'I', 1, current_time, 1, np.Inf), 'mortality'] = \
        paed_mortART['paed_mort'][(paed_mortART.time_on_ART == '12months') & (paed_mortART.age == '1_2')]

    # age 3-4
    inds.loc[get_index(3, 5, 'I', 1, current_time, 1, np.Inf), 'mortality'] = \
        paed_mortART['paed_mort'][(paed_mortART.time_on_ART == '12months') & (paed_mortART.age == '3_4')]

    # ADULTS
    # early starters > 2 years to death when starting treatment
    # 0-6 months on treatment by four age groups
    # male age <25
    inds.loc[get_index(5, 25, 'I', 1, current_time, 0, 0.5, optarg1=2, optarg2=np.Inf, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age15_24') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y0_6E')]

    # male age 25-34
    inds.loc[get_index(25, 35, 'I', 1, current_time, 0, 0.5, optarg1=2, optarg2=np.Inf, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age25_34') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y0_6E')]

    # male age 35-44
    inds.loc[get_index(25, 45, 'I', 1, current_time, 0, 0.5, optarg1=2, optarg2=np.Inf, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age35_44') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y0_6E')]

    # male age >= 45
    inds.loc[get_index(45, np.Inf, 'I', 1, current_time, 0, 0.5, optarg1=2, optarg2=np.Inf, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age45') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y0_6E')]

    # female age <25
    inds.loc[get_index(5, 25, 'I', 1, current_time, 0, 0.5, optarg1=2, optarg2=np.Inf, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age15_24') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y0_6E')]

    # female age 25-34
    inds.loc[get_index(25, 35, 'I', 1, current_time, 0, 0.5, optarg1=2, optarg2=np.Inf, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age25_34') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y0_6E')]

    # female age 35-44
    inds.loc[get_index(25, 45, 'I', 1, current_time, 0, 0.5, optarg1=2, optarg2=np.Inf, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age35_44') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y0_6E')]

    # female age >= 45
    inds.loc[get_index(45, np.Inf, 'I', 1, current_time, 0, 0.5, optarg1=2, optarg2=np.Inf, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age45') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y0_6E')]

    # 7-12 months on treatment by four age groups
    # male age <25
    inds.loc[get_index(5, 25, 'I', 1, current_time, 0.5, 2, optarg1=2, optarg2=np.Inf, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age15_24') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y7_12E')]

    # male age 25-34
    inds.loc[get_index(25, 35, 'I', 1, current_time, 0.5, 2, optarg1=2, optarg2=np.Inf, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age25_34') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y7_12E')]

    # male age 35-44
    inds.loc[get_index(25, 45, 'I', 1, current_time, 0.5, 2, optarg1=2, optarg2=np.Inf, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age35_44') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y7_12E')]

    # male age >= 45
    inds.loc[get_index(45, np.Inf, 'I', 1, current_time, 0.5, 2, optarg1=2, optarg2=np.Inf, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age45') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y7_12E')]

    # female age <25
    inds.loc[get_index(5, 25, 'I', 1, current_time, 0.5, 2, optarg1=2, optarg2=np.Inf, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age15_24') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y7_12E')]

    # female age 25-34
    inds.loc[get_index(25, 35, 'I', 1, current_time, 0.5, 2, optarg1=2, optarg2=np.Inf, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age25_34') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y7_12E')]

    # female age 35-44
    inds.loc[get_index(25, 45, 'I', 1, current_time, 0.5, 2, optarg1=2, optarg2=np.Inf, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age35_44') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y7_12E')]

    # female age >= 45
    inds.loc[get_index(45, np.Inf, 'I', 1, current_time, 0.5, 2, optarg1=2, optarg2=np.Inf, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age45') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y7_12E')]

    # > 12 months on treatment by four age groups
    # male age <25
    inds.loc[get_index(5, 25, 'I', 1, current_time, 2, np.Inf, optarg1=2, optarg2=np.Inf, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age15_24') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y12E')]

    # male age 25-34
    inds.loc[get_index(25, 35, 'I', 1, current_time, 2, np.Inf, optarg1=2, optarg2=np.Inf, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age25_34') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y7_12E')]

    # male age 35-44
    inds.loc[get_index(25, 45, 'I', 1, current_time, 2, np.Inf, optarg1=2, optarg2=np.Inf, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age35_44') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y12E')]

    # male age >= 45
    inds.loc[get_index(45, np.Inf, 'I', 1, current_time, 2, np.Inf, optarg1=2, optarg2=np.Inf, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age45') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y12E')]

    # female age <25
    inds.loc[get_index(5, 25, 'I', 1, current_time, 2, np.Inf, optarg1=2, optarg2=np.Inf, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age15_24') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y12E')]

    # female age 25-34
    inds.loc[get_index(25, 35, 'I', 1, current_time, 2, np.Inf, optarg1=2, optarg2=np.Inf, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age25_34') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y12E')]

    # female age 35-44
    inds.loc[get_index(25, 45, 'I', 1, current_time, 2, np.Inf, optarg1=2, optarg2=np.Inf, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age35_44') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y12E')]

    # female age >= 45
    inds.loc[get_index(45, np.Inf, 'I', 1, current_time, 2, np.Inf, optarg1=2, optarg2=np.Inf, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age45') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y12E')]

    # late starters < 2 years to death when starting treatment
    # 0-6 months on treatment by four age groups
    # male age <25
    inds.loc[get_index(5, 25, 'I', 1, current_time, 0, 0.5, optarg1=0, optarg2=2, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age15_24') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y0_6L')]

    # male age 25-34
    inds.loc[get_index(25, 35, 'I', 1, current_time, 0, 0.5, optarg1=0, optarg2=2, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age25_34') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y0_6L')]

    # male age 35-44
    inds.loc[get_index(25, 45, 'I', 1, current_time, 0, 0.5, optarg1=0, optarg2=2, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age35_44') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y0_6L')]

    # male age >= 45
    inds.loc[get_index(45, np.Inf, 'I', 1, current_time, 0, 0.5, optarg1=0, optarg2=2, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age45') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y0_6L')]

    # female age <25
    inds.loc[get_index(5, 25, 'I', 1, current_time, 0, 0.5, optarg1=0, optarg2=2, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age15_24') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y0_6L')]

    # female age 25-34
    inds.loc[get_index(25, 35, 'I', 1, current_time, 0, 0.5, optarg1=0, optarg2=2, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age25_34') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y0_6L')]

    # female age 35-44
    inds.loc[get_index(25, 45, 'I', 1, current_time, 0, 0.5, optarg1=0, optarg2=2, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age35_44') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y0_6L')]

    # female age >= 45
    inds.loc[get_index(45, np.Inf, 'I', 1, current_time, 0, 0.5, optarg1=0, optarg2=2, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age45') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y0_6L')]

    # 7-12 months on treatment by four age groups
    # male age <25
    inds.loc[get_index(5, 25, 'I', 1, current_time, 0.5, 2, optarg1=0, optarg2=2, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age15_24') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y7_12L')]

    # male age 25-34
    inds.loc[get_index(25, 35, 'I', 1, current_time, 0.5, 2, optarg1=0, optarg2=2, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age25_34') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y7_12L')]

    # male age 35-44
    inds.loc[get_index(25, 45, 'I', 1, current_time, 0.5, 2, optarg1=0, optarg2=2, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age35_44') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y7_12L')]

    # male age >= 45
    inds.loc[get_index(45, np.Inf, 'I', 1, current_time, 0.5, 2, optarg1=0, optarg2=2, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age45') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y7_12EL')]

    # female age <25
    inds.loc[get_index(5, 25, 'I', 1, current_time, 0.5, 2, optarg1=0, optarg2=2, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age15_24') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y7_12L')]

    # female age 25-34
    inds.loc[get_index(25, 35, 'I', 1, current_time, 0.5, 2, optarg1=0, optarg2=2, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age25_34') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y7_12L')]

    # female age 35-44
    inds.loc[get_index(25, 45, 'I', 1, current_time, 0.5, 2, optarg1=0, optarg2=2, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age35_44') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y7_12L')]

    # female age >= 45
    inds.loc[get_index(45, np.Inf, 'I', 1, current_time, 0.5, 2, optarg1=0, optarg2=2, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age45') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y7_12L')]

    # > 12 months on treatment by four age groups
    # male age <25
    inds.loc[get_index(5, 25, 'I', 1, current_time, 2, np.Inf, optarg1=0, optarg2=2, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age15_24') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y12L')]

    # male age 25-34
    inds.loc[get_index(25, 35, 'I', 1, current_time, 2, np.Inf, optarg1=0, optarg2=2, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age25_34') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y7_12L')]

    # male age 35-44
    inds.loc[get_index(25, 45, 'I', 1, current_time, 2, np.Inf, optarg1=0, optarg2=2, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age35_44') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y12L')]

    # male age >= 45
    inds.loc[
        get_index(45, np.Inf, 'I', 1, current_time, 2, np.Inf, optarg1=0, optarg2=2, optarg3='M'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age45') & (ad_mort.sex == 'M') & (ad_mort.ART == 'Y12L')]

    # female age <25
    inds.loc[get_index(5, 25, 'I', 1, current_time, 2, np.Inf, optarg1=0, optarg2=2, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age15_24') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y12L')]

    # female age 25-34
    inds.loc[get_index(25, 35, 'I', 1, current_time, 2, np.Inf, optarg1=0, optarg2=2, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age25_34') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y12L')]

    # female age 35-44
    inds.loc[get_index(25, 45, 'I', 1, current_time, 2, np.Inf, optarg1=0, optarg2=2, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age35_44') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y12L')]

    # female age >= 45
    inds.loc[get_index(45, np.Inf, 'I', 1, current_time, 2, np.Inf, optarg1=0, optarg2=2, optarg3='F'), 'mortality'] = \
        ad_mort['rate'][(ad_mort.age == 'age45') & (ad_mort.sex == 'F') & (ad_mort.ART == 'Y12L')]

    return inds


def init_death_inds(inds, current_time):
    # PAEDIATRIC time of death
    hiv_inf = inds.index[(inds.status == 'I') & (inds.treat == 0) & (inds.age < 3)]

    # need a two parameter Weibull with size parameter, multiply by scale instead
    time_of_death_slow = np.random.weibull(a=s, size=len(hiv_inf)) * mu

    # while time of death is shorter than time infected keep redrawing (only for the entries that need it)
    while np.any(
            time_of_death_slow < (current_time - inds.loc[hiv_inf, 'timeInf'])):  # if any condition=TRUE for any rows

        redraw = np.argwhere(time_of_death_slow < (current_time - inds.loc[hiv_inf, 'timeInf']))
        redraw2 = redraw.ravel()

        if len(redraw) == 0:
            break

        # redraw time of death
        time_of_death_slow[redraw2] = np.random.weibull(a=s, size=len(redraw2)) * mu

    # subtract time already spent
    inds.loc[hiv_inf, 'timeDeath'] = current_time + time_of_death_slow - (current_time - inds.loc[hiv_inf, 'timeInf'])

    # ADULT time of death, adults are all those aged >3 for untreated mortality rates
    hiv_ad = inds.index[(inds.status == 'I') & (inds.treat == 0) & (inds.age >= 3)]

    time_of_death = np.random.weibull(a=s2, size=len(hiv_ad)) * np.exp(log_scale(inds.loc[hiv_ad, 'age']))

    # while time of death is shorter than time infected keep redrawing (only for entries that need it)
    while np.any(time_of_death < (current_time - inds.loc[hiv_ad, 'timeInf'])):  # if any condition=TRUE for any rows

        redraw = np.argwhere(time_of_death < (current_time - inds.loc[hiv_ad, 'timeInf']))
        redraw2 = redraw.ravel()

        if len(redraw) < 10:  # this condition needed for older people with long time since infection
            break

        age_index = hiv_ad[redraw2]

        time_of_death[redraw2] = np.random.weibull(a=s2, size=len(redraw2)) * np.exp(
            log_scale(inds.loc[age_index, 'age']))

    # subtract time already spent
    inds.loc[hiv_ad, 'timeDeath'] = current_time + time_of_death - (current_time - inds.loc[hiv_ad, 'timeInf'])

    # assign mortality rates on ART
    inds = ART_mort_inds(inds, current_time)

    return inds


def inf_inds_ad(inds, current_time, beta_ad):
    infected = len(inds[(inds.status == 'I') & (inds.treat == 0) & (inds.age >= 15)])  # number infected untreated

    h_infected = h * len(inds[(inds.status == 'I') & (inds.treat == 1) & (inds.age >= 15)])  # number infected treated

    total_pop = len(inds[(inds.age >= 15)])  # whole population over 15 years

    foi = beta_ad * ((infected + h_infected) / total_pop)  # force of infection for adults

    # distribute FOI by age
    foi_m = foi * age_distr['age_distribution'][(age_distr.year == 2018) & (age_distr.sex == 'M')]  # age 15-80+
    foi_f = foi * age_distr['age_distribution'][(age_distr.year == 2018) & (age_distr.sex == 'F')]

    for i in range(66):  # ages 15-80
        age_value = i + 14 # adults only FOI

        # males
        susceptible_age = len(inds[(inds.age == age_value) & (inds.sex == 'M') & (inds.status == 'U')])

        # to determine number of new infections by age
        tmp1 = np.random.binomial(1, p=foi_m[i], size=susceptible_age)

        # allocate infections to people with high/low risk
        # scale high/low-risk probabilities to sum to 1 for each sub-group
        risk = inds['risk'][(inds.age == age_value) & (inds.sex == 'M') & (inds.status == 'U')] / \
            np.sum(inds['risk'][(inds.age == age_value) & (inds.sex == 'M') & (inds.status == 'U')])

        tmp2 = np.random.choice(inds.index[(inds.age == age_value) & (inds.sex == 'M') & (inds.status == 'U')],
                                size=len(tmp1), p=risk, replace=False)

        inds.loc[tmp2, 'status'] = 'I'  # change status to infected
        inds.loc[tmp2, 'timeInf'] = current_time

        inds.loc[tmp2, 'timeDeath'] = current_time + (
                    np.random.weibull(a=s2, size=len(tmp2)) * np.exp(log_scale(inds.age.iloc[tmp2])))

        # females
        susceptible_age = len(inds[(inds.age == age_value) & (inds.sex == 'F') & (inds.status == 'U')])

        # to determine number of new infections by age
        tmp3 = np.random.binomial(1, p=foi_f[i], size=susceptible_age)

        # allocate infections to people with high/low risk
        # scale high/low-risk probabilities to sum to 1 for each sub-group
        risk = inds['risk'][(inds.age == age_value) & (inds.sex == 'F') & (inds.status == 'U')] /\
            np.sum(inds['risk'][(inds.age == age_value) & (inds.sex == 'F') & (inds.status == 'U')])

        tmp4 = np.random.choice(inds.index[(inds.age == age_value) & (inds.sex == 'F') & (inds.status == 'U')],
                                size=len(tmp3), p=risk, replace=False)

        inds.loc[tmp4, 'status'] = 'I'  # change status to infected
        inds.loc[tmp4, 'timeInf'] = current_time

        inds.loc[tmp2, 'timeDeath'] = current_time + (
                    np.random.weibull(a=s2, size=len(tmp4)) * np.exp(log_scale(inds.age.iloc[tmp4])))

    return inds


# need a function to define probability of infant infection given mother's HIV status

def ART_inds(inds, current_time):
    # look at how many slots are currently taken
    # then check number available for current year
    # remember to divide by sim_size
    # allocate any unfilled ART slots by longest time infected

    # total number of ART slots available 2018
    ART_infants = int(ART_totals['number_on_ART'][(ART_totals.year == 2018) & (ART_totals.age == '0_14')] / sim_size)
    ART_adults = int(ART_totals['number_on_ART'][(ART_totals.year == 2018) & (ART_totals.age == '15_80')] / sim_size)

    # infants - this treats older kids first as they've been infected longer
    # less likely to have infants treated close to birth/infection
    tmp1 = len(inds[(inds.treat == 1) & (inds.age < 15)])  # current number on ART
    diff_inf = ART_infants - tmp1

    if diff_inf < 0:
        diff_inf = 0  # replace negative values with zero

    subgroup = inds[(inds.age < 15) & (inds.treat == 0) & (inds.status == 'I')]
    subgroup = subgroup.sort_values(by='timeInf', ascending=True, na_position='last')  # order by earliest time infected
    tmp2 = subgroup.id[0:(diff_inf + 1)]
    inds.loc[tmp2, 'treat'] = 1
    inds.loc[tmp2, 'timeTreated'] = current_time

    # adults
    tmp3 = len(inds[(inds.treat == 1) & (inds.age >= 15)])  # current number on ART
    diff_ad = ART_adults - tmp3

    if diff_ad < 0:
        diff_ad = 0  # replace negative values with zero

    subgroup2 = inds[(inds.age >= 15) & (inds.treat == 0) & (inds.status == 'I')]
    subgroup2 = subgroup2.sort_values(by='timeInf', ascending=True, na_position='last')  # order by earliest time infected
    tmp4 = subgroup2.id[0:(diff_ad + 1)]
    inds.loc[tmp4, 'treat'] = 1
    inds.loc[tmp4, 'timeTreated'] = current_time

    return inds


# run the death functions once a year
def killHIV_inds(inds, current_time):
    # choose which ones die at current_time
    current_time_int = int(round(current_time))  # round current_time to nearest year

    tmp = inds.index[(round(inds.timeDeath) == current_time_int) & (inds.treat == 0)]

    inds.loc[tmp, 'status'] = 'DH'

    return inds


def killHIV_ART_inds(inds):
    tmp1 = np.random.uniform(low=0, high=1, size=inds.shape[0])  # random number for every entry

    tmp2 = inds.index[(pd.notna(inds.mortality)) & (tmp1 < inds['mortality']) &
                      (inds.status == 'I') & (inds.treat == 1)]

    inds.loc[tmp2, 'status'] = 'DH'

    return inds


# to set up the baseline population
inds.head(20)
inds.describe(include='all')
inds['status'].value_counts()

inds = high_risk_inds(inds)
inds = prevalence_inds(inds, current_time)
inds = initART_inds(inds, current_time)
inds = init_death_inds(inds, current_time)

inds.head(20)
inds.describe(include='all')
inds['status'].value_counts()
inds['treat'].value_counts()


# to run projections set up these commands in a loop
# example for 2019 projections with placeholder transmission rate beta_ad=0.12
inds = inf_inds_ad(inds, 2019, 0.12)
inds = ART_inds(inds, 2019)
inds = killHIV_inds(inds, 2019)
inds = killHIV_ART_inds(inds)

inds.describe(include='all')
inds['status'].value_counts()
inds['treat'].value_counts()

# TODO: handle births. link child's risk of HIV to mother's HIV status
# TODO: separate HIV infection and ART methods
# TODO: include cotrimoxazole for children
# TODO: code FOI as separate function from infection function
