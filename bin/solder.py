#!/usr/bin/env python

from __future__ import print_function

import argparse
import colorama
import tabulate

import technic.solder

# pylint: disable=unused-argument

def better_print(message, *args, **kwargs):
	if 'color' in kwargs:
		color = kwargs['color']

		message = color + message + colorama.Style.RESET_ALL

		del kwargs['color']

	message = message.format(*args, **kwargs)

	print(message)

def print_error(message, *args, **kwargs):
	better_print(
		message,
		color = colorama.Fore.RED,
		*args,
		**kwargs
	)

def parse_server_info_args(parsers):
	parsers.add_parser(
		'info',
		help = 'Get the server information',
	).set_defaults(func = cmd_server_info)

def parse_mod_args(parsers):
	mod_parser = parsers.add_parser(
		'mod',
	)

	subcommands = mod_parser.add_subparsers()

	info_parser = subcommands.add_parser(
		'info',
		help = 'Get information about a mod',
	)

	info_parser.add_argument(
		'mod_slug',
		type = str,
		help = 'The modslug',
	)

	info_parser.set_defaults(func = cmd_mod_info)

def parse_modpack_args(parsers):
	modpack_parser = parsers.add_parser(
		'modpack',
	)

	subcommands = modpack_parser.add_subparsers()

	subcommands.add_parser(
		'list',
		help = 'List all available modpacks',
	).set_defaults(func = cmd_modpack_list)

	info_parser = subcommands.add_parser(
		'info',
		help = 'Get information about a specific modpack',
	)

	info_parser.add_argument(
		'modpack_slug',
		type = str,
		help = 'The modpack slug',
	)

	info_parser.set_defaults(func = cmd_modpack_info)

	build_parser = subcommands.add_parser(
		'build',
	)

	build_parser.add_argument(
		'modpack_slug',
		type = str,
		help = 'The modpack slug',
	)

	build_parser.add_argument(
		'build',
		type = str,
		help = 'The modpack build',
	)

	parse_modpack_build_args(build_parser.add_subparsers())

def parse_modpack_build_args(parsers):
	parsers.add_parser(
		'info',
	).set_defaults(func = cmd_modpack_build_info)

	parsers.add_parser(
		'download',
	).set_defaults(func = cmd_modpack_build_download)

def parse_args():
	parser = argparse.ArgumentParser(
		description = 'Solder command line client',
	)

	parser.add_argument(
		'--config',
		type    = str,
		default = None,
		dest    = 'config',
		help    = 'The Solder client config file. Defaults to ~/.solderrc',
	)

	parser.add_argument(
		'solder_url',
		type = str,
		help = 'The Solder server URL',
	)

	subcommand_parsers = parser.add_subparsers()
	parse_server_info_args(subcommand_parsers)
	parse_mod_args(subcommand_parsers)
	parse_modpack_args(subcommand_parsers)

	return parser.parse_args()

def command(func):
	def wrapper(args):
		server = technic.solder.SolderServer(args.solder_url, config_file = args.config)

		return func(server, args)

	return wrapper

@command
def cmd_server_info(server, args):
	info = server.server_info
	print(
		'Version {} {}'.format(
			info[0],
			info[1],
		)
	)

@command
def cmd_mod_info(server, args):
	mod = server.get_mod_info(args.mod_slug)
	better_print(
		mod['pretty_name'],
		color = colorama.Fore.GREEN,
	)

	print(
		tabulate.tabulate(
			[
				['Slug',        mod['name']],
				['Author',      mod['author']],
				['Description', mod['description']],
				['Website',     mod['link']],
				['Donate URL',  mod['donate_link']],
				['Versions',    ', '.join(mod['versions'][:10])],
			]
		)
	)

@command
def cmd_modpack_list(server, args):
	print(
		tabulate.tabulate(
			[
				[slug, name]
				for slug, name in server.modpacks.iteritems()
			],
			headers = ['Slug', 'Name'],
		)
	)

@command
def cmd_modpack_info(server, args):
	modpack = server.get_modpack_info(args.modpack_slug)

	better_print(
		modpack['display_name'],
		color = colorama.Fore.GREEN,
	)

	print(
		tabulate.tabulate(
			[
				['Slug',              modpack['name']],
				['URL',               modpack['url']],
				['Recommended Build', modpack['recommended']],
				['Latest Build',      modpack['latest']],
				['Builds',            ', '.join(modpack['builds'][:10])],
			]
		)
	)

@command
def cmd_modpack_build_info(server, args):
	build_info = server.get_modpack_build_info(args.modpack_slug, args.build)

	better_print(
		'{modpack} Build {build}',
		color = colorama.Fore.GREEN,
		modpack = args.modpack_slug,
		build   = args.build,
	)

	print(
		tabulate.tabulate(
			[
				['Minecraft Version', build_info['minecraft']],
				['Forge',             build_info['forge']],
				['Mod Count',         len(build_info['mods'])],
			]
		)
	)

def callback_mod_download(status, *args, **kwargs):
	if status == 'mod.download.start':
		better_print('\t{}', kwargs['name'], color = colorama.Fore.CYAN)

		better_print(
			'\t\tDownloading...',
			color = colorama.Fore.YELLOW,
		)
	elif status == 'mod.download.cache':
		better_print(
			'\t\tCached, skipping',
			color = colorama.Fore.YELLOW,
		)
	elif status == 'mod.download.verify':
		better_print(
			'\t\tVerifying...',
			color = colorama.Fore.YELLOW,
		)
	elif status == 'mod.download.verify.error':
		better_print(
			'\t\tFile did not download correctly!',
			color = colorama.Fore.RED,
		)
	elif status == 'mod.download.unpack':
		better_print(
			'\t\tUnpacking...',
			color = colorama.Fore.YELLOW,
		)
	elif status == 'mod.download.clean':
		better_print(
			'\t\tCleaning...',
			color = colorama.Fore.YELLOW,
		)
	elif status == 'mod.download.finish':
		better_print(
			'\t\tFinished!',
			color = colorama.Fore.GREEN,
		)

@command
def cmd_modpack_build_download(server, args):
	better_print(
		'Starting download of build {build} for {modpack}...',
		color   = colorama.Fore.YELLOW,
		modpack = args.modpack_slug,
		build   = args.build,
	)

	server.download_modpack(args.modpack_slug, args.build, callback_mod_download)

	better_print(
		'Finished downloading modpack build!',
		color = colorama.Fore.GREEN,
	)

def main():
	args = parse_args()

	try:
		args.func(args)
	except technic.solder.SolderAPIError as ex:
		print_error(ex.message)

if __name__ == '__main__':
	main()

