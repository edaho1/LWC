#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
options extraction.
'''

# cryptotvgen 1.0.0
# Ekawat (Ice) Homsirikimal and William Diehl
#
# Based on aeadtvgen 2.0.0 by Ekawat Homsirikamol (GMU CERG)

import argparse
import textwrap
import sys
import os
from enum import Enum

class AlgorithmClass(Enum):
    AEAD = 0
    HASH = 1

# ============================================================================
# Reference: http://stackoverflow.com/questions/8624034/python-argparse-type-and-choice-restrictions-with-nargs-1
def make_validate_library_action(algorithm_class):
    class ValidateLibrary(argparse.Action):
        ''' Validate whether specified library is valid (compiled) '''
        def __call__(self, parser, args, value=0, option_string=None):
            # print('{n} {v} {o}'.format(n=args, v=value, o=option_string))
            lib_path = args.lib_path
            if not os.path.exists(lib_path):
                raise(FileNotFoundError('No library path found {s!r}. Please'
                                        ' provide the correct path!'
                                        .format(s=lib_path)))
    
            lib_name = value            
            if (algorithm_class == AlgorithmClass.AEAD):
                class_path = 'crypto_aead'
                delattr(args, 'aead')
            elif (algorithm_class == AlgorithmClass.HASH):
                class_path = 'crypto_hash'
                delattr(args, 'hash')
            else:
                raise(argparse.ArgumentError('Unsupported algorithm class'))
            b_windows = True if sys.platform in ['win32', 'win64', 'msys'] else False
            lib_name += '_dbg' if args.dbg == True else ""
            lib_name += '.dll' if b_windows else '.so'
            lib_file = '{}/{}/{}'.format(lib_path, class_path, lib_name)
            
            if not os.path.isfile(lib_file):
                raise(FileNotFoundError('No library {s!r} found. Please compile'
                                        ' it first!'.format(s=lib_file)))


            try:
                algorithm_class_paths = args.algorithm_class_paths
            except AttributeError:
                algorithm_class_paths = ['' for a in AlgorithmClass]            
            
            algorithm_class_paths[algorithm_class.value] = lib_file
                        
            setattr(args, 'algorithm_class_paths', algorithm_class_paths)
    return ValidateLibrary

class UseDebugLibrary(argparse.Action):
    ''' Validate block_size_ad '''
    def __call__(self, parser, args, values, option_string=None):
        # print '{n} {v} {o}'.format(n=args, v=values, o=option_string)
        for algorithm_class, path in args.algorithm_class_paths:
            new_path = path
            args.algorithm_class_paths[algorithm_class] = new_path


class ValidateBlockSizeAd(argparse.Action):
    ''' Validate block_size_ad '''
    def __call__(self, parser, args, values, option_string=None):
        # print '{n} {v} {o}'.format(n=args, v=values, o=option_string)
        if values > args.block_size:
            raise(argparse.ArgumentError(
                self, 'block_size_ad cannot be larger than block_size'))
        setattr(args, self.dest, values)

class ValidateMsgFormat(argparse.Action):
    ''' Validate message format '''
    def __call__(self, parser, args, values, option_string=None):
        # print '{n} {v} {o}'.format(n=args, v=values, o=option_string)

        # Remove duplicate
        # http://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-in-python-whilst-preserving-order
        seen = set()
        seen_add = seen.add
        values = [x for x in values if not (x in seen or seen_add(x))]

        # Check invalid segment
        valid_segments = (
            'npub', 'nsec', 'ad', 'ad_npub', 'npub_ad',
            'data', 'data_tag', 'tag', 'hash_tag')
        for value in values:
            if value.lower() not in valid_segments:
                raise argparse.ArgumentError(
                    self, 'Invalid segment type {s!r}'.format(s=value))

        setattr(args, self.dest, values)


routines = ('gen_random', 'gen_custom', 'gen_test_routine', 'gen_single', 'gen_hash', 'gen_test_combined')

class ValidateGenRandom(argparse.Action):
    ''' Validate gen_random option '''
    def __call__(self, parser, args, values, option_string=None):
        # print '{n} {v} {o}'.format(n=args, v=values, o=option_string)

        if (values < 1 or values > 1000):
            raise argparse.ArgumentError(
                self, textwrap.dedent('''\
                Number of test has to between 1 and 1000: {s!r}'''
                .format(s=values)))
        try:
            routine = getattr(args, 'routines')
            routine.append(routines.index(self.dest))
        except AttributeError:
            routine = [routines.index(self.dest), ]
        setattr(args, 'routines', routine)
        setattr(args, self.dest, values)

class ValidateGenCustom(argparse.Action):
    ''' Validate gen_custom option '''
    def __call__(self, parser, args, values, option_string=None):
        # print '{n} {v} {o}'.format(n=args, v=values, o=option_string)

        # Create string list from an input string
        list = [
            [item.strip() for item in array.strip().split(',')]
            for array in values.split(':')]

        # Convert string to int
        for list_ind in range(len(list)):
            for item_ind in range(5):
                val = list[list_ind][item_ind]
                # check digit
                if val.isdigit():
                    list[list_ind][item_ind] = int(val)
                    continue
                # check boolean
                inv_data = 0
                if (item_ind == 1):
                    inv_data = 1
                if (item_ind == 4):
                    if val.lower == 'true':
                        list[list_ind][item_ind] = 1
                    elif val.lower() == 'false':
                        list[list_ind][item_ind] = 0
                elif (item_ind < 4):
                    if val.lower() == 'true':
                        list[list_ind][item_ind] = 0^inv_data
                    elif val.lower() == 'false':
                        list[list_ind][item_ind] = 1^inv_data
                else:
                    raise argparse.ArgumentError(
                        self, textwrap.dedent('''\
                        Invalid argument for --{dest}:\t{s}
                        '''.format(dest=self.dest, s=list)))
        try:
            routine = getattr(args, 'routines')
            routine.append(routines.index(self.dest))
        except AttributeError:
            routine = [routines.index(self.dest), ]
        setattr(args, 'routines', routine)
        setattr(args, self.dest, list)

class ValidateGenTestRoutine(argparse.Action):
    ''' Validate gen_test_routine option '''
    def __call__(self, parser, args, values, option_string=None):
        # print '{n} {v} {o}'.format(n=args, v=values, o=option_string)

        min = 1
        max = 22
        if (values[0] < min or values[0] > max):
            raise argparse.ArgumentError(
                self, 'Values of out bound (BEGIN={})'.format(values[0]))
        if (values[1] < min or values[1] > max):
            raise argparse.ArgumentError(
                self, 'Values of out bound (END={})'.format(values[1]))
        if (values[0] > values[1]):
            raise argparse.ArgumentError(
                self, 'BEGIN > END ({v[0]} > {v[1]})'.format(v=values))
        if (values[2] not in [0, 1, 2]):
            raise argparse.ArgumentError(
                self, 'Valid MODE is [0, 1, 2]. (MODE={v[2]})'.format(v=values))
        try:
            routine = getattr(args, 'routines')
            routine.append(routines.index(self.dest))
        except AttributeError:
            routine = [routines.index(self.dest), ]
        setattr(args, 'routines', routine)
        setattr(args, self.dest, values)

class ValidateGenTestCombinedRoutine(argparse.Action):
    ''' Validate gen_test_routine option '''
    def __call__(self, parser, args, values, option_string=None):
        # print '{n} {v} {o}'.format(n=args, v=values, o=option_string)

        min = 1
        max = 33
        if (values[0] < min or values[0] > max):
            raise argparse.ArgumentError(
                self, 'Values of out bound (BEGIN={})'.format(values[0]))
        if (values[1] < min or values[1] > max):
            raise argparse.ArgumentError(
                self, 'Values of out bound (END={})'.format(values[1]))
        if (values[0] > values[1]):
            raise argparse.ArgumentError(
                self, 'BEGIN > END ({v[0]} > {v[1]})'.format(v=values))
        if (values[2] not in [0, 1, 2]):
            raise argparse.ArgumentError(
                self, 'Valid MODE is [0, 1, 2]. (MODE={v[2]})'.format(v=values))
        try:
            routine = getattr(args, 'routines')
            routine.append(routines.index(self.dest))
        except AttributeError:
            routine = [routines.index(self.dest), ]
        setattr(args, 'routines', routine)
        setattr(args, self.dest, values)

class ValidateHash(argparse.Action):
    ''' Validate gen_hash_routine option '''
    def __call__(self, parser, args, values, option_string=None):
        #print ( '{n} {v} {o}'.format(n=args, v=values, o=option_string))

        min = 1
        max = 22
        if (values[0] < min or values[0] > max):
            raise argparse.ArgumentError(
                self, 'Values of out bound (BEGIN={})'.format(values[0]))
        if (values[1] < min or values[1] > max):
            raise argparse.ArgumentError(
                self, 'Values of out bound (END={})'.format(values[1]))
        if (values[0] > values[1]):
            raise argparse.ArgumentError(
                self, 'BEGIN > END ({v[0]} > {v[1]})'.format(v=values))
        if (values[2] not in [0, 1, 2]):
            raise argparse.ArgumentError(
                self, 'Valid MODE is [0, 1, 2]. (MODE={v[2]})'.format(v=values))
        try:
            routine = getattr(args, 'routines')
            routine.append(routines.index(self.dest))
        except AttributeError:
            routine = [routines.index(self.dest), ]
        setattr(args, 'routines', routine)
        setattr(args, self.dest, values)

class ValidateGenSingle(argparse.Action):
    ''' Validate gen_single option '''
    def __call__(self, parser, args, values, option_string=None):
        # print '{n} {v} {o}'.format(n=args, v=values, o=option_string)

        if values[0].isdigit():
            values[0] = int(values[0])
        elif values[0].lower() == 'true':
            values[0] = 1
        elif values[0].lower() == 'false':
            values[0] = 0

        # Check hex
        for val in values[1:]:
            if len(val) == 0:
                continue
            int(val, 16)

        txt = ['KEY', 'NPUB', 'NSEC']
        exp = [args.key_size, args.npub_size, args.nsec_size]
        for j, val in enumerate(exp):
            i = j+1
            if (val > 0 and len(values[i])*4 != val):
                raise argparse.ArgumentError(
                    self, '{}:{}(size={}) must have the size of {}'
                    .format(txt[j], values[i], len(values[i])*4, val))

        # Check
        try:
            routine = getattr(args, 'routines')
            routine.append(routines.index(self.dest))
        except AttributeError:
            routine = [routines.index(self.dest), ]
        setattr(args, 'routines', routine)
        setattr(args, self.dest, values)

class InvalidateArgument(argparse.Action):
    def __call__(self, parser, args, values, option_string=None):
        raise argparse.ArgumentError(
            self, 'This argument is not yet supported.')


# ============================================================================
# Reference: http://stackoverflow.com/questions/34544752/argparse-and-argumentdefaultshelpformatter-formatting-of-default-values-when-sy
class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawTextHelpFormatter):
    ''' RawTextHelpFromatter + ArgumentDefaultsHelpFormatter class'''
    def _get_help_string(self, action):
        help = action.help
        if '%(default)' not in action.help:
            if action.default is not argparse.SUPPRESS:
                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    if type(action.default)==type(sys.stdin):
                        print(action.default.name)
                        help += ' (default: '+str(action.default.name)+')'
                    else:
                        help += ' (default: %(default)s)'
        return help

# ============================================================================
# Argument parsing
# ============================================================================
def get_parser():
    parser = argparse.ArgumentParser(
        add_help=False,
        formatter_class=CustomFormatter,
        prog='cryptotvgen',
        description = textwrap.dedent('''\
            Test vectors generator for NIST Lightweight Cryptography
            candidates. The script REQUIREs that the C library for the
            intended algorithm is compiled first.'''))

    mainop = parser.add_argument_group(
        textwrap.dedent('''\
            :::::Required Parameters:::'''),
        'Library path specifier::')
    mainop.add_argument(
        'lib_path',
        help=textwrap.dedent('''\
            Path to CAESAR shared library, i.e.
                ../../prepare_src/libs.'''))
                
    secondaryop = parser.add_argument_group(
        textwrap.dedent('''\
            :::::At least one of these parameters are required:::'''),
        'Library name specifier::')
    secondaryop.add_argument(
        '--aead', action=make_validate_library_action(AlgorithmClass.AEAD),
        metavar='<ALGORITHM_NAME--IMPLEMENTATION_NAME>',
        help=textwrap.dedent('''\
            Shared library's for AEAD algorithm, i.e. gimli24v1--ref
            Note: The library should be generated prior to the start
            of the program.'''))

    secondaryop.add_argument(
        '--hash', action=make_validate_library_action(AlgorithmClass.HASH),
        metavar='<ALGORITHM_NAME--IMPLEMENTATION_NAME>',
        help=textwrap.dedent('''\
            Shared library's for HASH algorithm, i.e. gimli24v1--ref
            Note: The library should be generated prior to the start
            of the program.'''))

    test = parser.add_argument_group(':::::Test Generation Parameters:::',
            textwrap.dedent('''\
            Test vectors generation modes (use at least one from the list
            below)::
            Common notation and convetions:
            AD - Associated Data
            DATA - Plaintext/Message or Ciphertext
            PT - Plaintext/Message
            CT - Ciphertext
            HASH - Message to be hashed
            HASH_TAG - Message Digest
            (*)_LEN - Length of data (*) type, i.e. AD_LEN.
            Operation - 0: encryption, 1: decryption
            H* - a string composed of multiple repetitions of the hexadecimal
                 digit H (the number of repetitions is determined by the size
                 of a given argument)
                 All lengths are expressed in bytes.

            For Boolean arguments, 0 can be used instead of False,
            and 1 can be used instead of True.
            '''))
    # run_mutex = test.add_mutually_exclusive_group(required=True)
    test.add_argument(
        '--gen_random', type=int, default=0, metavar='N',
        action=ValidateGenRandom,
        help=textwrap.dedent('''\
            Randomly generates multiple test vectors with
            varying AD_LEN, PT_LEN, and operation (For use only with AEAD)'''))
    test.add_argument(
        '--gen_custom_mode', type=int, default=0, choices=range(3),
        metavar='MODE', help=textwrap.dedent('''\ The mode of test vector generation used by the --gen_custom option.

            Meaning of MODE values:
                0 = All random data
                1 = Fixed test values.
                    Key=0xFF*, Npub=0x55*, Nsec=0xDD*,
                    AD=0xA0*, PT=0xC0*, HASH=0xFF*
                2 = Same as option 1, except an input is now a running
                    value (each subsequent byte is a previous byte
                    incremented by 1).
            '''))

    test.add_argument(
        '--gen_custom', type=str,
        metavar=('Array'), action=ValidateGenCustom,
        help=textwrap.dedent('''\
            Randomly generate multiple test vectors, with each test vector
            specified using the following fields:
               NEW_KEY (Boolean), DECRYPT (Boolean), AD_LEN, PT_LEN or
               HASH_LEN, HASH (Boolean)
               ":" is used as a separator between two consecutive test
               vectors.

            Example:
            --gen_custom True,False,0,20,False:0,0,0,24,True

            Generates 2 test vectors. The first vector will
            create a new key and perform an encryption with a dataset that
            has AD_LEN and PT_LEN of 0 and 20 bytes, respectively.  The
            second vector performs a HASH on a message with HASH_LEN of 24
            bytes.'''))
    test.add_argument(
        '--gen_hash', type=int, nargs=3, default=None, metavar=('BEGIN','END','MODE'),action=ValidateHash,help=textwrap.dedent('''\
            This mode generates 20 test vectors for HASH only.
            The test vectors are specified using the following array:
               [NEW_KEY (boolean),  # Ignored due to hash operation
                DECRYPT (boolean),  # Ignored due to hash operation
                AD_LEN,             # Ignored due to hash operation
                PT_LEN,
                HASH   (boolean)]:
            The following parameters are used:
                [False ,    False,       0,         0        ,   True],
                [False ,    False,       0,         1        ,   True],
                [False,     False,       0,         2        ,   True],
                [False ,    False,       0,         3        ,   True],
                [False,     False,       0,         4        ,   True],
                [False ,    False,       0,         5        ,   True],
                [False,     False,       0,         6        ,   True],
                [False ,    False,       0,         7        ,   True],
                [False,     False,       0,         bsd-2    ,   True],
                [False ,    False,       0,         bsd-1    ,   True],
                [False,     False,       0,         bsd      ,   True],
                [False ,    False,       0,         bsd+1    ,   True],
                [False,     False,       0,         bsd+2    ,   True],
                [False ,    False,       0,         bsd*2    ,   True],
                [False,     False,       0,         bsd*2+1  ,   True],
                [False ,    False,       0,         bsd*3    ,   True],
                [False,     False,       0,         bsd*3+1  ,   True],
                [False ,    False,       0,         bsd*4    ,   True],
                [False,     False,       0,         bsd*4+1  ,   True],
                [False ,    False,       0,         bsd*5    ,   True],
                [False,     False,       0,         bsd*5+1  ,   True]]

            where,
                bsa is the associated data block size (block_size_ad = 0 for
                hash), and
                bsd is the data block size (block_size = # of bytes of
                message to hash).

            Note that sdi.txt will have a header, but no generated keys.
            Also, key_id = 0 for all hash test vectors.

            BEGIN (min=1,max=22) determines the starting test number.
            END (min=1,max=22) determines the ending test number.
            MODE determines the test vector generation mode, where
                0 = All random data
                1 = Fixed test values.
                    HASH=0xF0*
                2 = Same as option 1, except each input is now a running
                    value (each subsequent byte is a previous byte
                    incremented by 1).

            Example:

            --gen_hash 1 20 0

            Generates tests 1 to 20 with MODE=0.

            --gen_hash 5 5 1

            Generates test 5 with MODE=1.''')
        )
    test.add_argument(
        '--gen_test_combined', type=int, nargs=3, default=None, metavar=('BEGIN','END','MODE'),action=ValidateGenTestCombinedRoutine,help=textwrap.dedent('''
            This mode generates 33 test vectors for the common sizes of AD and
            PT that the hardware designer should, at a minimum, verify. It also
            combines AEAD and hash test vectors into one set of test
            vectors, which are interleaved as encrypt, decrypt, and hash.
            The test vectors are specified using the following array:
               [NEW_KEY (boolean),
                DECRYPT (boolean),
                AD_LEN,
                PT_LEN,
                HASH    (boolean)]:
            The following parameters are used:
                [True ,     False,      0,         0        ,   False],
                [False,     True,       0,         0        ,   False],
                [False,     True,       0,         0        ,   True],
                [True ,     False,      1,         0        ,   False],
                [False,     True,       1,         0        ,   False],
                [False,     True,       0,         1        ,   True],
                [True ,     False,      0,         1        ,   False],
                [False,     True,       0,         1        ,   False],
                [False,     True,       0,         2        ,   True],
                [True ,     False,      1,         1        ,   False],
                [False,     True,       1,         1        ,   False],
                [False,     True,       0,         3        ,   True],
                [True ,     False,      2,         2        ,   False],
                [False,     True,       2,         2        ,   False],
                [False,     True,       0,         4        ,   True],
                [True ,     False,      bsa-1,     bsd-1    ,   False],
                [False,     True,       bsa-1,     bsd-1    ,   False],
                [False,     True,       0,         bsd-1    ,   True],
                [True ,     False,      bsa,       bsd      ,   False],
                [False,     True,       bsa,       bsd      ,   False],
                [False,     True,       0,         bsd+1    ,   True],
                [True ,     False,      bsa+1,     bsd+1    ,   False],
                [False,     True,       bsa+1,     bsd+1    ,   False],
                [False,     True,       0,         bsd+2    ,   True],
                [True ,     False,      bsa*2,     bsd*2    ,   False],
                [False,     True,       bsa*2,     bsd*2    ,   False],
                [False,     True,       0,         bsd*2    ,   True],
                [True ,     False,      bsa*2+1,   bsd*2+1  ,   False],
                [False,     True,       bsa*2+1,   bsd*2+1  ,   False],
                [False,     True,       0,         bsd*2+1  ,   True],
                [True ,     False,      bsa*3,     bsd*3    ,   False],
                [False,     True,       bsa*3,     bsd*3    ,   False],
                [False,     True,       0    ,     bsd*3    ,   True]]

            where,
                bsa is the associated data block size (block_size_ad), and
                bsd is the data block size (block_size).

            Note: key_id = 0 for all hash test vectors.

            BEGIN (min=1,max=33) determines the starting test number.
            END (min=1,max=33) determines the ending test number.
            MODE determines the test vector generation mode, where
                0 = All random data
                1 = Fixed test values.
                    Key=0xF*, Npub=0x5*, Nsec=0xD*,
                    Ad=0xA0*, PT=0xC0*, HASH=0xF*
                2 = Same as option 1, except each input is now a running
                    value (each subsequent byte is a previous byte
                    incremented by 1).

            Example:

            --gen_test_combine 1 20 0

            Generates tests 1 to 20 with MODE=0.

            --gen_test_combine 5 5 1

            Generates test 5 with MODE=1.''')
        )

    test.add_argument(
        '--gen_test_routine', type=int, nargs=3, default=None,
        metavar=('BEGIN', 'END', 'MODE'), action=ValidateGenTestRoutine,
        help=textwrap.dedent('''\
            This mode generates test vectors for the common sizes of AD and
            PT that the hardware designer should, at a minimum, verify.
            Only AEAD test vectors are generated, hashes are not generated.
            The test vectors are specified using the following array:
               [NEW_KEY (boolean),
                DECRYPT (boolean),
                AD_LEN,
                PT_LEN,
                HASH    (boolean)]:
            The following parameters are used:
                [True ,     False,      0,         0        ,   False],
                [False,     True,       0,         0        ,   False],
                [True ,     False,      1,         0        ,   False],
                [False,     True,       1,         0        ,   False],
                [True ,     False,      0,         1        ,   False],
                [False,     True,       0,         1        ,   False],
                [True ,     False,      1,         1        ,   False],
                [False,     True,       1,         1        ,   False],
                [True ,     False,      bsa,       bsd      ,   False],
                [False,     True,       bsa,       bsd      ,   False],
                [True ,     False,      bsa-1,     bsd-1    ,   False],
                [False,     True,       bsa-1,     bsd-1    ,   False],
                [True ,     False,      bsa+1,     bsd+1    ,   False],
                [False,     True,       bsa+1,     bsd+1    ,   False],
                [True ,     False,      bsa*2,     bsd*2    ,   False],
                [False,     True,       bsa*2,     bsd*2    ,   False],
                [True ,     False,      bsa*3,     bsd*3    ,   False],
                [False,     True,       bsa*3,     bsd*3    ,   False],
                [True ,     False,      bsa*4,     bsd*4    ,   False],
                [False,     True,       bsa*4,     bsd*4    ,   False],
                [True ,     False,      bsa*5,     bsd*5    ,   False],
                [False,     True,       bsa*5,     bsd*5    ,   False]

            where,
                bsa is the associated data block size (block_size_ad), and
                bsd is the data block size (block_size).

            BEGIN (min=1,max=22) determines the starting test number.
            END (min=1,max=22) determines the ending test number.
            MODE determines the test vector generation mode, where
                0 = All random data
                1 = Fixed test values.
                    Key=0xF*, Npub=0x5*, Nsec=0xD*,
                    Ad=0xA0*, PT=0xC0*
                2 = Same as option 1, except each input is now a running
                    value (each subsequent byte is a previous byte
                    incremented by 1).

            Example:

            --gen_test_routine 1 20 0

            Generates tests 1 to 20 with MODE=0.

            --gen_test_routine 5 5 1

            Generates test 5 with MODE=1.
            '''))
    test.add_argument(
        '--gen_single', nargs=6,
        metavar=('DECRYPT', 'KEY','NPUB','NSEC','AD','PT'),
        action=ValidateGenSingle,
        help=textwrap.dedent('''\
            Generate a single test vector based on the provided values of
            all inputs expressed in the hexadecimal notation. (For use only
            with AEAD)

            Example:
            --gen_single 0 5555 0123456 789ABCD 010204 08090A

            Note:
            KEY, NPUB and NSEC must have size equal to the expected
            value. Exception: NSEC is ignored --nsec_size is set to 0.
            All arguments must contain an even number of hexadecimal
            digits, e.g., 00 is valid; 0 is invalid.
            '''))

    optops = parser.add_argument_group(':::::Optional Parameters::::',
        'Debugging options::')
    optops.add_argument("-h", "--help", action="help",
        help="Show this help message and exit.")
    optops.add_argument(
        '--dbg', default=False, nargs=0, action=UseDebugLibrary,
        help='Run the C code with the DBG preprocessor flag.')

    optops.add_argument(
        '--verify_lib', default=False, action='store_true',
        help=textwrap.dedent('''\
            This operation will verify the generated test vectors
            via the decryption operation.

            Note: This option provides an additional check against possible
                  mismatch of results between encryption and decryption
                  in the reference software.
            '''))

    optops.add_argument('-V', '--version', action="version",
        version="%(prog)s 1.0")
    optops.add_argument('-v', '--verbose', default=False, action='store_true',
        help=('Verbose for script debugging purposes.'))

    impops = parser.add_argument_group(
        '', 'Algorithm and implementation specific options::')
    impops.add_argument(
        '--io', nargs=2, type=int, default=(32, 32),
        metavar=('PUBLIC_PORTS_WIDTH', 'SECRET_PORT_WIDTH'),
        help='Size of PDI/DO and SDI port in bits.')
    impops.add_argument(
        '--key_size', type=int, default=128, metavar='BITS',
        help='Size of key in bits')
    impops.add_argument(
        '--npub_size', type=int, default=128, metavar='BITS',
        help='Size of public message number in bits')
    impops.add_argument(
        '--nsec_size', type=int, default=0, metavar='BITS',
        help='Size of secret message number in bits')
    impops.add_argument(
        '--tag_size', type=int, default=128, metavar='BITS',
        help='Size of authentication tag in bits')
    impops.add_argument(
        '--message_digest_size', type=int, default=64, metavar='BITS',
        help='Size of message digest (hash_tag) in bits')
    impops.add_argument(
        '--block_size', type=int, default=128, metavar='BITS',
        help='''Algorithm's data block size''')
    impops.add_argument(
        '--block_size_ad', type=int, metavar='BITS',
        action=ValidateBlockSizeAd,
        help='''Algorithm's associated data block size.
        This parameter is assumed to be equal to block_size if unspecified.''')
    impops.add_argument(
        '--ciph_exp', default=False,
        action='store_true',
        help=textwrap.dedent('''\
            Ciphertext expansion algorithm. When this option is set, the last
            block will have its own segment. This is required for a correct
            operation of the accompanied PostProcessor.

            Currently, we assume that PAD_AD and PAD_D are both set to 4
            when this mode is used.
            '''))
    impops.add_argument(
        '--ciph_exp_noext', default=False, action='store_true',
        help=textwrap.dedent('''\
            [requires --ciph_exp]

            Additional option for the ciphertext expansion mode. This option
            indicates that the algorithm does not expand the ciphertext
            (i.e., does not make the ciphertext size greater than the message
            size) if the message size is a multiple of a block size.'''))
    impops.add_argument(
        '--add_partial', default=False,
        action='store_true',
        help=textwrap.dedent('''\
            [requires --ciph_exp]

            For use with --ciph_exp flag. When this option is set, a PARTIAL
            bit will be set to 1 in the header of a data segment
            if the size of this segment is not a multiple of a block size.

            Note: This option is required for algorithms such as AES_COPA
            '''))

