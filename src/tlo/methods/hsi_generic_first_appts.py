"""
The file contains the event HSI_GenericFirstApptAtFacilityLevel1, which describes the first interaction with
the health system following the onset of acute generic symptoms.
"""
from tlo import logging
from tlo.events import IndividualScopeEventMixin
from tlo.methods.bladder_cancer import (
    HSI_BladderCancer_Investigation_Following_Blood_Urine,
    HSI_BladderCancer_Investigation_Following_pelvic_pain,
)
from tlo.methods.chronicsyndrome import HSI_ChronicSyndrome_SeeksEmergencyCareAndGetsTreatment
from tlo.methods.healthsystem import HSI_Event
from tlo.methods.labour import (
    HSI_Labour_PresentsForSkilledBirthAttendanceInLabour,
    HSI_Labour_ReceivesCareForPostpartumPeriod,
)
from tlo.methods.malaria import (
    HSI_Malaria_complicated_treatment_adult,
    HSI_Malaria_complicated_treatment_child,
    HSI_Malaria_non_complicated_treatment_adult,
    HSI_Malaria_non_complicated_treatment_age0_5,
    HSI_Malaria_non_complicated_treatment_age5_15,
)
from tlo.methods.mockitis import HSI_Mockitis_PresentsForCareWithSevereSymptoms
from tlo.methods.oesophagealcancer import HSI_OesophagealCancer_Investigation_Following_Dysphagia

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------------------------------------
#
#    ** NON-EMERGENCY APPOINTMENTS **
#
# ---------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------
#    HSI_GenericFirstApptAtFacilityLevel1
# ---------------------------------------------------------------------------------------------------------

