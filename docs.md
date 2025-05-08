# VMChecker Next Interactive (Student Handbook)

## Download & Installation

The latest `vmck` realease can be downloaded from the [releases page](https://github.com/open-education-hub/vmchecker-next-cli/releases/download/latest/vmck).

To install the CLI add it to a location accessible from the `PATH` environment variable.

**Example**:

- System wide install:
```bash
sudo install -m 755 vmck /usr/local/bin/
```

- User install:
```bash
install -m 755 vmck ~/.local/bin/
```

Ensure `~/.local/bin/` is in your $PATH by adding this to `~/.bashrc` or `~/.zshrc`:
```bash
export PATH="$HOME/.local/bin:$PATH"
```
## The CLI

The VMChecker CLI binary is a tool designed to streamline the management of interactive assignments within virtualized environments. The primary function of the VMChecker CLI is to orchestrate and manage all the necessary environments for interactive assignments, providing a consistent workflow.

With the VMChecker CLI, you can start, connect, and stop your interactive environments without the risk of losing progress, as the CLI supports pausing assignments while maintaining data persistence. To achieve this, the CLI binds important locations inside the container to volumes or specific locations on the host machine. Some bindings, such as the host's home directory, are predefined and are always mounted inside the guest environment. Additionally, the CLI allows for customizable bindings, specified within the assignment `manifest.yml` file, to ensure that critical data remains persistent across sessions.

### CLI Commands

The CLI implements the following commands:

- **submit**: This command sends a signed archive to VMChecker, creating a finished submission in the middleware. Encapsulates all necessary files and metadata required for evaluation.
- **check**: Running this command triggers the checker within the assignment's environment, which generates a signed archive, with its output, that is ready for submission. The check command is versatile, allowing users to verify a single task and save its output, ensuring targeted feedback and validation.
- **shell**: This command initiates the container or VM (depending on the assignment) in an interactive mode, providing a terminal interface for users to work directly within the environment.
- **clean**: Designed to free up resources, this command removes runtime assignment resources such as Docker containers or images. A clear warning is issued to alert users that the execution of this command will result in the loss of the current assignment state.
- **update**: This command fetches the latest updates and changes, ensuring that users are working with the most current version of the assignment and related resources.
- **stop**: Stops all running containers.
- **start**: Starts all containers of the assignment.
- **init**: Intializes the assignment based on the manifest.yml file pulled from a provided URL.
- **version**: Prints the version of the CLI.

#### Init
```
Init the project

Usage:
  vmck init <url>
```
- **url** - The URL of the manifest.yml file.

The command will use the current directory to store and initialize the assignemnt and its resources and store any metadata inside a .vmck directory. All subsequent commands must be executed in the same directory.

**Example**

```bash
vmck init https://example.com/manifest.yml
```
This will read the manifest file from https://example.com/manifest.yml, initialize the assignment and pull its resources.

#### Shell
```
Start a shell inside the assignment container

Usage:
  vmck shell
```

Will provide an interactive shell inside the assignemnt container through which you'll complete your tasks.

**Example**

#### Check
```
Check assignment

Usage:
  vmck check
```

Will run the checker on your current assingment.

**Example**

#### Submit
```
Submit assignment

Usage:
  vmck submit
```

Will prepare an archive with your submission to be sent to Moodle. An authentication URL, valid for 60s, will be printed where you will need to log in.

**Example**

#### Start
```
Start the assignment environment

Usage:
  vmck start
```

Will start all assignment containers. Equivalent to `docker start <container-id>`.

**Example**

#### Stop
```
Stop all containers

Usage:
  vmck stop
```

Will pause all assignment containers. Equivalent to `docker stop <container-id>`.

**Example**

#### Update
```
Update all containers

Usage:
  vmck update
```

This will stop all containers, pull their latest version and start them from scratch. All dynamic configurations will **not** be saved.

**Example**

#### Clean
```
Clear the environment. Remove all docker containers, and any stored data

Usage:
  vmck clean
```

This will remove the entire assignment information, deleting all your work. This operation is not **reversible**. Make sure you submit and check your assignment before running this command.

**Example**

### Submission flow

The submission flow is as follows:

1. Create a new directory for the assignment (E.g: `mkdir test-assignment`) and cd into it
2. Initialize the assignment using `vmck init <url>` (E.g: `vmck init https://example.com/manifest.yml`
3. Start the assignment using `vmck start`.
4. To start working on the assignment, run `vmck shell` to get a shell in the docker container.
5. Do some work inside the container.
6. Periodically, run `vmck check` outside the container to check your progress. Repeat points 5 and 6 untill done!
7. To submit the assignment, run `vmck submit`. This will print out a URL used to log in to the university's identity provider. After successfuly logging in, your submission will be complete.
8. On Moodle, go to the VMChecker block associated with the assignment and click on "Pull" to get your results and grade.


See the following movie for a step by step guide on how to use the CLI.


TODO - Move to TA side, Use Asciicinema

### Archive Format

The archive format generated `vmck check` command, will include:

- **Stdout** of the checker process.
- **Stderr** of the checker process.
- **An artifacts directory**, which contains relevant files to the assignment. The files that will be added are specified by the teaching assistants.

### Submission format

The submission data will contain:
- **The archive**, generated using `vmck check` (See [Archive Format](#archive-format)).
- **A JWT token**, received from the OIDC provider.
- **Moodle assignment ID**, the corresponding ID of the Moodle assignment.
- **Signature**, which is a digital signature of stdout, stderr, the artifacts directory.

## Support (For the CLI)

If you belive you have found a bug, report it on the Github issue tracker found [here](https://github.com/open-education-hub/vmchecker-next-cli).

Please include the following information:
- What were you doing
- What did you expect to happen
- What happened instead
- What operating system are you using
- What version of the CLI are you using
- The error and log messages (if any)

# VMChecker Next Interactive (TA Handbook)

## Building Checker

### Requirmentes && Dependencies

A checker example can be found at https://github.com/open-education-hub/vmchecker-next-cli. It is written in Golang an has the following structure:

```
build/
 |-Dockerfile
cmd/
pkg/
 |-checker/
scripts/
 |-publish.sh
```
The `cmd/` and`pkg/` directories contain the source code of the checker. The `scripts/` directory contains the build and publishscript, which will be used to build and distribute the checker. The `build/` directory contains the Dockerfile, which will be used to generate the checker image.

### API

The checker development API has exposes 2 interfaces: checker and printer.

The checker has the following interface:

```golang
/*
* Registers a callback function for a test. The name of the test will be testName.
*/
RegisterTest(testName string, testFunction TestFunction)

/*
* Runs all the registered tests.
*/
RunTests()

/*
* Writes the results of the tests to the specified location. This include the stdout and stderr in a zip file called archive at the specified location. It will also write the signature of the archive at the specified location.
*/
WriteResults(location string) error
```

The printer has the following interface:

```golang
/*
* It exposes part of the fmt package api. It will print the message to the stdout and keep it in memory for signing purposes.
*/
Println(a ...any) (int, error)
Printf(format string, a ...any) (int, error)
```
The printer API is provided as a parameter to each test function at runtime.

#### Test Examples

The following test grants 10 points and does not perform any checks:

```golang
func test_ex_officio(_ checker.Printer) (mark float64, err error) {
	mark = 10
	return mark, err
}
```

The following test grants 10 points and checks whether the /opt directory and /opt/test_file file exist:

```golang
func test_file(printer checker.Printer) (mark float64, err error) {
	if fInfo, e := os.Stat("/opt"); e == nil && fInfo.IsDir() {
		printer.Println("Good job! Found /opt directory")
		mark += 5
	} else {
		printer.Printf("Could not find /opt directory: %v\n", e)
	}

	if fInfo, e := os.Stat("/opt/test_file"); e == nil && !fInfo.IsDir() {
		printer.Println("Good job! Found /opt/test_file file")
		mark += 5
	} else {
		printer.Printf("Could not find /opt/test_file file: %v\n", e)
	}

	return mark, err
}
```

The following test runs an external checker, parses the output, and grants points based on it. The external checker is a bash script that aceepts the test name as an argument and prints out the total points.****

```golang
func test_external_checker(printer checker.Printer) (mark float64, err error) {
	cmd := exec.Command("bash", "/opt/assignment/external_checker.sh", "test_3")
	rawOutput, err := cmd.Output()
	if err != nil {
		printer.Printf("Error running external checker: %v\n", err)
		printer.Println(string(rawOutput))
		return 0, err
	}

	output := string(rawOutput)
	printer.Println(output)

	rawResults := regexp.MustCompile("Total: ([0-9]+)").FindStringSubmatch(output)[1]
	rawMark, err := strconv.Atoi(rawResults)
	if err != nil {
		printer.Printf("Error parsing external checker output: %v\n", err)
		return 0, err
	}

	return float64(rawMark), err
}
```
### Building Checker

The build script will do the following steps:
- Generate an RSA key pair and write the keys in a public.pem and private.pem file
- Build the docker image which will have the following substeps:
  - Copy the private.pem file inside the image
  - Build the checker and embed the private.pem file inside the binary
  - Copy the checker binary to a new base image (e.g: ubuntu:22.04)

The struecture of the checker image will be:
- `/opt/assignment/checker` - the location of the checker binary
- `/opt/assignment/out` - the location of where the checker will write the output archive (see [Archive Format](#archive-format)) in an `archive.zip` file and its signature in the `signature` file.

The checker image will be pushed to a public registry (e.g: Docker Hub, GitLab Container Registry) usin the `publish.sh` script.

## Setting up the Assignment Declaration

The `manifest.yml` file is the centerpiece of the assignment declaration. It must contain the Docker-compose configuration that dictates how the assignment environment is set up, an artifacts entry, which lists additional files that must be packed inside the archive, and the Moodle assignment ID. The file must be publicly accessible on the internet.

The `manifest.yml` file must be in the following format:
- **Docker-Compose Configuration**: This section dictates how the assignment environment is set up. It defines the services, networks, and volumes that are necessary for the assignment. The Docker-Compose configuration ensures that all required containers are specified and properly configured to work together. The main Docker service, the container in which the checker binary is present and where the students will spend most of their time, must be annotated with the is\_checker label. The VMChecker CLI must know where the checker is found.
- **Artifacts Entry**: This entry lists additional files that must be packed inside the archive. These files could include supplementary resources, scripts, or any other necessary materials that are essential for the completion of the assignment. The artifacts entry ensures that all required files are included in the archive.
- **Moodle Assignment ID**: This is a unique identifier for the assignment within the Moodle learning management system. Including the Moodle assignment ID in the manifest.yml file links the configuration and artifacts to the specific assignment, ensuring that everything is correctly associated, graded, and managed within Moodle.

Example:
```yml
version: '1.0'
moodle_assignment: 1234
environment:
  services:
    main_container:
      image: my_course/assignment_1:1.0.0
      labels:
        is_checker: true
      volumes:
        - special-folder:/opt/configs/

    extra_service_container:
      image: my-course/extra:1.0.0
      depends_on:
        - main-container

  volumes:
    special-folder

artifacts:
  main_container:
    - /home/student/.bash_history
    - /home/ssh/sshd_config
  extra_service_container:
    - /opt/custom-configs/
```

## Setting up Moodle

The Moodle assignment will follow the normal VMChecker Next process (create the assignment and associate a new VMChecker block to it - See the [VMChecker Next Moodle integration](https://github.com/open-education-hub/vmchecker-next/wiki/Teaching-Assistant-Handbook#3-moodle-setup) docs).
<details>
<summary>TL;DR – Moodle Setup for VMChecker</summary>

- Enable Moodle VMChecker Plugin:
  - Get access from your Moodle admin, enable VMChecker block.

- Create Assignment in Moodle:
  - Add a new assignment for students to upload their work. Enable file submissions.

- Connect Moodle to GitLab:
  - Configure the VMChecker block:
    - Add your GitLab project ID.
    - Use your personal access token for GitLab API access.
    - Set the image name to the one you built in your pipeline.

- Configure Repositories & Pipelines:
  - Point Moodle to the private GitLab repository.
  - The checker will use the pipeline image to test homework submissions.

- Test Setup - Submit a dummy file to make sure everything works!
</details>

<br/>
This time, when setting up the VMChecker block, you will have to choose the type of the assignment to be **Interactive**. In this case, it will include a new field: the **Public key**, which is the same key that was generated when the checker was built, and it will be used to validate the authenticity of a submission, before grading it.

## Releasing the Assignment

Before releasing the assignment to students, publish the URL of the `manifest.yml` file (A convenient way is to use a public Github repository or the institutional GitLab instance), and the make the VMChecker block visible to students.
