<p align="center">
    <img src="https://raw.githubusercontent.com/albertopoljak/Licensy/master/logo.png">
</p>

[![Licensy archived](https://img.shields.io/badge/Licensy-archived-red)](#)
[![Python 3.6](https://img.shields.io/badge/python-3.6%2B-blue)](#)
[![License AGPL3](https://img.shields.io/github/license/albertopoljak/Licensy?color=red)](LICENSE.md)

This bot is archived, there will be no more updates.

I am also no longer hosting the bot, you can find someone else to host it, or you can host it yourself.

I will still be active in the support server but please ask bot related questions (no questions like 'how to setup vps' you can Google those)

# Licensy - easily manage expiration of roles with subscriptions!

Generate license keys that, when redeemed by a member, will add a certain role to member
that will last for certain time.

Each license is tied to a certain role and certain duration.

When member redeems the license he will get that role for that certain duration.

You can make all of your roles subscribable and each license can have different expiration date.

Members can have unlimited subscriptions active at the same time! (only limited by the Discord role limit per member which is 250).

Works independently with multiple guilds.

## Quickstart bot usage

For full bot usage make sure you have the **administrator** guild permission (or guild owner).

Default prefix is `!`

Default license expiration time is 720h aka 30 days.

After the bot joined the guild call:

```bash
!default_role @role_here
!generate 5
```

First line will set **@role_here** as default guild role.

Second will generate 5 licenses, and as you can see only 5 is an argument so the 
command will use **default** guild role (previously set to **@role_here**) and **default** expiration 
date (which is initially set to 720h aka 30days upon guild join).

If you want to use `!generate` command in some other way (that doesn't rely on using
default guild data but relies on passed arguments) call `!help generate` to see full explanation 
on how to use it.

Quick example for custom `!generate` arguments:

```
!generate 10 @subscription 1m
!generate 5 @supporter 1w
```

This will generate 10 licenses for role `@subscription` in duration of 1 month and 5 licenses for role `@supporter` in
duration of 1 week.

In general these 2 are your friends:

- Call `!help` to see available commands.
Note that you will not see commands that you don't have the permission for.
Example non-admin members will not see admin commands listed when calling help.

- Call `!help command_name` to see additional help for that specific command.
Every command is properly documented.


Optional (so you have more information):

```bash
!guild_info
!faq
```

For any other questions/help/suggestions/anything call `!support` and join the support server :)

You can also join it from this Github page, click on the icon at the top of this readme.

## Permissions needed

Note that even if bot has all of these permissions he might still not be able to manage some roles:

- Remember that bots' role has to be **higher** in role hierarchy than the managed members top role.
Meaning it can only manage roles **below** its own role in hierarchy.

Bot needs these permissions to operate:

```bash
read_messages=True
```
- Needed so bot can see commands being called, otherwise nothing will happen
when using a command.

```bash
send_messages=True
```
- For sending feedback to guild (success, failure, errors, info)

```bash
manage_roles=True
```
- For actually adding/removing licensed roles from members.

```bash
manage_messages=True
```
- In case there is error while using command that exposes the license your original 
message that is showing license will get deleted to minimize chances of stealing.
This happens for example if you redeem license for a role you **already** have.

## Requirements for source

You need Python 3.6 and packages from `requirements.txt`

In Ubuntu, Mint and Debian you can install Python 3 like this:

    $ sudo apt-get install python3 python3-pip

For other Linux flavors, macOS and Windows, packages are available at

  http://www.python.org/getit/

## Quickstart source code

```bash
$ cd Licensy
$ pip install -r requirements.txt
```

Before running the bot edit the `config.json` found in the root directory.
Adding the bot token is the most important thing.
If you don't know what top.gg is or don't need it you can leave top_gg_api_key as it is (empty).

After that you are ready to run it:

```bash
$ python3 bot.py
```

Upon startup the bot will create what it needs (if it's missing), this includes:
log file and database file, including folders for them.

Invite the bot to any guild, it will create database guild entry upon joining.

Further steps on how to use the bot are in [Quickstart bot usage](#quickstart-bot-usage)

## Authors

* **[Joseph Kim](https://github.com/KimchiTastesGood)** - *Original bot and idea*
* **[Braindead](https://github.com/albertopoljak)** - *New bot redesign based on original idea*

## License

This project is licensed under the GNU AGPLv3 License - see the [LICENSE.md](LICENSE.md) file for details
, for plain english you can check out [tldrlegal](https://tldrlegal.com/license/gnu-affero-general-public-license-v3-(agpl-3.0)).

If you fork/download the code and run your own bot instance **WITHOUT** changing the code then you don't have to worry
regarding the license as all is already implemented in the bot functionality (commands that link to this readme, state
authors etc..) 

But if you fork/download/host this bot and you **CHANGED** any of the code you **must** hold to this:

- Include copyright (see [Authors](#authors))
  - You cannot claim this code as yours.
- Include the same license (see [LICENSE.md](LICENSE.md))
- State changes
  - any changes to the source code must be disclosed (public).
- Disclose source
  - you cannot take the code and make it private.
- Include install instructions
  - You can link to this readme or to your own instructions.

Only and only if you adhere to all the above points you **can**:

- Use the bot for commercial use
- Modify the source
- Distribute the bot
- Place Warranty