class HSI_GenericFirstApptAtFacilityLevel1(HSI_Event, IndividualScopeEventMixin):
    """
    This is a Health System Interaction Event.

    It is the generic appointment that describes the first interaction with the health system following the onset of
    acute generic symptoms.

    It occurs at Facility_Level = 1

    """

    def __init__(self, module, person_id):
        super().__init__(module, person_id=person_id)

        # Confirm that this appointment has been created by the HealthSeekingBehaviour module
        assert module is self.sim.modules['HealthSeekingBehaviour']

        # Work out if this is for a child or an adult
        is_child = self.sim.population.props.at[person_id, "age_years"] < 5

        # Get a blank footprint and then edit to define call on resources of this treatment event
        if is_child:
            the_appt_footprint = self.make_appt_footprint({'Under5OPD': 1})  # Child out-patient appointment
        else:
            the_appt_footprint = self.make_appt_footprint({'Over5OPD': 1})   # Adult out-patient appointment

        # Define the necessary information for an HSI
        self.TREATMENT_ID = 'GenericFirstApptAtFacilityLevel1'
        self.EXPECTED_APPT_FOOTPRINT = the_appt_footprint
        self.ACCEPTED_FACILITY_LEVEL = 1
        self.ALERT_OTHER_DISEASES = []

    def apply(self, person_id, squeeze_factor):
        logger.debug(key='message',
                     data=f'HSI_GenericFirstApptAtFacilityLevel1 for person'
                          f'{person_id}')

        df = self.sim.population.props
        symptoms = self.sim.modules['SymptomManager'].has_what(person_id=person_id)
        age = df.at[person_id, "age_years"]
        # NOTES: this section is repeated from the malaria.HSI_Malaria_rdt
        # requests for comsumables occur inside the HSI_treatment events
        # perhaps requests also need to occur here in case alternative treatments need to be scheduled

        # make sure query consumables has the generic hsi as the module requesting

        # diagnostic algorithm for child <5 yrs
        if age < 5:
            # ----------------------------------- CHILD <5 -----------------------------------
            # It's a child:
            logger.debug(key='message',
                         data='Run the ICMI algorithm for this child [dx_algorithm_child]')

            # If one of the symptoms is diarrhoea, then run the diarrhoea for a child routine:
            if 'diarrhoea' in symptoms:
                self.sim.modules['DxAlgorithmChild'].do_when_diarrhoea(person_id=person_id, hsi_event=self)

            # Run DxAlgorithmChild to get additional diagnoses:
            diagnosis = self.sim.modules["DxAlgorithmChild"].diagnose(
                person_id=person_id, hsi_event=self
            )

            if "Malaria" in self.sim.modules:

                # Treat / refer based on diagnosis
                if diagnosis == "severe_malaria":

                    # Make the relevant treatment HSI event:
                    treatment_hsi = HSI_Malaria_complicated_treatment_child(
                        self.sim.modules["Malaria"], person_id=person_id
                    )

                    # Schedule the HSI event:
                    self.sim.modules["HealthSystem"].schedule_hsi_event(
                        treatment_hsi, priority=1, topen=self.sim.date, tclose=None
                    )

                elif diagnosis == "clinical_malaria":

                    # Make the relevant treatment HSI event:
                    treatment_hsi = HSI_Malaria_non_complicated_treatment_age0_5(
                        self.sim.modules["Malaria"], person_id=person_id
                    )

                    # Schedule the HSI event:
                    self.sim.modules["HealthSystem"].schedule_hsi_event(
                        treatment_hsi, priority=1, topen=self.sim.date, tclose=None
                    )

        if (age >= 5) and (age < 15):
            # ----------------------------------- CHILD 5-14 -----------------------------------

            # Run DxAlgorithmChild to get (additional) diagnoses:
            diagnosis = self.sim.modules["DxAlgorithmChild"].diagnose(
                person_id=person_id, hsi_event=self
            )

            if "Malaria" in self.sim.modules:

                # Treat / refer based on diagnosis
                if diagnosis == "severe_malaria":

                    # Make the relevant treatment HSI event:
                    treatment_hsi = HSI_Malaria_complicated_treatment_child(
                        self.sim.modules["Malaria"], person_id=person_id
                    )

                    # Schedule the relevant HSI event:
                    self.sim.modules["HealthSystem"].schedule_hsi_event(
                        treatment_hsi, priority=1, topen=self.sim.date, tclose=None
                    )

                elif diagnosis == "clinical_malaria":

                    # Make the relevant treatment HSI event:
                    treatment_hsi = HSI_Malaria_non_complicated_treatment_age5_15(
                        self.sim.modules["Malaria"], person_id=person_id
                    )

                    # Schedule the relevant HSI event:
                    self.sim.modules["HealthSystem"].schedule_hsi_event(
                        treatment_hsi, priority=1, topen=self.sim.date, tclose=None
                    )

        if age >= 15:
            # ----------------------------------- ADULT -----------------------------------

            # If the symptoms include dysphagia, then begin investigation for Oesophageal Cancer:
            if 'dysphagia' in symptoms:
                hsi_event = HSI_OesophagealCancer_Investigation_Following_Dysphagia(
                    module=self.sim.modules['OesophagealCancer'],
                    person_id=person_id,
                )
                self.sim.modules['HealthSystem'].schedule_hsi_event(
                    hsi_event,
                    priority=0,
                    topen=self.sim.date,
                    tclose=None
                )

            if 'BladderCancer' in self.sim.modules:
                # If the symptoms include blood_urine, then begin investigation for Bladder Cancer:
                if 'blood_urine' in symptoms:
                    hsi_event = HSI_BladderCancer_Investigation_Following_Blood_Urine(
                        module=self.sim.modules['BladderCancer'],
                        person_id=person_id,
                    )
                    self.sim.modules['HealthSystem'].schedule_hsi_event(
                        hsi_event,
                        priority=0,
                        topen=self.sim.date,
                        tclose=None
                    )

                # If the symptoms include pelvic_pain, then begin investigation for Bladder Cancer:
                if 'pelvic_pain' in symptoms:
                    hsi_event = HSI_BladderCancer_Investigation_Following_pelvic_pain(
                        module=self.sim.modules['BladderCancer'],
                        person_id=person_id,
                    )
                    self.sim.modules['HealthSystem'].schedule_hsi_event(
                        hsi_event,
                        priority=0,
                        topen=self.sim.date,
                        tclose=None
                    )

            # ---- ROUTINE ASSESSEMENT FOR DEPRESSION ----
            if 'Depression' in self.sim.modules:
                depr = self.sim.modules['Depression']
                if (squeeze_factor == 0.0) and (self.module.rng.rand() <
                                                depr.parameters['pr_assessed_for_depression_in_generic_appt_level1']):
                    depr.do_when_suspected_depression(person_id=person_id, hsi_event=self)

            # DxAlgorithmAdult only exists in the malaria branch currently
            if "Malaria" in self.sim.modules:
                # Run DxAlgorithmAdult to get additional diagnoses:
                diagnosis = self.sim.modules["DxAlgorithmAdult"].diagnose(
                    person_id=person_id, hsi_event=self
                )

                if diagnosis == "severe_malaria":

                    # Make relevant treatment HSI event
                    treatment_hsi = HSI_Malaria_complicated_treatment_adult(
                        self.sim.modules["Malaria"], person_id=person_id
                    )

                    # Schedule relevant treatment HSI event
                    self.sim.modules["HealthSystem"].schedule_hsi_event(
                        treatment_hsi, priority=1, topen=self.sim.date, tclose=None
                    )

                elif diagnosis == "clinical_malaria":

                    # Make relevant treatment HSI event
                    treatment_hsi = HSI_Malaria_non_complicated_treatment_adult(
                        self.sim.modules["Malaria"], person_id=person_id
                    )

                    # Schedule relevant treatment HSI event
                    self.sim.modules["HealthSystem"].schedule_hsi_event(
                        treatment_hsi, priority=1, topen=self.sim.date, tclose=None
                    )

    def did_not_run(self):
        logger.debug(key='message',
                     data='HSI_GenericFirstApptAtFacilityLevel1: did not run')

