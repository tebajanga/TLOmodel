"""
A skeleton template for disease methods.
"""
import numpy as np
import pandas as pd

from tlo import DateOffset, Module, Parameter, Property, Types
from tlo.events import PopulationScopeEventMixin, RegularEvent, Event, IndividualScopeEventMixin


class Mockitis(Module):
    """
    One line summary goes here...

    All disease modules need to be implemented as a class inheriting from Module.
    They need to provide several methods which will be called by the simulation
    framework:
    * `read_parameters(data_folder)`
    * `initialise_population(population)`
    * `initialise_simulation(sim)`
    * `on_birth(mother, child)`
    """

    # Here we declare parameters for this module. Each parameter has a name, data type,
    # and longer description.
    PARAMETERS = {
        'p_infection': Parameter(Types.REAL, 'Probability that an uninfected individual becomes infected'),
        'p_cure': Parameter(Types.REAL, 'Probability that an infected individual is cured'),
        'initial_prevalence': Parameter(Types.REAL, 'Prevalence of the disease in the population'),
    }

    # Next we declare the properties of individuals that this module provides.
    # Again each has a name, type and description. In addition, properties may be marked
    # as optional if they can be undefined for a given individual.
    PROPERTIES = {
        'mi_is_infected': Property(Types.BOOL, 'Current status of mockitis'),
        'mi_status': Property(Types.CATEGORICAL,
                              'Historical status: N=never; T1=type 1; T2=type 2; P=previously',
                              categories=['N', 'T1', 'T2', 'P', 'NT1', 'NT2']),
        'mi_date_infected': Property(Types.DATE, 'Date of latest infection'),
        'mi_date_death': Property(Types.DATE, 'Date of death of infected individual'),
        'mi_date_cure': Property(Types.DATE, 'Date an infected individual was cured'),
    }

    def read_parameters(self, data_folder):
        """Read parameter values from file, if required.

        Here we do nothing.

        :param data_folder: path of a folder supplied to the Simulation containing data files.
          Typically modules would read a particular file within here.
        """
        params = self.parameters
        params['p_infection'] = 0.01
        params['p_cure'] = 0.01
        params['initial_prevalence'] = 0.05


    def initialise_population(self, population):
        """Set our property values for the initial population.

        This method is called by the simulation when creating the initial population, and is
        responsible for assigning initial values, for every individual, of those properties
        'owned' by this module, i.e. those declared in the PROPERTIES dictionary above.

        :param population: the population of individuals
        """

        df = population.props  # a shortcut to the dataframe storing data for individuals

        df['mi_is_infected'] = False  # default: no individuals infected
        df['mi_status'].values[:] = 'N'  # default: never infected, this is how you initialise a categorical
        df['mi_date_infected'] = pd.NaT  # default: not a time
        df['mi_date_death'] = pd.NaT  # default: not a time
        df['mi_date_cure'] = pd.NaT  # default: not a time

        # randomly selected some individuals as infected
        initial_infected = self.parameters['initial_prevalence']
        initial_uninfected = 1 - initial_infected
        df['mi_is_infected'] = np.random.choice([True, False], size=len(df), p=[initial_infected, initial_uninfected])

        # get all the infected individuals
        infected_count = df.mi_is_infected.sum()

        # date of infection of infected individuals
        infected_years_ago = np.random.exponential(scale=5, size=infected_count)  # sample years in the past
        # pandas requires 'timedelta' type for date calculations
        infected_td_ago = pd.to_timedelta(infected_years_ago, unit='y')

        # date of death of the infected individuals (in the future)
        death_years_ahead = np.random.exponential(scale=2, size=infected_count)
        death_td_ahead = pd.to_timedelta(death_years_ahead, unit='y')

        # set the properties of infected individuals
        df.loc[df.mi_is_infected, 'mi_date_infected'] = self.sim.date - infected_td_ago
        df.loc[df.mi_is_infected, 'mi_date_death'] = self.sim.date + death_td_ahead

        age = population.age
        df.loc[df.mi_is_infected & (age.years > 15), 'mi_status'] = 'T1'
        df.loc[df.mi_is_infected & (age.years <= 15), 'mi_status'] = 'T2'

    def initialise_simulation(self, sim):
        """Get ready for simulation start.

        This method is called just before the main simulation loop begins, and after all
        modules have read their parameters and the initial population has been created.
        It is a good place to add initial events to the event queue.
        """
        # add the basic event (we will implement below)
        event = MockitisEvent(self)
        sim.schedule_event(event, sim.date + DateOffset(months=1))

        # add an event to log to screen
        sim.schedule_event(MockitisLoggingEvent(self), sim.date + DateOffset(months=6))

        # add the death event of infected individuals
        df = sim.population.props
        infected_individuals = df[df.mi_is_infected].index
        for index in infected_individuals:
            individual = self.sim.population[index]
            death_event = MockitisDeathEvent(self, individual)
            self.sim.schedule_event(death_event, individual.mi_date_death)

    def on_birth(self, mother, child):
        """Initialise our properties for a newborn individual.

        This is called by the simulation whenever a new person is born.

        :param mother: the mother for this child
        :param child: the new child
        """
        pass


