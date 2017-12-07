#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

from os import urandom, environ
from os.path import realpath

from flask import Flask, request, render_template
from flask_menu import Menu, current_menu, register_menu
from flask_babel import Babel, lazy_gettext as _

from sqlsoup import SQLSoup

from logging import getLogger, NullHandler


__all__ = ['site', 'db']


log = getLogger(__name__)
log.addHandler(NullHandler)

site = Flask(__name__)
site.secret_key = urandom(16)

# Default configuration options.
site.config.from_mapping({
    'HOST': '::',
    'PORT': 5000,
    'DEBUG': False,
    'BABEL_DEFAULT_LOCALE': 'cs',
    'SQLSOUP_DATABASE_URI': 'postgresql://vlna:vlna@localhost/vlna',
    'MAX_CONTENT_LENGTH': 32 * 1024 * 1024,
    'DATA_PATH': 'data',
})

if 'VLNA_SETTINGS' in environ:
    # Load rest from a configuration file specified in the environment.
    # Set by the --config option when run using the bin/vlna.
    site.config.from_envvar('VLNA_SETTINGS')

# Make sure we use absolute path to the data directory.
site.config['DATA_PATH'] = realpath(site.config['DATA_PATH'])

# Initialize the automatic menu generation.
menu = Menu(site)

# Initialize the l18n module.
babel = Babel(site)


@site.template_global('get_locale')
@babel.localeselector
def get_locale():
    """
    Return currently selected locale.
    """

    if 'lang' in request.args:
        return request.args['lang']

    locale = site.config['BABEL_DEFAULT_LOCALE']
    return request.cookies.get('lang', locale)


@site.after_request
def insert_lang_cookie(response):
    """
    Make user locale selection persistent using a cookie.
    """

    if 'lang' in request.args:
        response.set_cookie('lang', request.args['lang'])

    return response


# Use SQLSoup for database access.
db = SQLSoup(site.config['SQLSOUP_DATABASE_URI'])


@site.teardown_request
def teardown_request(exn=None):
    """
    Rolls back current session at the end of every request.
    """

    try:
        db.session.rollback()
    except Exception as subexn:
        # Teardown callbacks may not raise exceptions.
        log.exception(subexn)


@site.context_processor
def inject_env():
    """
    Injects site configuration and other globals to templates.
    """

    return dict(site.config, current_menu=current_menu)


@site.route('/')
@register_menu(site, 'sub', _('Subscriptions'))
def home():
    return render_template('sub.html')


@site.route('/trn/')
@register_menu(site, 'trn', _('Transmissions'))
def sending():
    return render_template('trn.html')


# vim:set sw=4 ts=4 et:
