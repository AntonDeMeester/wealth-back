# Set up

`pipenv install`

# Run

`make run` or `make run-dev`

# Check

`make check`

# Format

`make reformat`

# Test

`make test`

# Setting up your dev environment

### VScode test discover

Because of some error, VS Code test discover does not work. It wants to log stuff, but pytest has already closed the logger.

To fix this, do this:

1. Go to `pymongo_inmemory.mongod`. This is a dependency, so go to your virtual environment.
2. Remove the logging line of the `cleanup` function (line 24 as of writing)
3. Save
