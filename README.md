# Member license key Discord bot

Create license keys that will assign the member with a temporary role when activated.

## Requirements

You need Python 3.6 or later and packages from `requirements.txt`

In Ubuntu, Mint and Debian you can install Python 3 like this:

    $ sudo apt-get install python3 python3-pip

For other Linux flavors, macOS and Windows, packages are available at

  http://www.python.org/getit/

## Usage

```bash
$ cd MemberLicenseKey-DiscordBot
$ pip install -r requirements.txt
$ python3 bot.py
```

Note that discord.py version that was used in development is 1.2.3
, anything above that (except for mayor version changes) should work.

Nevertheless for compability reasons the `requirements.txt` will target specifically v1.2.3
but if you are sure that there are no breaking changes in future version feel free to update.

## What is it?

Role license subscription bot. 

Manage licenses, licensed roles and set license expiration dates.

Bulk create licenses with custom or default values or bulk print them.

Licenses are unique and random.

Made with security in mind and to work independently with multiple guilds.

## Example usage

Currently in development. See [Quickstart](##Quickstart)

## Quickstart

Start the bot, it will create database.

Invite it to guild, it will create database guild entry upon joining.
Default prefix is `!`

Call `!setup prefix @default_license_role`
 (this is only for development stage)
  
Bot is ready to use! Call `!help` to see available commands.



## Authors

* **[Joseph Kim](https://github.com/KimchiTastesGood)** - *Original bot and idea*
* **[Braindead](https://github.com/albertopoljak)** - *New bot redesign based on original idea*

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
