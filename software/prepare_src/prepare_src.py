#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import textwrap
import os
import sys
import logging
import re
import shutil

### Setup
logging.basicConfig(level=logging.DEBUG)

def setup_logger(log_filename):
    '''
    Setup logging infrastructure

    Reference Source: https://realpython.com/python-logging/
    '''

    # Create a custom logger
    logger = logging.getLogger(__name__)

    # Create handlers
    # All messages goes to a log file
    i_handler = logging.FileHandler(log_filename)
    i_handler.setLevel(logging.INFO)

    # Create formatters and add it to handlers
    format = '%(asctime)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(format)
    i_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(i_handler)


    return logger;


def get_parser():
    ''' Get option parser configuration '''

    parser = argparse.ArgumentParser(
        add_help = False,
        prog     = 'prepare_src',
        description = textwrap.dedent('''\
            prepare_src is a utility to prepare source code from SuperCop directory
            for use as a shared library required for test vector generation tool (crypytotvgen).
            Currently, crypto_aead and crypto_hash are currently supported.'''))

    parser.add_argument('-h', '--help',
        action='help',
        help='Show this help message.')

    parser.add_argument('-o', '--overwrite',
        action  = 'store_true',
        default = False,
        help    = 'Overwrite previously modified/copied files')

    parser.add_argument('-c', '--clean',
        action  = 'store_true',
        default = False,
        help    = textwrap.dedent('''\
                Clean previously modified/copied files only.
                Note: This option will not modified or copied any files.'''))


    requiredNamed = parser.add_argument_group('required named arguments')
    requiredNamed.add_argument(
        '-p', '--path',        
        metavar = '<PATH>',
		required = True,	
        help=textwrap.dedent('''\
            Path to SuperCop directory or directory containing crypto_aead and crypto_hash folder.'''))
    return parser;



log = setup_logger('log.prepare');
p = get_parser()
opts = p.parse_args(sys.argv[1:])
opts.path = os.path.abspath(opts.path)

### Global constants
SUPPORTED_CRYPTO_CLASS = ('crypto_aead', 'crypto_hash')
MAKEFILE_PATH      = 'Makefile.paths'
AUTOGEN_TEXT       = 'This file has been modified or generated by prepare_src.py for library generation'


### Core code

def get_ref_paths(path):
    ''' Get reference paths of algorithm from "path" directory'''
    log.info('Extracting reference path from %s', path)

    ref_paths = []
    for alg in os.listdir(path):
        alg_path = os.path.join(path, alg)
        if not os.path.isdir(alg_path):
            continue

        alg_ref_path = os.path.join(alg_path, 'ref')
        if not os.path.isdir(alg_ref_path):
            log.warning('%s in %s has no reference folder', alg, path)
            continue
            
        ref_paths.append((alg, alg_ref_path))
    return ref_paths

def prepare_file(src, tgt, is_hash):
    ext = os.path.splitext(src)[1]
    b_src = False
    with open(tgt, 'w') as f:
        f.write('/* ### {} ### */\n'.format(AUTOGEN_TEXT))

    txt = ''
    with open(src, 'r') as r:
        txt = r.read()

    txt = re.sub(r'int\W+crypto_aead',
                 r'EXPORT int crypto_aead',
                 txt)

    txt = re.sub(r'int\W+crypto_hash',
                 r'EXPORT int crypto_hash',
                 txt)

    with open(tgt, 'a') as f:
        f.write('#include "../../../dll.h"\n')
        f.write(txt)

def prepare_directory(src_dir_path, tgt_dir_path, is_hash):
    ''' Prepare a reference algorithm directory for library generation '''

    if (is_hash):
        regex = re.compile('int\Wcrypto_hash')
    else:
        regex = re.compile('int\Wcrypto_aead_')

    b_has_header = False
    header_file_name = 'crypto_hash.h' if is_hash else 'crypto_aead.h'
    for file in os.listdir(src_dir_path):
        src_file_path = os.path.join(src_dir_path, file)
        tgt_file_path = os.path.join(tgt_dir_path, file)

        if (file == header_file_name):
            b_has_header = True
            
        if (os.path.isdir(src_file_path)):
            continue
        if (os.path.exists(tgt_file_path) and not opts.overwrite):
            continue

        b_needs_process = False

        # Determine if any special processing needs to be done for the file
        with open(src_file_path, 'r') as f:
            found = re.findall(regex, f.read())
            if found:
                b_needs_process = True

        if (b_needs_process):
            log.info('Modifying %s ...', tgt_file_path)
            prepare_file(src_file_path, tgt_file_path, is_hash)
        else:
            shutil.copy(src_file_path, tgt_file_path)
            
    # Add a dummy header file since some algorith needs it
    if not b_has_header:
        header_file_path = os.path.join(tgt_dir_path, header_file_name)
        if not os.path.exists(header_file_path):
            with open(header_file_path, 'w') as f:
                f.write('')

    # Append the target directory path to the list of Makefile
    with open(MAKEFILE_PATH, 'a') as f:
        f.write(' \\\n    {}'.format(tgt_dir_path))

def prepare_directories(crypto_class, crypto_class_path, is_hash):
    '''
    Prepare a class of cryptographic refrence directories from SuperCop for library generation.
    Only crypto_aead and crtypo_hash are supported.
    '''

    try:
        if not os.path.exists(crypto_class):
            os.mkdir(crypto_class)
    except Exception as e:
        log.error("Unable to create %s directory",crypto_class_path, exc_info=True)

    ref_paths = get_ref_paths(os.path.join(opts.path, crypto_class))


    i=0
    for (algo_name, src_dir_path) in ref_paths:
        tgt_dir_path = os.path.join(crypto_class, algo_name, 'ref')
        if not os.path.exists(tgt_dir_path):
            log.info('Creating "%s" folder', tgt_dir_path)
            os.makedirs(tgt_dir_path)
        try:
            prepare_directory(src_dir_path, tgt_dir_path, is_hash)
        except Exception as e:
            log.error('Error in algorithm "{}"'.format(algo_name), exc_info=True)           


if __name__ == '__main__':
    has_aead = False;
    has_hash = False;

    if (opts.overwrite or opts.clean):
        for dir in SUPPORTED_CRYPTO_CLASS:
            if os.path.exists(dir):
                shutil.rmtree(dir)

    if (opts.clean):
        sys.exit()

    with open(MAKEFILE_PATH, 'w') as f:
        f.write('# {}\n'.format(AUTOGEN_TEXT))
        f.write("PRIMITIVE_PATHS = ")

    for crypto_class in os.listdir(opts.path):
        if crypto_class in SUPPORTED_CRYPTO_CLASS:
            if (crypto_class == 'crypto_aead'):
                has_aead = True
            else:
                has_hash = True
            crypto_class_path = os.path.join(opts.path, crypto_class)
            prepare_directories(crypto_class, crypto_class_path, has_hash)

    if (not has_aead):
        log.warning("No crypto_aead found in opts.path")
    if (not has_hash):
        log.warning("No crypto_hash found in opts.path")
