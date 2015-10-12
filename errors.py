__author__ = 'dominiczippilli'
import traceback
import sys

def import_fail(err):
    print("\nOops! There was a problem finding your function.\n")
    print(err.message)
    sys.exit(1)


def event_fail(err):
    print("There was a problem parsing your JSON event.")
    print(err.message)
    sys.exit(1)


def stream_fail(err):
    print("There was a problem parsing your JSON stream. Perhaps you are not passing in Line-Delimited JSON?")
    print(err.message)
    sys.exit(1)


def invoke_fail():
    print("\nThere was an error running your function. Ensure it has a signature like `def lambda_handler (event, context)`.\n")
    traceback.print_exc()
    sys.exit(1)