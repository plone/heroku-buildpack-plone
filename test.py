#!/usr/bin/env bash
"""A script used for verifying if Plone was installed correctly.

Run like this:
bin/instance run test.py
"""

import sys
import Products.CMFPlone
if Products.CMFPlone:
    sys.exit(0)
else:
    sys.exit(1)
