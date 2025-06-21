# Checking for errors

At a high level, when you're ready to check for errors you download
logs from the bucket to your local machine, and then run scripts on
the data to see if there were errors. If there were, you can extract
the relevant inputs for these errors and use them with replay unit
tests in Swift.

The Python scripts that perform analysis expect the same dependencies
as the service, so make sure that you are running a `venv`, as
described in the README.md file.

## Downloading data

To download data, you need to make sure that you have a service key
that gives you permission to access the bucket and save it in a file
called `google-auth.json` in the main directory of the repo. The
download script, called `update_trio_stats.sh` will use this file for
bucket authentication. Make sure to protect this service key file as
it provides access to the service.

## Checking for errors

The logs include both successful and unsuccessful runs, so to see if
there were any errors you use the `check_for_errors.sh` script. For
example, you can run:

```bash
$ ./check_for_errors.sh makeProfile 2025-06-20
```

And it will look through all of the logs for the makeProfile function
for 2025-06-20 and print something to stdout for all of them that
contain errors. You can open these files directly to inspect the JSON
to get more information about the error.

**Note:** The script hard-codes the app version, so you may need to
change this as the app version updates.

## Replaying errors

If you want to replay errors, you can extract the inputs for a
function and then serve them via a simple HTTP server. Each of the
functions have unit tests for downloading these error files and
replyaing the inputs in Swift to compare against modified JS running
from the testing bundle.

```bash
$ ./extract_errors.sh iob 2025-06-20
$ python serve_errors.py
```

Will extract errors for a function / day combination and then start
the HTTP server that is used by the Swift unit tests in Xcode.
