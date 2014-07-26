#!/usr/bin/env bash
"""Since Plone cannot read env vars or command line parameters we have to
go through the zope.conf and searc/replace values. Bad Plone!"""
import os

DIR = '/app/'
zope_conf_orig = DIR + 'parts/instance/etc/zope.conf'
zope_conf_new = DIR + 'parts/instance/etc/zope.conf.new'

with open(zope_conf_new, 'wt') as fout:
    with open(zope_conf_orig, 'rt') as fin:
        for line in fin:
            fout.write(
                line.
                replace('address 8080', 'address {}'.format(os.environ['PORT'])).
                replace('PG_HOST', os.environ['DATABASE_URL'].split('@')[1].split(':')[0]).
                replace('PG_DBNAME', os.environ['DATABASE_URL'].split('/')[-1]).
                replace('PG_USER', os.environ['DATABASE_URL'].split('//')[1].split(':')[0]).
                replace('PG_PASS', os.environ['DATABASE_URL'].split('//')[1].split(':')[1].split('@')[0])
            )

os.system('mv {} {}'.format(zope_conf_new, zope_conf_orig))
