'''
Created on Dec 12, 2017

@author: dvanaken
'''

import re

from .base import BaseParser
from website.models import DBMSCatalog
from website.types import DBMSType, KnobUnitType
from website.utils import ConversionUtil


class PostgresParser(BaseParser):

    POSTGRES_BYTES_SYSTEM = [
        (1024 ** 5, 'PB'),
        (1024 ** 4, 'TB'),
        (1024 ** 3, 'GB'),
        (1024 ** 2, 'MB'),
        (1024 ** 1, 'kB'),
        (1024 ** 0, 'B'),
    ]

    POSTGRES_TIME_SYSTEM = [
        (1000 * 60 * 60 * 24, 'd'),
        (1000 * 60 * 60, 'h'),
        (1000 * 60, 'min'),
        (1, 'ms'),
        (1000, 's'),
    ]

    POSTGRES_BASE_PARAMS = {
        'global.data_directory': None,
        'global.hba_file': None,
        'global.ident_file': None,
        'global.external_pid_file': None,
        'global.listen_addresses': None,
        'global.port': None,
        'global.max_connections': None,
        'global.unix_socket_directories': None,
        'global.log_line_prefix': '%t [%p-%l] %q%u@%d ',
        'global.track_counts': 'on',
        'global.track_io_timing': 'on',
        'global.autovacuum': 'on',
        'global.default_text_search_config': 'pg_catalog.english',
    }

    @property
    def base_configuration_settings(self):
        return dict(self.POSTGRES_BASE_PARAMS)

    @property
    def configuration_filename(self):
        return 'postgresql.conf'

    @property
    def transactions_counter(self):
        return 'pg_stat_database.xact_commit'

    def convert_integer(self, int_value, param_info):
        converted = None
        try:
            converted = super(PostgresParser, self).convert_integer(
                int_value, param_info)
        except ValueError:
            if param_info.unit == KnobUnitType.BYTES:
                converted = ConversionUtil.get_raw_size(
                    int_value, system=self.POSTGRES_BYTES_SYSTEM)
            elif param_info.unit == KnobUnitType.MILLISECONDS:
                converted = ConversionUtil.get_raw_size(
                    int_value, system=self.POSTGRES_TIME_SYSTEM)
            else:
                raise Exception(
                    'Unknown unit type: {}'.format(param_info.unit))
        if converted is None:
            raise Exception('Invalid integer format for param {} ({})'.format(
                param_info.name, int_value))
        return converted

    def format_integer(self, int_value, param_info):
        if param_info.unit != KnobUnitType.OTHER and int_value > 0:
            if param_info.unit == KnobUnitType.BYTES:
                int_value = ConversionUtil.get_human_readable(
                    int_value, PostgresParser.POSTGRES_BYTES_SYSTEM)
            elif param_info.unit == KnobUnitType.MILLISECONDS:
                int_value = ConversionUtil.get_human_readable(
                    int_value, PostgresParser.POSTGRES_TIME_SYSTEM)
            else:
                raise Exception(
                    'Invalid knob unit type: {}'.format(param_info.unit))
        else:
            int_value = super(PostgresParser, self).format_integer(int_value, param_info)
        return int_value

    def parse_version_string(self, version_string):
        dbms_version = version_string.split(',')[0]
        return re.search("\d+\.\d+(?=\.\d+)", dbms_version).group(0)


class Postgres96Parser(PostgresParser):

    def __init__(self):
        dbms = DBMSCatalog.objects.get(
            type=DBMSType.POSTGRES, version='9.6')
        super(Postgres96Parser, self).__init__(dbms.pk)
