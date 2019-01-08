"""
General utility functions for TLO analysis
"""
import logging
from ast import literal_eval

import pandas as pd

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def parse_line(line):
    """
    Parses a single line of logged output. It has the format:
    INFO|<logger name>|<simulation date>|<log key>|<python object>

    It returns the dictionary:
        { 'logger': <logger name>,
          'sim_date': <simulation date>,
          'key': <the key of this log entry>,
          'object': <the logged python object>
        }

    :param line: the full line from log file
    :return: a dictionary with parsed line
    """
    parts = line.split('|')
    logger.debug('%s', line)
    info = {
        'logger': parts[1],
        'sim_date': parts[2],
        'key': parts[3],
        'object': literal_eval(parts[4])
    }
    logger.debug('%s', info)
    return info


def parse_output(filepath):
    """
    Parses logged output from a TLO run and create Pandas dataframes for analysis.

    The input lines follow the format:
    INFO|<logger name>|<simulation datestamp>|<log key>|<python list or dictionary>

    e.g.

    INFO|tlo.methods.demography|2010-11-02 23:00:59.111968|on_birth|{'mother': 17, 'child': 50}
    INFO|tlo.methods.demography|2011-01-01 00:00:00|population|{'total': 51, 'male': 21, 'female': 30}
    INFO|tlo.methods.demography|2011-01-01 00:00:00|age_range_m|[5, 4, 1, 1, 1, 2, 1, 2, 2, 1, 1, 0]
    INFO|tlo.methods.demography|2011-01-01 00:00:00|age_range_f|[4, 7, 5, 1, 5, 1, 2, 0, 1, 2, 0, 1]

    The dictionary returned has the format:
    {
        <logger 1 name>: {
                           <log key 1>: <pandas dataframe>,
                           <log key 2>: <pandas dataframe>,
                           <log key 3>: <pandas dataframe>
                         },

        <logger 2 name>: {
                           <log key 4>: <pandas dataframe>,
                           <log key 5>: <pandas dataframe>,
                           <log key 6>: <pandas dataframe>
                         },
        ...
    }

    :param filepath: the full filepath to logged output file
    :return: a dictionary holding logged data as Python objects
    """
    o = dict()

    # read logging lines from the file
    with open(filepath) as log_file:
        # for each logged line
        for line in log_file:
            # we only parse 'INFO' lines
            if line.startswith('INFO'):
                i = parse_line(line.strip())
                # add a dictionary for the logger name, if required
                if i['logger'] not in o:
                    o[i['logger']] = dict()
                # add a dataframe for the name/key of this log entry, if required
                if i['key'] not in o[i['logger']]:
                    # if the logged data is a list, it doesn't have column names
                    if isinstance(i['object'], list):
                        # create column names for each entry in the list
                        columns = ['col_%d' % x for x in range(0, len(i['object']))]
                    else:
                        # create column names from the keys of the dictionary
                        columns = list(i['object'].keys())
                    columns.insert(0, 'date')
                    o[i['logger']][i['key']] = pd.DataFrame(columns=columns)

                df = o[i['logger']][i['key']]

                # create a new row to append to the dataframe, add the simulation date
                if isinstance(i['object'], dict):
                    row = i['object']
                    row['date'] = i['sim_date']
                elif isinstance(i['object'], list):
                    if len(df.columns) - 1 != len(i['object']):
                        logger.warning('List to dataframe %s, number of columns do not match', i['key'])
                    # add list to columns (skip first column, which is date)
                    row = dict(zip(df.columns[1:], i['object']))
                    row['date'] = i['sim_date']
                else:
                    raise ValueError('Cannot handle log object of type %s' % type(i['object']))
                # append the new row to the dataframe for this logger & log name
                o[i['logger']][i['key']] = df.append(row, ignore_index=True)
    return o
