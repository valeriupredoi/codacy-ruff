# Codacy Ruff

This is the docker engine to be used at Codacy to have [Ruff](https://github.com/astral-sh/ruff) support.
You can also create a docker container to integrate the tool and language of your choice!
See the [codacy-engine-scala-seed](https://github.com/codacy/codacy-engine-scala-seed) repository for more information.

# Build docker container

You can create the docker container by doing:

  ```bash
  docker build -t codacy-ruff:latest .
  ```

The docker container is ran with the following command:

  ```bash
  docker run -it -v $srcDir:/src codacy-ruff:latest
  ```

or non-interactively/TTY with:

  ```bash
  docker run -v ./src codacy-ruff:latest
  ```

# Github Action

[Running in this directory](https://github.com/valeriupredoi/codacy-ruff/actions)