class MockitisEvent(RegularEvent, PopulationScopeEventMixin):

    def __init__(self, module):
        super().__init__(module, frequency=DateOffset(months=1))
        self.p_infection = module.parameters['p_infection']
        self.p_cure = module.parameters['p_cure']

    def apply(self, population):
        df = population.props

        # 1. get (and hold) index of currently infected and uninfected individuals
        currently_infected = df.index[df.mi_is_infected & df.is_alive]
        currently_uninfected = df.index[~df.mi_is_infected & df.is_alive]

        # 2. handle new infections
        now_infected = np.random.choice([True, False], size=len(currently_uninfected),
                                        p=[self.p_infection, 1 - self.p_infection])
        # if any are infected
        if now_infected.sum():
            infected_idx = currently_uninfected[now_infected]

            df.loc[infected_idx, 'mi_date_infected'] = self.sim.date
            df.loc[infected_idx, 'mi_date_death'] = self.sim.date + pd.Timedelta(25, unit='Y')
            df.loc[infected_idx, 'mi_date_cure'] = pd.NaT
            df.loc[infected_idx, 'mi_is_infected'] = True

            infected_age = population.age.loc[infected_idx]
            infected_lte_15 = infected_idx.intersection(infected_age.index[infected_age.years <= 15])
            infected_gt_15 = infected_idx.intersection(infected_age.index[infected_age.years > 15])

            df.loc[infected_gt_15, 'mi_status'] = 'NT1'
            df.loc[infected_lte_15, 'mi_status'] = 'NT2'

            # schedule death events for newly infected individuals
            for index in infected_idx:
                individual = self.sim.population[index]
                death_event = MockitisDeathEvent(self, individual)
                self.sim.schedule_event(death_event, individual.mi_date_death)

        # 3. handle cures
        cured = np.random.choice([True, False], size=len(currently_infected), p=[self.p_cure, 1 - self.p_cure])

        if cured.sum():
            cured = currently_infected[cured]
            df.loc[cured, 'mi_is_infected'] = False
            df.loc[cured, 'mi_status'] = 'P'
            df.loc[cured, 'mi_date_death'] = pd.NaT
            df.loc[cured, 'mi_date_cure'] = self.sim.date


# need to pass the individual to this class not just the population dataframe
class MockitisDeathEvent(Event, IndividualScopeEventMixin):
    def __init__(self, module, individual):
        super().__init__(module, person=individual)

    def apply(self, individual):
        pass


class MockitisLoggingEvent(RegularEvent, PopulationScopeEventMixin):
    def __init__(self, module):
        """comments...
        """
        # run this event every month
        self.repeat = 6
        super().__init__(module, frequency=DateOffset(months=self.repeat))

    def apply(self, population):
        # get some summary statistics
        df = population.props

        infected_total = df.mi_is_infected.sum()
        proportion_infected = infected_total / len(df)

        mask = (df['mi_date_infected'] > self.sim.date - DateOffset(months=self.repeat))
        infected_in_last_month = mask.sum()
        mask = (df['mi_date_cure'] > self.sim.date - DateOffset(months=self.repeat))
        cured_in_last_month = mask.sum()

        counts = {'N': 0, 'T1': 0, 'T2': 0, 'P': 0}
        counts.update(df['mi_status'].value_counts().to_dict())
        status = 'Status: { N: %(N)d; T1: %(T1)d; T2: %(T2)d; P: %(P)d }' % counts

        self.module.store.append(proportion_infected)

        print('%s - Mockitis: {TotInf: %d; PropInf: %.3f; PrevMonth: {Inf: %d; Cured: %d}; %s }' %
              (self.sim.date,
               infected_total,
               proportion_infected,
               infected_in_last_month,
               cured_in_last_month,
               status), flush=True)


