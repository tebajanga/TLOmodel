import json
import os
from pathlib import Path

import pandas as pd
import pytest

from tlo import Date, Simulation, logging
from tlo.methods import demography, enhanced_lifestyle

start_date = Date(2010, 1, 1)
popsize = 500


@pytest.fixture(scope='function')
def basic_configuration(tmpdir):
    """Setup basic file handler configuration"""
    # tlo module config
    file_name = tmpdir.join('test.log')
    file_handler = logging.set_output_file(file_name)

    yield file_handler, file_name

    file_handler.close()


@pytest.fixture(scope='function')
def simulation_configuration(tmpdir):
    resourcefilepath = Path(os.path.dirname(__file__)) / '../resources'

    sim = Simulation(start_date=start_date, log_config={'filename': 'log', 'directory': tmpdir})
    sim.register(demography.Demography(resourcefilepath=resourcefilepath),
                 enhanced_lifestyle.Lifestyle(resourcefilepath=resourcefilepath))

    yield sim.output_file, sim.log_filepath

    sim.output_file.close()


def read_file(file_handler, file_name):
    """
    Reads file and returns the lines
    :param file_handler: filehandler (to flush) though might be a bit unnecessary
    :param file_name: path to file
    :return: list of lines
    """
    file_handler.flush()
    with open(file_name) as handle:
        lines = handle.readlines()
    return lines


