from nornir import InitNornir
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.tasks.networking import napalm_configure
from nornir.plugins.functions.text import print_result

commands = input("Command: ").split(",")
for cmd in commands:
    nr = InitNornir(config_file="config.yaml")
    result = nr.run(
        task=napalm_configure,
        command_string=cmd
    )
    print_result(result)
