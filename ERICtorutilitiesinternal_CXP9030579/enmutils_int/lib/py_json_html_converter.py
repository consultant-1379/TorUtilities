# ********************************************************************
# Name    : Python JSON HTML Converter
# Summary : Functional tool to convert between JSON, HTML, DICT
#           object. Used primarily by the update_enmutils_rpm tool,
#           convert the Nexus stored json artifacts to python objects
#           for functionality such as workload diff, contains wrapper
#           functionality to convert between JSON, HTML and DICT
#           objects.
# ********************************************************************


import imp
import json
import sys
from os import getenv

from json2html import json2html


def _get_table_styling():
    """
    Returns a styling for the html table

    :returns: Styling for the table
    :rtype: str
    """
    return '<style>table, th, td {0}</style>'.format(
        '{border: 1px solid black; border-collapse: collapse;padding: 5px; background-color: #ffffff;}')


def _get_caption(version):
    """
    Returns a caption for the html table

    :param version: Version of the rpm
    :type version: str
    :returns: caption for the html table
    :rtype: str
    """
    return '<caption><h2>WORKLOAD PROFILES - version: {0}</h2></caption>'.format(version)


def convert_from_dict_to_json(dict_to_convert):
    """
    Converts from a normal dictionary to json

    :param dict_to_convert: Dictionary to be converted to json
    :type dict_to_convert: dict
    :returns: converted json
    :rtype: json
    """
    return json.dumps(dict_to_convert)


def convert_from_json_to_dict(json_to_convert):
    """
    Converts from json to a normal dictionary

    :param json_to_convert: Json to be converted to a normal dictionary
    :type json_to_convert: json
    :returns: converted dict
    :rtype: dict
    """
    return json.loads(json_to_convert)


def convert_json_to_html_table(json_to_convert):
    """
    Converts from json to a a html table

    :param json_to_convert: Json to be converted to a html table
    :type json_to_convert: json
    :returns: converted html table
    :rtype: str
    """
    generated_table = json2html.convert(json=json_to_convert)
    return generated_table


def get_html(version, dict_to_convert):
    """
    Get a html page with a caption, styling and html table

    :param version: Version of the rpm
    :type version: str
    :param dict_to_convert: dict to be converted
    :type dict_to_convert: dict
    :returns: Simple html page
    :rtype: str
    """
    j = convert_from_dict_to_json(dict_to_convert)
    table = convert_json_to_html_table(j)
    return _get_caption(version) + _get_table_styling() + table


def _get_env_variable(var_to_pull):
    """Get value of specified variable from environment.
    Can be used in Jenkins when variables are exported"""
    return getenv(var_to_pull, 'not_specified')


def create_python_module_from_file(networks_file):
    """
    Create and compile a python module from a python file

    @type networks_file: string
    @param networks_file: The absolute path to the file that contains networks dict
    @rtype: module
    """

    d = imp.new_module('networks')
    d.__file__ = networks_file
    try:
        with open(networks_file) as config_file:
            exec(compile(config_file.read(), networks_file, 'exec'), d.__dict__)
    except IOError as e:
        print 'Unable to load file (%s)' % e.strerror
    return d


def get_json_from_a_file(file_path):
    with open(file_path) as f:
        return f.readlines()


def _print_help():
    print """
    Supported options
     --json    Convert to json
     --html    Convert to html
     --version=<version-that-will-be-listed-at-the-top-of-the-html-page.Usually-a-ref-to-rpm-version>
     --path-to-networks=<absolute-path-to-python-file-holding-'networks'-dictionary-to-be-converted>
     --path-to-save=<absolute-path-to-new-file-after-conversion>

     Example:
       py_json_html_converter.py --json --version=4.34.32 --path-to-save=/tmp/workload_profiles_ver_4.34.32.json
       py_json_html_converter.py --html --version=4.34.32 --path-to-save=/tmp/workload_profiles_ver_4.34.32.html

       Above commands don't specify  '--path-to-networks' option.
       In this case, it will default to: enmutils_int.lib.nrm_default_configurations.profile_values
     """


def cli():
    if '--help' in sys.argv:
        _print_help()

    # get networks dict, either from provided or default location
    path_to_networks = ''.join([p.split('=')[1] for p in sys.argv if p.startswith('--path-to-networks=')])
    if not path_to_networks:
        from enmutils_int.lib.nrm_default_configurations.profile_values import networks
    else:
        networks = create_python_module_from_file(path_to_networks).networks

    # get version, either provided or from environment
    version = ''.join(
        [v.split('=')[1] for v in sys.argv if v.startswith('--version=')]) or _get_env_variable('version')

    extension = ''
    if '--html' in sys.argv:
        extension = 'html'
    elif '--json' in sys.argv:
        extension = 'json'

    if extension:
        # save converted into a new file
        file_name = 'workload_profiles_ver_{0}.{1}'.format(version, extension)
        path_to_save = ''.join(
            [p.split('=')[1] for p in sys.argv if p.startswith('--path-to-save=')]) or file_name

        with open(path_to_save, 'wb') as f:
            if extension == 'html':
                f.write(get_html(version, networks))
            else:
                f.write(convert_from_dict_to_json(networks))


if __name__ == '__main__':  # pragma: no cover
    cli()
