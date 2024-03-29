"""
This module provides a command line tool to help manage string transformations
through a yaml config file and some understanding of regular expressions.

There are 2 ways the string transformations will be handled:

1. YAML configuration with an order of precedence:

    1. environment variable (SARLAC_CONFIG) set to configuration file location
    2. home directory with a .sarlac.yaml file
    3. /usr/local/etc/sarlac.yaml

2. CLI args for single ad-hoc transformations

Argument lists and stdin are both acceptable ways to input the string(s) to be
transformed.
"""

from pathlib import Path
import os
import re
import yaml
import click
from python_sarlac.__init__ import __version__


def _print_help(ctx, param, value):  # pylint: disable=unused-argument
    '''click help output overridden to allow for help as the default (no
    argument) option on the command line'''
    if value is False:
        return
    click.echo(ctx.get_help())
    ctx.exit()


@click.command()
@click.option('-h', '--help', is_flag=True, expose_value=False, is_eager=False, \
    callback=_print_help, help='Print help message.')
@click.option('-m', '--match', 'match_pattern', help='Ad-hoc match regex.')
@click.option('-r', '--replace', 'replace_pattern', help='Regex replacement.')
@click.version_option(version=__version__)
@click.argument('cli_args', nargs=-1)
@click.pass_context
def main(ctx, match_pattern, replace_pattern, cli_args):
    '''A tool to help manage string transformations through a yaml config file
    and some understanding of regular expressions.'''
    if not match_pattern and not replace_pattern and not cli_args:
        _print_help(ctx, None, value=True)
    sub_rules = _generate_cli_adhoc_rules(match_pattern, replace_pattern)
    config = _get_config_filename()
    if not sub_rules:
        sub_rules = _parse_config(config)
    _process_input(sub_rules, cli_args)
    ctx.exit()


def _generate_cli_adhoc_rules(match_pattern, replace_pattern):
    '''helper method for processing ad-hoc cli match/replace requests'''
    sub_rules = None
    if match_pattern and replace_pattern:
        sub_rules = {
            'substitutions': [
                {'match': re.compile(match_pattern), 'replace': replace_pattern}
            ]
        }
    return sub_rules


def _get_config_filename():
    ''' config file order of precedence is:
    1. environment variable SARLAC_CONFIG
    2. $HOME/.sarlac.yaml
    3. /usr/local/etc/sarlac.yaml
    '''
    envfile = os.getenv('SARLAC_CONFIG')
    homefile = Path(str(Path.home()) + "/.sarlac.yaml")
    globalfile = '/usr/local/etc/sarlac.yaml'
    configfile = globalfile
    if homefile.is_file():
        configfile = str(homefile)
    if envfile:
        configfile = envfile
    return configfile


def _process_input(sub_rules, cli_args):
    # process piped stdin input
    if cli_args[-1] == "-":
        with click.open_file('-', mode='r') as infile:
            for instr in infile:
                out = _run_subs(sub_rules, instr.rstrip())
                click.echo(out)
    else:
        for instr in cli_args:
            out = _run_subs(sub_rules, instr)
            click.echo(out)


def _run_subs(sub_rules, instr):
    '''take substitution rules tuple {match, replace}, and see if input matches.
    If match, then replace.
    '''
    for rule in sub_rules['substitutions']:
        if rule['match'].match(instr):
            return re.sub(rule['match'], rule['replace'], instr)
    return None


def _parse_config(configfile):
    '''parse config file and return it as a set of rules that will be used in
    the match/replace logic'''
    with open(configfile, 'r') as infile:
        config = yaml.safe_load(infile)
    for rule in config['substitutions']:
        rule['match'] = re.compile(rule['match'])
    return config


if __name__ == '__main__':
    main()  # pylint: disable=no-value-for-parameter