# ---------------------------------------------------------------------------------------------------------
#    HSI_GenericFirstApptAtFacilityLevel0
# ---------------------------------------------------------------------------------------------------------


class HSI_GenericFirstApptAtFacilityLevel0(HSI_Event, IndividualScopeEventMixin):
    """
    This is a Health System Interaction Event.

    It is the generic appointment that describes the first interaction with the health system following the onset of
    acute generic symptoms.

    It occurs at Facility_Level = 0

    """

    def __init__(self, module, person_id):
        super().__init__(module, person_id=person_id)

        # Confirm that this appointment has been created by the HealthSeekingBehaviour module
        assert module is self.sim.modules['HealthSeekingBehaviour']

        # Define the necessary information for an HSI
        self.TREATMENT_ID = 'GenericFirstApptAtFacilityLevel0'
        self.EXPECTED_APPT_FOOTPRINT = self.make_appt_footprint({'ConWithDCSA': 1})
        self.ACCEPTED_FACILITY_LEVEL = 0
        self.ALERT_OTHER_DISEASES = []

    def apply(self, person_id, squeeze_factor):
        logger.debug(key='message',
                     data=f'This is HSI_GenericFirstApptAtFacilityLevel0 for person {person_id}')

    def did_not_run(self):
        logger.debug(key='message',
                     data='HSI_GenericFirstApptAtFacilityLevel0: did not run')

# ---------------------------------------------------------------------------------------------------------
#
#    ** EMERGENCY APPOINTMENTS **
#
# ---------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------
#    HSI_GenericEmergencyFirstApptAtFacilityLevel1
# ---------------------------------------------------------------------------------------------------------

