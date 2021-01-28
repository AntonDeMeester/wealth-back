# set base image (host OS)
FROM python:3.8

ENV WORKDIR=/code

# set the working directory in the container
WORKDIR $WORKDIR

# copy the dependencies file to the working directory
COPY Pipfile.lock $WORKDIR

# install dependencies 
RUN pipenv install --system --deploy --ignore-pipfile

# copy the content of the local src directory to the working directory
COPY wealth/ .

# command to run on container start
CMD [ "uvicorn", "wealth.main:app"]