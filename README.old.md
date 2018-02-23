# emulambda

**EMULA**tes AWS La**MBDA**

## Recommended Uses
Use `emulambda` to emulate the AWS Lambda API locally. It provides a Python "harness" that you can use to wrap your
function and run/analyze it.

  - Development
    - Run your lambda functions instantly locally, without packaging and sending to AWS.
    - Shorten your feedback loop on lambda executions.
    - Easily attach debuggers to your lambda.
  - Testing
    - Easily integrate with test tools using a simple CLI and various input methods.
    - Use stream mode to test many cases or run fuzz tests.
    - Use profiling information to identify expensive/problematic lambdas early.


## Features
Present:
  - Run an AWS-compatible lambda function
  - Take event from file or stdin
    - Also accepts LDJSON stream of events (manually switched)
  - Set timeout up to 300s
  - Send lambda result to stdout
  - Estimate time and memory usage in verbose mode
    - Also produces summary report and statistics when given a stream
  - execute your lambda function under a user-supplied IAM Role (Lambda Execution Role)
  - picks up any library present in ``./lib`` directory
  - Take context from file


Planned:
  - SQS support (though for now, you can easily pipe AWS CLI output to Emulambda stdin)
  - Kinesis support / emulation
  - An AWS event library, for common integrations with other services