class HSI_GenericEmergencyFirstApptAtFacilityLevel1(HSI_Event, IndividualScopeEventMixin):
    """
    This is a Health System Interaction Event.

    It is the generic appointment that describes the first interaction with the health system following the onset of
    acute generic symptoms.

    It occurs at Facility_Level = 1

    """

    def __init__(self, module, person_id):
        super().__init__(module, person_id=person_id)

        # Confirm that this appointment has been created by the HealthSeekingBehaviour module or Labour module
        assert module.name in ['HealthSeekingBehaviour', 'Labour']

        # Work out if this is for a child or an adult
        is_child = self.sim.population.props.at[person_id, 'age_years'] < 5

        # Get a blank footprint and then edit to define call on resources of this treatment event
        if is_child:
            the_appt_footprint = self.make_appt_footprint({'Under5OPD': 1})  # Child out-patient appointment
        else:
            the_appt_footprint = self.make_appt_footprint({'Over5OPD': 1})   # Adult out-patient appointment

        # Define the necessary information for an HSI
        self.TREATMENT_ID = 'GenericEmergencyFirstApptAtFacilityLevel1'
        self.EXPECTED_APPT_FOOTPRINT = the_appt_footprint
        self.ACCEPTED_FACILITY_LEVEL = 1
        self.ALERT_OTHER_DISEASES = []

    def apply(self, person_id, squeeze_factor):
        logger.debug(key='message',
                     data=f'This is HSI_GenericEmergencyFirstApptAtFacilityLevel1 for person {person_id}')

        df = self.sim.population.props
        symptoms = self.sim.modules['SymptomManager'].has_what(person_id)
        age = df.at[person_id, "age_years"]

        health_system = self.sim.modules["HealthSystem"]

        if 'Labour' in self.sim.modules:
            mni = self.sim.modules['Labour'].mother_and_newborn_info
            labour_list = self.sim.modules['Labour'].women_in_labour

            # -----  COMPLICATION DURING BIRTH  -----
            if person_id in labour_list:
                if df.at[person_id, 'la_currently_in_labour'] & (mni[person_id]['sought_care_for_complication']) \
                        & (mni[person_id]['sought_care_labour_phase'] == 'intrapartum'):
                    event = HSI_Labour_PresentsForSkilledBirthAttendanceInLabour(
                        module=self.sim.modules['Labour'], person_id=person_id,
                        facility_level_of_this_hsi=int(self.module.rng.choice([1, 2])))
                    health_system.schedule_hsi_event(event, priority=1, topen=self.sim.date)

            # -----  COMPLICATION AFTER BIRTH  -----
                if df.at[person_id, 'la_currently_in_labour'] & (mni[person_id]['sought_care_for_complication']) \
                        & (mni[person_id]['sought_care_labour_phase'] == 'postpartum'):
                    event = HSI_Labour_ReceivesCareForPostpartumPeriod(
                        module=self.sim.modules['Labour'], person_id=person_id,
                        facility_level_of_this_hsi=int(self.module.rng.choice([1, 2])))
                    health_system.schedule_hsi_event(event, priority=1, topen=self.sim.date)

        # -----  SUSPECTED DEPRESSION  -----
        if "Depression" in self.sim.modules:

            if 'Injuries_From_Self_Harm' in symptoms:
                self.sim.modules['Depression'].do_when_suspected_depression(person_id=person_id, hsi_event=self)
                # TODO: Trigger surgical care for injuries.

        # ------ MALARIA ------
        if "Malaria" in self.sim.modules:

            # Quick diagnosis algorithm - just perfectly recognises the symptoms of severe malaria
            sev_set = {"acidosis",
                       "coma_convulsions",
                       "renal_failure",
                       "shock",
                       "jaundice",
                       "anaemia"
                       }

            # if person's symptoms are on severe malaria list then treat
            any_symptoms_indicative_of_severe_malaria = len(sev_set.intersection(symptoms)) > 0

            # Run DxAlgorithmAdult to log consumable and confirm malaria parasitaemia:
            diagnosis = self.sim.modules["DxAlgorithmAdult"].diagnose(
                person_id=person_id, hsi_event=self
            )

            # if any symptoms indicative of malaria and they have parasitaemia (would return a positive rdt)
            if any_symptoms_indicative_of_severe_malaria and (diagnosis in ["severe_malaria", "clinical_malaria"]):
                # Launch the HSI for treatment for Malaria - choosing the right one for adults/children
                if age < 5.0:
                    health_system.schedule_hsi_event(
                        hsi_event=HSI_Malaria_complicated_treatment_child(
                            self.sim.modules["Malaria"], person_id=person_id
                        ),
                        priority=0,
                        topen=self.sim.date,
                    )
                else:
                    health_system.schedule_hsi_event(
                        hsi_event=HSI_Malaria_complicated_treatment_adult(
                            self.sim.modules["Malaria"], person_id=person_id
                        ),
                        priority=0,
                        topen=self.sim.date,
                    )
        # else:
            # treat symptoms acidosis, coma_convulsions, renal_failure, shock, jaundice, anaemia

        # -----  EXAMPLES FOR MOCKITIS AND CHRONIC SYNDROME  -----
        if 'craving_sandwiches' in symptoms:
            event = HSI_ChronicSyndrome_SeeksEmergencyCareAndGetsTreatment(
                module=self.sim.modules['ChronicSyndrome'],
                person_id=person_id
            )
            health_system.schedule_hsi_event(event, priority=1, topen=self.sim.date)

        if 'extreme_pain_in_the_nose' in symptoms:
            event = HSI_Mockitis_PresentsForCareWithSevereSymptoms(
                module=self.sim.modules['Mockitis'],
                person_id=person_id
            )
            health_system.schedule_hsi_event(event, priority=1, topen=self.sim.date)

    def did_not_run(self):
        logger.debug(key='message',
                     data='HSI_GenericEmergencyFirstApptAtFacilityLevel1: did not run')

        return False  # Labour debugging
        # pass

    def not_available(self):
        pass