# -*- coding: utf-8 -*-
"""
$Id$

Copyright 2010 Lars Kruse <devel@sumpfralle.de>

This file is part of PyCAM.

PyCAM is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

PyCAM is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with PyCAM.  If not, see <http://www.gnu.org/licenses/>.
"""

from pycam.Importers.SVGImporter import convert_eps2dxf
import pycam.Importers.DXFImporter
from pycam.Utils import check_uri_exists, retrieve_uri
import tempfile
import os

log = pycam.Utils.log.get_logger()


def import_model(filename, program_locations=None, unit="mm", callback=None):
    if not check_uri_exists(filename):
        log.error("PSImporter: file (%s) does not exist" % filename)
        return None
    if not os.path.isfile(filename):
        # non-local file - write it to a temporary file first
        local_file = False
        uri = filename
        ps_file_handle, ps_file_name = tempfile.mkstemp(suffix=".ps")
        os.close(ps_file_handle)
        log.debug("Retrieving PS file for local access: %s -> %s" % \
                (uri, ps_file_name))
        if not retrieve_uri(uri, ps_file_name, callback=callback):
            log.error("PSImporter: Failed to retrieve the PS model file: " + \
                    "%s -> %s" % (uri, ps_file_name))
        filename = ps_file_name
    else:
        local_file = True

    if program_locations and "pstoedit" in program_locations:
        pstoedit_path = program_locations["pstoedit"]
    else:
        pstoedit_path = None

    def remove_temp_file(filename):
        if os.path.isfile(filename):
            try:
                os.remove(filename)
            except OSError, err_msg:
                log.warn("PSImporter: failed to remove temporary file " \
                        + "(%s): %s" % (filename, err_msg))

    # convert eps to dxf via pstoedit
    dxf_file_handle, dxf_file_name = tempfile.mkstemp(suffix=".dxf")
    os.close(dxf_file_handle)
    success = convert_eps2dxf(filename, dxf_file_name, unit=unit,
            location=pstoedit_path)
    if not local_file:
        remove_temp_file(ps_file_name)
    if not success:
        result = None
    elif callback and callback():
        log.warn("PSImporter: load model operation cancelled")
        result = None
    else:
        log.info("Successfully converted PS file to DXF file")
        # pstoedit uses "inch" -> force a scale operation
        result = pycam.Importers.DXFImporter.import_model(dxf_file_name,
                unit=unit, callback=callback)
    # always remove the dxf file
    remove_temp_file(dxf_file_name)
    return result