## Installation
1. `git clone` [the Emulambda repo](https://github.com/fugue/emulambda/)
2. Install it with `pip install -e emulambda` (you might need to sudo this command if you're using your system Python instead of a virtualenv or similar)


## Usage

```
usage: emulambda [-h] [-s] [-t TIMEOUT] [-v] lambdapath eventfile contextfile

Python AWS Lambda Emulator. At present, AWS Lambda supports Python 2.7 only.

positional arguments:
  lambdapath            An import path to your function, as you would give it
                        to AWS: `module.function`.
  eventfile             A JSON file to give as the `event` argument to the
                        function.

optional arguments:
  -h, --help            show this help message and exit
  -r ROLE, --role ROLE  ARN of the role to execute your Lambda function (your
                        user must have AssumeRole priviledge and your user ARN
                        must be in Lambda's execution role TrustedPolicy).
  -s, --stream          Treat `eventfile` as a Line-Delimited JSON stream.
  -t TIMEOUT, --timeout TIMEOUT
                        Execution timeout in seconds. Default is 300, the AWS
                        maximum.
  -v, --verbose         Verbose mode. Provides exact function run, timing,
                        etc.
  contextfile           A JSON file to give as the `context` argument to the function
```

## Quick Start

### Single-Event Mode

From the repository root, run:
`emulambda example.example_handler - -v < example/example.json`

You should see output similar to the following:
```
Executed example.example_handler
Estimated...
...execution clock time:		 277ms (300ms billing bucket)
...execution peak RSS memory:	 368M (386195456 bytes)
----------------------RESULT----------------------
value1
```

Note that without the `-v` switch, the function return is printed to `stdout` with no modification or other information.

```
$ emulambda example.example_handler example/example.json
value1
```

#### What's happening?

In this example, `emulambda` is:
  1. Loading the `example_handler` function from the `example` module.
  1. Deserializing `stdin` (which is the contents of `example/example.json`) as the `event` argument for the function.
  1. Invoking the function, and measuring elapsed time and memory consumption.
  1. Reporting on resource usage.
  1. Printing the function result.

### Single-Event Mode with Context

From the repository root, run:
`emulambda example.example_handler example/example.json example/context.json -v `

You should see output similar to the following:
```
Function name is:  example
Executed example.example_handler
Estimated...
...execution clock time:     212ms (300ms billing bucket)
...execution peak RSS memory:    368M (385900544 bytes)
----------------------RESULT----------------------
value1
```

Note that without the `-v` switch, the function return is printed to `stdout` with no modification or other information.

```
$ emulambda example.example_handler example/example.json example/context.json
Function name is:  example
value1
```

#### What's happening?

In this example, `emulambda` is:
  1. Loading the `example_handler` function from the `example` module.
  1. Deserializing `stdin` (which is the contents of `example/example.json`) as the `event` argument for the function.
  1. Deserializing `stdin` (which is the contents of `example/context.json`) as the `context` argument for the function.
  1. Invoking the function, and measuring elapsed time and memory consumption.
  1. Reporting on resource usage.
  1. Printing the function result.

====

### Event Stream Mode

From the repository root, run:
`emulambda example.example_handler - -s -v -t 2 < example/ex-stream.ldjson`

You should see output similar to the following:
```
Entering stream mode.

Object 1 { "key1": "value1", "key2": "value2", "key3": "value3" }
Executed example.example_handler
Estimated...
...execution clock time:		 187ms (200ms billing bucket)
...execution peak RSS memory:		 367M (385839104 bytes)
----------------------RESULT----------------------
value1

Object 2 { "key2": "value2b", "key3": "value3b" }

There was an error running your function. Ensure it has a signature like `def lambda_handler (event, context)`.

Traceback (most recent call last):
.
.
[...snip...]
.
.
Object 18 { "key1": "value1b", "key2": "value2b", "key3": "value3b" }
Executed example.example_handler
Estimated...
...execution clock time:		 190ms (200ms billing bucket)
...execution peak RSS memory:		 404M (424108032 bytes)
----------------------RESULT----------------------
value1b

Summary profile from stream execution:
Samples: 18
(ERRORS DETECTED: Removing timing samples from aborted invocations.)
New sample size: 17
[187.44301795959473, 193.43900680541992, 201.05385780334473, 198.35305213928223, 201.8599510192871, 210.9360694885254, 197.86906242370605, 193.1910514831543, 197.47090339660645, 207.42297172546387, 196.4428424835205, 193.54796409606934, 194.66304779052734, 190.23799896240234, 192.36183166503906, 185.38999557495117, 190.08898735046387]
Clock time:
	Min: 185ms, Max: 210ms, Median: 194ms, Median Billing Bucket: 200ms, Rounded Standard Deviation: 7ms
Peak resident set size (memory):
	Min: 367M, Max: 404M
```

#### What's happening?

In this example, `emulambda` is:
  1. Loading the `example_handler` function from the `example` module.
  1. Streaming Line-Delimited JSON (LDJSON) lines from `stdin` (which is the contents of `example/ex-stream.ldjson`) as `event` arguments.
  1. Once per `event` object, invoking the function, reporting on resource usage, and printing the function result.
  1. At `event` number 2, there is an intentional error. Note that `emulambda` reports the error and recovers.
  1. After running each event through the lambda, reporting aggregate timing and memory information.

### Third-Party Libraries

Any third party library your Lambda function is using must be packaged and shipped to AWS Lambda.

`emulambda` will automatically pickup these libaries when installed in ``./lib`` directory of your project.

To install a third party library, just type : ``pip install -t ./lib <libary name>``

Notice that the AWS Python SDK (aka boto) is provided by default by the AWS runtime and should not be included into your project.

### Using a Lambda Execution Role

At the time you create a Lambda function, you specify an IAM role that AWS Lambda can assume to execute your Lambda function on your behalf. This role is also referred to as the execution role. If your Lambda function accesses other AWS resources during execution (for example, to create an object in an Amazon S3 bucket, to read an item from a DynamoDB table, or to write logs to CloudWatch Logs), you need to grant the execution role permissions for the specific actions that you want to perform using your Lambda function.

To simulate this behavior, you can pass your a Lambda Execution Role to ``emulambda`` using ``-r`` command line parameter, just like this

```
./emulambda -v lambda_function.lambda_handler ./test/lambda-event.json -r arn:aws:iam::012345678912:role/lambda_basic_execution
```

(be sure to replace the AWS Account ID and role name in the example above)

To use Lambda's Execution Role with ``emulambda``, you will need to setup the following :
- a default IAM user that has permission to assume the Lambda Execution Role
- the default IAM user's Access Key and Secret Key
- a Lambda Execution Role referencing your default IAM user in its TrustedPolicy.

The following section provides you with more detailed instructions to create these.

#### Create an IAM User

The default IAM user will be used by ``emulambda`` to Assume the Lambda Execution Role
- Go to the IAM Console and create a user for ``emulambda``.
- Collect the user's Access Key and Secret Key in ``~/.aws/credentials`` file
- Assign the AssumeRole permission to the user.

A sample IAM User credentials file looks like this :
```
$ cat ~/.aws/credentials
[default]
aws_access_key_id=AK...EA
aws_secret_access_key=7t...6O
```
A sample User Permission policy looks like (see ``example/UserPolicy.json`` file):
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Stmt123",
            "Effect": "Allow",
            "Action": [
                "sts:AssumeRole"
            ],
            "Resource": [
                "arn:aws:iam::<YOUR ACCOUNT>:role/<YOUR LAMBDA EXECUTION ROLE NAME>"
            ]
        }
    ]
}
```

#### Lambda Execution Role

The Lambda Execution Role is the one assumed by the Lambda container at runtime to acquire privileges to access other AWS resources.  

The **Policies** part of that role can contain any policies required by your lambda function code to access other AWS resources.

The **TrustedPolicies** part of that role must authorise your IAM user (created above) and the Lambda Service itself to assume the role.

A sample TrustedPolicy looks like (see ``example/TrustedPolicy.json`` file):

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "lambdaservice",
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    },
    {
      "Sid": "emulambda",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::<YOUR ACCOUNT ID>:user/<YOUR IAM USER>"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```


## How Profiling Works

The profiling in `emulambda` is meant to help with billing estimation more than anything else. Since we can only guess at some AWS Lambda internals, we've run some experiments against the service to partially reverse-engineer the metrics it uses for billing. Therefore:
  * Clock time is as close as possible to function execution. It does not include time spent loading the module(s), though that is a penalty you would pay the first time you execute the lambda in AWS.
  * System-reported peak RSS (resident set size) is used for memory estimation. This represents real memory use, not the use of virtual memory.

The authors of this project make no guarantees whatsoever that the profiling information given by `emulambda` is accurate. It may not correlate with what AWS bills. Many variables, including the resources allocated to the function runtime by AWS, may have an impact on the real billed amount.
