# Meterstick
## Benchmark tool for cloud deployed Minecraft-like games

### Config

- Specify experiment and practical parameters in config.cfg 
- Specify node IPs in ips
    - First IP runs MC server
    - All following nodes run yardstick player emulation
- Add necessary SSL keys for access to those IPs in keys folder
    - Ensure these are listed in config.cfg

### Specifying Servers
- To use default ones, run retrieve_jars.sh 
- Otherwise, copy the server folder into servers
    - Change servers var in config.cfg
    - Specify jmx_url in config.cfg
        - If unknown, check with jconsole or similar tool
- Add the run.sh script to the server folder.
    - If necessary, change the name of the jar file it runs.

### Specifying Worlds
- Copy world folder MC/worlds
- Add world name to worlds list in config.cfg

### Run
- Run start_experiment.sh
    - Total runtime in seconds will be around (duration + 45) * iterations * number of servers * number of worlds

### Plotting
- After collecting results, run the python files in the plotting_tools folder
    - Multi plot may require renaming results folders and moving the plotting file

### Tools used
- See [this link](https://github.com/atlarge-research/yardstick/commit/066a2b258a6c6f9c333a386751154d05c763b6d4) for relevant branch of the Yardstick player emulation tool 
- [PSUtil project](https://pypi.org/project/psutil/)
- [Java Management Extensions](https://docs.oracle.com/javase/tutorial/jmx/overview/javavm.html) 


