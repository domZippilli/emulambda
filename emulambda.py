#!/usr/bin/env python
from __future__ import print_function
import argparse
import gc
from importlib import import_module
import json
import math
import resource
import sys
import time

from hurry.filesize import size

from errors import import_fail, event_fail, invoke_fail
from timeout import timeout, TimeoutError

__author__ = 'dominiczippilli'
__description__ = '''
A local emulator for AWS Lambda for Python.
Features:
  - Run an AWS-compatible lambda function
  - Take event from file
  - Set timeout up to 300s
  - Send lambda result to stdout
  - Estimate time and memory usage in verbose mode
Planned features:
  - Take event via stdin
  - LDJSON
  - Multiple runs / test battery profile
  - SQS (use AWS CLI?)
  - Kinesis
  - AWS Event lib
  - Contexts?
'''


def parseargs():
    parser = argparse.ArgumentParser(
        description='Python AWS Lambda Emulator. At present, AWS Lambda supports Python 2.7 only.')
    parser.add_argument('lambdapath',
                        help='An import path to your function, as you would give it to AWS: `module.function`.')
    parser.add_argument('eventfile', help='A JSON file to give as the `event` argument to the function.')
    parser.add_argument('-s', '--stream', help='Treat `eventfile` as a Line-Delimited JSON stream.',
                        action='store_true') #TODO -- investigate if this can be auto-detected
    parser.add_argument('--timeout', help='Execution timeout in seconds. Default is 300, the AWS maximum.', type=int,
                        default=300)
    parser.add_argument('-v', '--verbose', help='Verbose mode. Provides exact function run, timing, etc.',
                        action='store_true')
    return parser.parse_args()


def import_lambda(path):
    try:
        # Parse path into module and function name.
        path = str(path)
        spath = path.split('.')
        module = '.'.join(spath[:-1])
        function = spath[-1]
        # Import the module and get the function.
        import_module(module)
        return getattr(sys.modules[module], function)

    except (AttributeError, TypeError) as e:
        import_fail(e)


def read_file_to_string(filename):
    try:
        with sys.stdin if filename is '-' else open(filename, 'r') as event_file:
            return event_file.read()
    except IOError as e:
        e.message = "File not found / readable!"
        event_fail(e)


def emit_to_function(stream, func):
    '''
    :param stream: A file-like object providing a LDJSON stream.
    :param func: A function to invoke with objects from the stream.
    :return: Void.
    '''
    print("Entering stream mode.")
    i = 1
    try:
        with sys.stdin if stream is '-' else open(stream, 'r') as event_stream:
            for line in event_stream:
                gc.collect()  # force GC between each run to get quality memory usage sample
                print("\nObject %i %s" % (i, line.rstrip()[:65] + ('...' if len(line) > 65 else '')))
                i += 1
                func(json.loads(line))
    except ValueError as e:
        event_fail(e)
    except IOError as e:
        event_fail(e)


def parse_event(eventstring):
    try:
        return json.loads(eventstring)
    except ValueError as e:
        event_fail(e)


def invoke_lambda(lfunc, event, context, t):
    @timeout(t)
    def _invoke_lambda(l, e, c):
        s = time.time()
        r = l(e, c)
        x = time.time() - s  # TODO investigate suitability of timeit here
        return r, x

    try:
        return _invoke_lambda(lfunc, event, context)
    except (AttributeError, TypeError):
        invoke_fail()
    except TimeoutError:
        print("Your lambda timed out! (Timeout was %is)\n" % t)
        sys.exit(1)


def render_result(args, result, exec_clock, exec_rss):
    if args.verbose:
        print("Executed %s" % args.lambdapath)
        print("Estimated...")
        print("...execution clock time:\t\t %f seconds (%i ms) (%i ms bucket)" % (
            exec_clock,
            (exec_clock * 1000),
            int(math.ceil((exec_clock * 1000) / 100.0)) * 100
        ))
        print("...execution peak RSS memory:\t\t %s (%i bytes)" % (size(exec_rss), exec_rss))
        print("----------------------RESULT----------------------")
    print(str(result))


def main():
    args = parseargs()

    # Get process peak RSS memory before execution
    pre_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    # Import the lambda
    lfunc = import_lambda(args.lambdapath)

    def execute(event):
        # Invoke the lambda
        result, exec_clock = invoke_lambda(lfunc, event, None, args.timeout)

        # Get process peak RSS memory after execution
        exec_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss - pre_rss

        # Render the result
        render_result(args, result, exec_clock, exec_rss)

    if args.stream:
        # Enter stream mode
        emit_to_function(args.eventfile, execute)
    else:
        # Deserialize single event JSON
        event = read_file_to_string(args.eventfile)
        execute(parse_event(event))


if __name__ == '__main__':
    main()
