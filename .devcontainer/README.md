# Devcontainer

_The easiest way to contribute to and/or test this repository._

## Requirements

- [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [docker](https://docs.docker.com/install/)
- [VS Code](https://code.visualstudio.com/)
- [Dev Containers (VS Code Extention)](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

[More info about requirements and devcontainer in general](https://code.visualstudio.com/docs/remote/containers#_getting-started)

## How to use Devcontainer for development/test

1. Make sure your computer meets the requirements.
1. Fork this repository.
1. Clone the repository to your computer.
1. Open the repository using VS Code.

When you open this repository with VSCode and your computer meets the requirements you are asked to "Reopen in Container", do that.

If you don't see this notification, open the command pallet (ctrl+shift+p) and select `Dev Containers: Reopen Folder in Container`.

_It will now build the devcontainer._

The container have some "tasks" to help you testing your changes.

## Custom Tasks in this repository

_Start "tasks" by opening the the command pallet (ctrl+shift+p) and select `Tasks: Run Task`_

### Run tests

Will run unit tests in the workspace

### Run tests with coverage

Will run unit tests in the workspace with code coverage on

### Run tests with coverage and report

Will run unit tests in the workspace with code coverage and generated report on