###### Not supported in this version
#    impops.add_argument(
#        '--reverse_ciph', default=False,
#        #action='store_true',
#        action=InvalidateArgument,
#        help=textwrap.dedent('''\
#            Note: Not yet supported. Coming soon ~~~
#
#            [requires --ciph_exp]
#
#            Reversed ciphertext. When this option is set, the input ciphertext
#            is provided in a reversed order (including the possible length
#            segment).
#            Note: Only used by PRIMATEs-APE.')
#            '''))

    tvops = parser.add_argument_group(
        '', 'Formatting options::')
    tvops.add_argument(
        '--msg_format', nargs='+', action=ValidateMsgFormat,
        default=('npub', 'ad', 'data', 'tag'), metavar='SEGMENT_TYPE',
        help=textwrap.dedent('''\
            Specify the order of segment types in the input to encryption and
            decryption. Tag is always omitted in the input to encryption, and
            included in the input to decryption. In the expected output from
            encryption tag is always added last. In the expected output from
            decryption only nsec and data are used (if specified).
            Len is always automatically added as a first segment in the
            input for encryption and decryption for the offline algorithms.
            Len is not allowed as an input to encryption or decryption for
            the online algorithms.

            Example 1:
            --msg_format npub tag data ad

            The above example generates
            for an input to encryption: npub, data (plaintext), ad
            for an expected output from encryption: data (ciphertext), tag
            for an input to decryption: tag, data (ciphertext), ad
            for an expected output from decryption: data (plaintext)

            Example 2:
            --msg_format npub_ad data_tag

            The above example generates
            for an input to encryption:  npub_ad, data (plaintext)
            for an expected output from encryption: data_tag (ciphertext_tag)
            for an input to decryption: npub_ad, data_tag (ciphertext_tag)
            for an expected output from decryption: data (plaintext)

            Valid Segment types (case-insensitive):
                npub    -> public message number
                nsec    -> secret message number
                ad      -> associated data
                ad_npub -> associated data || npub
                npub_ad -> npub || associated data
                data    -> data (pt/ct)
                data_tag -> data (pt/ct) || tag
                tag     -> authentication tag

            Note: no support for multiple segments of the same type,
            separated by segments of another type e.g., header and trailer,
            treated as two segments of the type AD, separated by the message segments

            '''))
    tvops.add_argument(
        '--offline', default=False,
        action='store_true',
        help=textwrap.dedent('''\
            Indicate that the cipher is offline, i.e., the length of AD and
            DATA must be known before the encryption/decryption starts. If this
            option is used, the length segment will be automatically added as
            a first segment in the input to encryption and decryption.
            Otherwise, the length segment will not be generated for either
            encryption or decryption.
            '''))
    tvops.add_argument(
        '--min_ad', type=int, default=0, metavar='BYTES',
        help='Minimum randomly generated AD length')
    tvops.add_argument(
        '--max_ad', type=int, default=1000, metavar='BYTES',
        help='Maximum randomly generated AD length')
    tvops.add_argument(
        '--min_d', type=int, default=0, metavar='BYTES',
        help='Minimum randomly generated data length')
    tvops.add_argument(
        '--max_d', type=int, default=1000, metavar='BYTES',
        help='Maximum randomly generated data length')
    tvops.add_argument(
        '--max_block_per_sgmt', type=int, default=9999, metavar='COUNT',
        help='Maximum data block per segment (based on --block_size) parameter')
    tvops.add_argument(
        '--max_io_per_line', type=int, default=9999, metavar='COUNT',
        help=textwrap.dedent('''\
            Maximum data length in multiples of I/O width in a data line of test
            file. This option helps readability when a test vector is large.

            Example:
            If a user wants to limit a vector representation of data in a file
            to a block size where a block size is 64-bit and I/O = 32-bit,
            the value should be set to 2 (32*2 = 64 bits).

            --io 32 --block_size 64
            DAT = 000102030405060708090A0B0C0D0E0F

            --io 32 --block_size 64 --max_io_per_line 2

            DAT = 0001020304050607
            DAT = 08090A0B0C0D0E0F
            '''))

    tvops.add_argument(
        '--pdi_file', default='pdi.txt', metavar='FILENAME',
        help='Public data input filename')
    tvops.add_argument(
        '--sdi_file', default='sdi.txt', metavar='FILENAME',
        help='Secret data input filename')
    tvops.add_argument(
        '--do_file', default='do.txt', metavar='FILENAME',
        help='Data output filename')
    tvops.add_argument(
        '--dest', metavar='PATH_TO_DEST', default='.',
        help='Destination folder where the files should be written to.')
    tvops.add_argument(
        '--human_readable', default=False, action='store_true',
        help=textwrap.dedent('''\
            Create a human readable file (tests_vectors.txt) for each
            test vector in the format similar to NIST test vectors
            used in SHA-3, i.e.:

            # Message 1
            Key      = HEXSTR    # if AEAD
            Npub     = HEXSTR    # if AEAD
            Nsec_PT  = HEXSTR    # if --nsec_size > 0
            AD       = HEXSTR    # if AEAD
            PT       = HEXSTR    # if AEAD
            HASH     = HEXSTR    # if hash
            Nsec_CT  = HEXSTR    # if --nsec_size > 0
            CT       = HEXSTR    # if AEAD
            TAG      = HEXSTR    # if AEAD
            HASH_TAG = HEXSTR    # if hash
            '''))

    ccops = parser.add_argument_group(
        '', '[Experimental] CryptoCore options::')
    ccops.add_argument(
        '--cc_hls', default=False,
        action='store_true',
        help=textwrap.dedent('''\
            Generates test vectors for CryptoCore in C (used by HLS)
            '''))
    ccops.add_argument(
        '--cc_pad_enable', default=False,
        action='store_true',
        help='Enable padding operation')
    ccops.add_argument(
        '--cc_pad_ad', type=int, default=0, metavar='PAD_AD_MODE',
        help='Associated data padding mode')
    ccops.add_argument(
        '--cc_pad_d', type=int, default=0, metavar='PAD_D_MODE',
        help='Data input padding mode')
    ccops.add_argument(
        '--cc_pad_style', type=int, default=1, metavar='PAD_STYLE',
        help='Padding style')
    return parser

if __name__ == '__main__':
    parse_options(sys.argv[1:])