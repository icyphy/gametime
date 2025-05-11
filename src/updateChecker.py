#!/usr/bin/env python

"""Exposes functions to determine if updates to GameTime are available."""

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""


import json
import urllib2
import socket

from setuptools.dist import pkg_resources
from pkg_resources import parse_version

from defaults import config, logger


def getLatestVersionInfo():
    """Obtains information about the latest available version of GameTime.

    Returns:
        Dictionary that contains information about the latest available
        version of GameTime. If the dictionary is empty, then no such
        information could be obtained.

        If, however, the dictionary is not empty, it has at least
        the two following keys:
            - `version`, whose corresponding value is the number of
            the latest version of GameTime, and
            - `info_url`, whose corresponding value is the URL of
            the webpage that provides more information about
            the latest version of GameTime.
    """
    try:
        logger.info("Retrieving data about the latest version of GameTime...")
        urlHandler = urllib2.urlopen(config.LATEST_VERSION_INFO_URL, timeout=3)

        latestVersionInfo = json.load(urlHandler)
        logger.info("Data retrieved.")

        if not latestVersionInfo.has_key("version"):
            raise ValueError("Data retrieved does not have the number of "
                             "the latest version of GameTime.")
        elif not latestVersionInfo.has_key("info_url"):
            raise ValueError("Data retrieved does not have URL of the webpage "
                             "that provides more information about "
                             "the latest version of GameTime.")
        return latestVersionInfo
    except urllib2.URLError as e:
        errorReason = e.reason
        # Special case
        if len(e.args) > 0 and e.args[0].errno == 11001:
            errorReason = "No Internet connection detected."
        logger.warning("Unable to retrieve data about the latest "
                       "version of GameTime: %s" % errorReason)
        return {}
    except socket.timeout as e:
        logger.warning("Unable to retrieve data about the latest "
                       "version of GameTime: The attempt to connect with "
                       "the URL that provides this data timed out.")
        return {}
    except ValueError as e:
        logger.warning("Data retrieved was in an incorrect format: %s" % e)
        return {}

def isUpdateAvailable():
    """Checks if an update to the current version of GameTime is available.

    Returns:
        Tuple of two elements: The first element is `True` if an update
        is available and `False` otherwise. The second element is a
        dictionary that contains information about the latest version of
        GameTime that is available. If the dictionary is empty, then
        no information about the latest available version of GameTime
        could be obtained.

        If non-empty, the dictionary has at least the two following keys:
            - `version`, whose corresponding value is the number of
            the newer version of GameTime, and
            - `info_url`, whose corresponding value is the URL of
            the webpage that provides more information about
            the newer version of GameTime.
    """
    latestVersionInfo = getLatestVersionInfo()
    if latestVersionInfo:
        return ((parse_version(latestVersionInfo["version"]) >
                 parse_version(config.VERSION)),
                latestVersionInfo)
    return (False, {})
