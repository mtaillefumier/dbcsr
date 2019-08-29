#!/usr/bin/env python
# -*- coding: utf-8 -*-
####################################################################################################
# Copyright (C) by the DBCSR developers group - All rights reserved                                #
# This file is part of the DBCSR library.                                                          #
#                                                                                                  #
# For information on the license, see the LICENSE file.                                            #
# For further information please visit https://dbcsr.cp2k.org                                      #
# SPDX-License-Identifier: GPL-2.0+                                                                #
####################################################################################################

from __future__ import print_function

import json
import argparse
from os import path

from kernels.smm_acc_predict import params_dict_to_kernel


# ===============================================================================
def main(gpu_version, base_dir):
    # Read existing parameters
    print("GPU version: {}".format(gpu_version))
    param_fn = path.join(base_dir, "parameters_{}.json".format(gpu_version))
    with open(param_fn) as f:
        all_kernels = [params_dict_to_kernel(**params) for params in json.load(f)]
    print(
        "About to process {:,} kernels from file {}".format(len(all_kernels), param_fn)
    )

    # Construct output
    out, all_pars = write_parameters_file(all_kernels)

    # Write to c++ header-file
    file_h = "parameters.h"
    print("Found {:,} kernels in file {}".format(len(all_kernels), param_fn))
    print("Printing them to file {}".format(file_h))
    with open(file_h, "w") as f:
        f.write(out)


# ===============================================================================
def write_parameters_file(all_pars):

    # Header
    out = """\
/*------------------------------------------------------------------------------------------------*
 * Copyright (C) by the DBCSR developers group - All rights reserved                              *
 * This file is part of the DBCSR library.                                                        *
 *                                                                                                *
 * For information on the license, see the LICENSE file.                                          *
 * For further information please visit https://dbcsr.cp2k.org                                    *
 * SPDX-License-Identifier: GPL-2.0+                                                              *
 *------------------------------------------------------------------------------------------------*/

/*****************************************************************************
 *  FILE GENERATED BY SCRIPT 'generate_parameters.py' DO NOT EDIT            *
 *****************************************************************************/

#ifndef PARAMETERS_H
#define PARAMETERS_H

#include "parameters_utils.h"

/*
 * Lookup table: given a triplet (m, n, k) describing a matrix-matrix multiplication,
 * look up its optimal kernel parameters
 *
 * Keys:
 *   (m, n, k)
 *
 * Values: array of 8 integers with elements:
 *   0: mm algorithm (enum defined in libsmm_acc.h, possible values: 1, 2, 3, 4, 5)
 *   1: tile_m
 *   2: tile_n
 *   3: w
 *   4: v
 *   5: threads
 *   6: grouping
 *   7: minblocks
 *
 * Note: for the matrix matrix multiplication algorithms which take less than 8 parameters (i.e. tiny, small, medium),
 * the superfluous parameters are set to 0
 */

static const std::unordered_map<Triplet, KernelParameters> ht  = {
"""
    # Initializer list body
    print("Get parameters and write to file")
    init_list_line = (
        "    {{ {{{{{m:3}, {n:3}, {k:3}}}}},"
        + " {{{{ {algorithm:1}, {tile_m:2}, {tile_n:2}, {w:2}, {v:2}, {threads:3}, {grouping:2}, {minblocks:2} }}}} }},"
        + "  // perf: {perf} {source}\n"
    )
    for pars in all_pars:
        out += init_list_line.format(**pars.as_dict_for_parameters_h)

    # Footer
    out += """\
};

#endif
//EOF
\n\n
"""

    return out, all_pars


# ===============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generator of libsmm_acc. The Library for Small Matrix Multiplications on GPU.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-g",
        "--gpu_version",
        metavar="GPU_VERSION",
        default="P100",
        help="GPU card version, used to select the appropriate libsmm_acc parameters file. Default: %(default)s",
    )
    parser.add_argument(
        "-d",
        "--base_dir",
        metavar="BASE_DIR",
        default="parameters/",
        help="Set the base directory to look for the parameter files. Default: %(default)s",
    )
    args = parser.parse_args()
    main(args.gpu_version, args.base_dir)
