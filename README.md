<p align="center">
    <img src="https://raw.githubusercontent.com/albertopoljak/Licensy/master/logo.png">
</p>

[![Licensy vAplha](https://img.shields.io/badge/Licensy-alpha-yellow)](#)
[![Invite me!](https://img.shields.io/badge/-Invite%20me-7289DA)](https://discordapp.com/oauth2/authorize?client_id=604057722878689324&scope=bot&permissions=268446720)
[![Discord support server](https://img.shields.io/discord/613844667611611332?color=%237289DA&label=Support%20Server&logo=discord)](https://discord.gg/trCYUkz)
[![Activity](https://img.shields.io/github/commit-activity/w/albertopoljak/Licensy)](https://github.com/albertopoljak/Licensy/pulse)
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](#)
[![Python 3.6+](https://img.shields.io/badge/python-3.6%2B-blue)](#)
[![License AGPL3](https://img.shields.io/github/license/albertopoljak/Licensy?color=red)](LICENSE.md)

# Licensy - easily manage expiration of roles with subscriptions!

Generate license keys that, when redeemed by a member, will add a certain role to member
that will last for certain time.

Both role and expiration time are tied to license.

You can make all of your roles subscribable and each license can have different expiration date.

Licenses are unique and random.

Made with security in mind and to work independently with multiple guilds.

## Quickstart bot usage

Default prefix is `!`
  
Call `!help` to see available commands.

Call `!help command_name` to see additional help for that specific command.

After the bot joined the guild:

`!default_role @role_here`

`!generate 5`

Optional (so you have more information):

`!guild_info`

`!help`

`!help generate`

## Permissions needed

Bot needs certain permissions to operate, here they are explained:

- read_messages=True
  - Needed so bot can see commands being called, otherwise nothing will happen
when using a command.

- send_messages=True
  - For sending feedback to guild (success, failure, errors, info)

- manage_roles=True
  - For actually adding/removing licensed roles from members.
  
- manage_messages=True
  - In case there is error when redeeming the license your original message
showing license gets deleted to minimize chances of stealing.
This happens for example if you redeem license for a role you **already**
have.

## Requirements

You need Python 3.6 or later and packages from `requirements.txt`

In Ubuntu, Mint and Debian you can install Python 3 like this:

    $ sudo apt-get install python3 python3-pip

For other Linux flavors, macOS and Windows, packages are available at

  http://www.python.org/getit/

## Quickstart source code

```bash
$ cd Licensy
$ pip install -r requirements.txt
```

Note that discord.py version that was used in development is 1.2.3
, anything above that (except for mayor version changes) should work.

Nevertheless for compatibility reasons the `requirements.txt` will target specifically v1.2.3
but if you are sure that there are no breaking changes in future version feel free to update.

Before running the bot edit the `config.json` found in the root directory.
Adding the token is the most important thing.

After that you are ready to run it:

```bash
$ python3 bot.py
```

Upon startup the bot will create what it needs (if it's missing), this includes:
log file and database file, including folders for them.

Invite the bot to any guild, it will create database guild entry upon joining.

Further steps on how to use the bot are in [Quickstart bot usage](#quickstart bot usage)

## Authors

* **[Joseph Kim](https://github.com/KimchiTastesGood)** - *Original bot and idea*
* **[Braindead](https://github.com/albertopoljak)** - *New bot redesign based on original idea*

## License

This project is licensed under the GNU AGPLv3 License - see the [LICENSE.md](LICENSE.md) file for details