def log_message(message_level, logger_level, message, logger_name='tlo.test.logger', structured_logging=False):
    """
    Sets up logger level, and writes message at the message level

    :param message_level: level that the message will be added as
    :param logger_level: level that the logger is set to
    :param message: message to be written to log
    :param structured_logging:

    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(logger_level)

    if structured_logging:
        if message_level == 'logging.DEBUG':
            logger.debug(key='structured', data=message)
        elif message_level == 'logging.INFO':
            logger.info(key='structure', data=message)
        elif message_level == 'logging.WARNING':
            logger.warning(key='structured', data=message)
        elif message_level == 'logging.CRITICAL':
            logger.critical(key='structured', data=message)
    else:
        if message_level == 'logging.DEBUG':
            logger.debug(message)
        elif message_level == 'logging.INFO':
            logger.info(message)
        elif message_level == 'logging.WARNING':
            logger.warning(message)
        elif message_level == 'logging.CRITICAL':
            logger.critical(message)


class TestStdLibLogging:
    @pytest.mark.parametrize("message_level", ["logging.DEBUG", "logging.INFO", "logging.WARNING", "logging.CRITICAL"])
    def test_messages_at_same_level(self, basic_configuration, message_level):
        # given that messages are at the same level as the logger
        logger_level = eval(message_level)
        log_message(message_level, logger_level, "test message")
        lines = read_file(*basic_configuration)

        # messages should be written to log
        assert [f'{message_level.strip("logging.")}|tlo.test.logger|test message\n'] == lines

    @pytest.mark.parametrize("message_level", ["logging.DEBUG", "logging.INFO", "logging.WARNING", "logging.CRITICAL"])
    def test_messages_at_higher_level(self, basic_configuration, message_level):
        # given that messages are at a higher level as the logger
        logging_level = eval(message_level) - 1
        log_message(message_level, logging_level, "test message")
        lines = read_file(*basic_configuration)

        # messages should be written to log
        assert [f'{message_level.strip("logging.")}|tlo.test.logger|test message\n'] == lines

    @pytest.mark.parametrize("message_level", ["logging.DEBUG", "logging.INFO", "logging.WARNING", "logging.CRITICAL"])
    def test_messages_at_lower_level(self, basic_configuration, message_level):
        # given that messages are at a lower level as the logger
        logging_level = eval(message_level) + 1
        log_message(message_level, logging_level, "test message")
        lines = read_file(*basic_configuration)

        # messages should not be written to log
        assert [] == lines

    @pytest.mark.parametrize("message_level", ["logging.DEBUG", "logging.INFO", "logging.WARNING", "logging.CRITICAL"])
    def test_disable(self, basic_configuration, message_level):
        # given that messages are at a higher level as the logger BUT the logger is disabled at critical
        logging_level = eval(message_level) - 1
        logging.disable(logging.CRITICAL)
        log_message(message_level, logging_level, "test message")
        lines = read_file(*basic_configuration)

        # messages should not be written to log
        assert [] == lines

        # enable logging again
        logging.disable(0)


class TestStructuredLogging:
    @pytest.mark.parametrize("message_level", ["logging.DEBUG", "logging.INFO", "logging.WARNING", "logging.CRITICAL"])
    def test_messages_same_level(self, simulation_configuration, message_level):
        # given that messages are at the same level as the logger
        logger_level = eval(message_level)
        message = {"message": pd.Series([12.5])[0]}
        file_handler, file_path = simulation_configuration
        log_message(message_level, logger_level, message, structured_logging=True)

        lines = read_file(file_handler, file_path)
        header_json = json.loads(lines[5])
        data_json = json.loads(lines[6])

        # message should be written to log
        assert len(lines) == 7
        assert header_json['level'] == message_level.lstrip("logging.")
        assert 'message' in header_json['columns']
        assert header_json['columns']['message'] == 'float64'
        assert data_json['values'] == [12.5]

    @pytest.mark.parametrize("message_level", ["logging.DEBUG", "logging.INFO", "logging.WARNING", "logging.CRITICAL"])
    def test_messages_higher_level(self, simulation_configuration, message_level):
        # given that messages are a higher level than the logger
        logger_level = eval(message_level) - 1
        message = {"message": pd.Series([12.5])[0]}
        file_handler, file_path = simulation_configuration
        log_message(message_level, logger_level, message, structured_logging=True)

        lines = read_file(file_handler, file_path)
        header_json = json.loads(lines[5])
        data_json = json.loads(lines[6])

        # message should be written to log
        assert len(lines) == 7
        assert header_json['level'] == message_level.lstrip("logging.")
        assert 'message' in header_json['columns']
        assert header_json['columns']['message'] == 'float64'
        assert data_json['values'] == [12.5]

    @pytest.mark.parametrize("message_level", ["logging.DEBUG", "logging.INFO", "logging.WARNING", "logging.CRITICAL"])
    def test_messages_lower_level(self, simulation_configuration, message_level):
        # given that messages are at a lower level than logger
        logger_level = eval(message_level) + 1
        message = {"message": pd.Series([12.5])[0]}
        file_handler, file_path = simulation_configuration
        log_message(message_level, logger_level, message, structured_logging=True)

        lines = read_file(file_handler, file_path)

        # only simulation info messages should be written to log
        assert len(lines) == 5


class TestConvertLogData:
    def setup(self):
        self.expected_output = {'item_1': 1, 'item_2': 2}
        self.logger = logging.getLogger('tlo.test.logger')

    @pytest.mark.parametrize("iterable_data", [[1, 2], {1, 2}, (1, 2)])
    def test_convert_iterable_to_dict(self, iterable_data):
        output = self.logger._get_data_as_dict(iterable_data)
        assert self.expected_output == output

    def test_convert_df_to_dict(self):
        df = pd.DataFrame({'item_1': [1], 'item_2': [2]})
        output = self.logger._get_data_as_dict(df)

        assert self.expected_output == output

    def test_string_to_dict(self):
        output = self.logger._get_data_as_dict("strings")
        assert {'message': 'strings'} == output


def test_mixed_logging():
    """Logging with both oldstyle and structured logging should raise an error"""
    logger = logging.getLogger('tlo.test.logger')
    logger.setLevel(logging.INFO)
    with pytest.raises(ValueError):
        logger.info("stdlib method")
        logger.info(key="structured", data={"key": 10})